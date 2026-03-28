"""Analyze YOLO dataset structure and annotation quality from a data.yaml file."""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

try:
	import yaml
except ModuleNotFoundError:
	yaml = None


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass
class SplitStats:
	name: str
	image_dir: Path
	label_dir: Path
	total_images: int = 0
	labeled_images: int = 0
	missing_label_files: int = 0
	empty_label_files: int = 0
	orphan_label_files: int = 0
	bad_label_lines: int = 0
	class_instances: Counter = field(default_factory=Counter)
	class_images: Counter = field(default_factory=Counter)
	bad_line_examples: List[str] = field(default_factory=list)
	missing_label_examples: List[str] = field(default_factory=list)
	orphan_label_examples: List[str] = field(default_factory=list)


def resolve_dataset_path(base_dir: Path, value: str) -> Path:
	path = Path(value)
	if path.is_absolute():
		return path
	return (base_dir / path).resolve()


def resolve_split_image_dir(data_yaml_dir: Path, split_name: str, yaml_value: str) -> Path:
	"""Resolve split image directory with robust fallbacks for common dataset layouts."""
	primary = resolve_dataset_path(data_yaml_dir, yaml_value)
	if primary.exists():
		return primary

	split_aliases = {
		"train": ["train"],
		"val": ["val", "valid"],
		"test": ["test"],
	}

	candidates = []
	for alias in split_aliases.get(split_name, [split_name]):
		candidates.append((data_yaml_dir / alias / "images").resolve())

	for candidate in candidates:
		if candidate.exists():
			return candidate

	return primary


def infer_label_dir(image_dir: Path) -> Path:
	if image_dir.name == "images":
		return image_dir.parent / "labels"
	return image_dir.parent / "labels"


def parse_label_file(
	label_file: Path,
	class_count: int,
	split: SplitStats,
) -> Tuple[Counter, bool]:
	class_counts = Counter()
	had_any_annotation = False

	try:
		lines = label_file.read_text(encoding="utf-8").splitlines()
	except Exception:
		split.bad_label_lines += 1
		if len(split.bad_line_examples) < 5:
			split.bad_line_examples.append(f"{label_file.name}: cannot read file")
		return class_counts, False

	for idx, line in enumerate(lines, start=1):
		stripped = line.strip()
		if not stripped:
			continue

		parts = stripped.split()
		if len(parts) != 5:
			split.bad_label_lines += 1
			if len(split.bad_line_examples) < 5:
				split.bad_line_examples.append(
					f"{label_file.name}:{idx} -> expected 5 values, got {len(parts)}"
				)
			continue

		try:
			class_id = int(parts[0])
			_ = [float(v) for v in parts[1:]]
		except ValueError:
			split.bad_label_lines += 1
			if len(split.bad_line_examples) < 5:
				split.bad_line_examples.append(
					f"{label_file.name}:{idx} -> non-numeric label values"
				)
			continue

		if class_id < 0 or class_id >= class_count:
			split.bad_label_lines += 1
			if len(split.bad_line_examples) < 5:
				split.bad_line_examples.append(
					f"{label_file.name}:{idx} -> class id {class_id} out of range"
				)
			continue

		class_counts[class_id] += 1
		had_any_annotation = True

	return class_counts, had_any_annotation


def analyze_split(split_name: str, image_dir: Path, class_count: int) -> SplitStats:
	label_dir = infer_label_dir(image_dir)
	stats = SplitStats(name=split_name, image_dir=image_dir, label_dir=label_dir)

	if not image_dir.exists():
		return stats

	image_files = sorted(
		p for p in image_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS
	)
	stats.total_images = len(image_files)

	label_files = set()
	if label_dir.exists():
		label_files = {
			p.relative_to(label_dir).with_suffix("")
			for p in label_dir.rglob("*.txt")
			if p.is_file()
		}

	image_stems = {
		p.relative_to(image_dir).with_suffix("")
		for p in image_files
	}

	orphan_stems = sorted(label_files - image_stems)
	stats.orphan_label_files = len(orphan_stems)
	stats.orphan_label_examples = [str(s) for s in orphan_stems[:5]]

	for image_path in image_files:
		relative_stem = image_path.relative_to(image_dir).with_suffix("")
		# Do not use Path.with_suffix here because Roboflow filenames contain dots.
		label_path = label_dir / Path(f"{relative_stem}.txt")

		if not label_path.exists():
			stats.missing_label_files += 1
			if len(stats.missing_label_examples) < 5:
				stats.missing_label_examples.append(str(relative_stem))
			continue

		class_counts, had_annotation = parse_label_file(label_path, class_count, stats)
		if not had_annotation:
			stats.empty_label_files += 1
			continue

		stats.labeled_images += 1
		for cls_id, count in class_counts.items():
			stats.class_instances[cls_id] += count
			stats.class_images[cls_id] += 1

	return stats


def print_split_report(stats: SplitStats, class_names: Dict[int, str]) -> None:
	print(f"\n=== {stats.name.upper()} ===")
	print(f"Images directory : {stats.image_dir}")
	print(f"Labels directory : {stats.label_dir}")
	if not stats.image_dir.exists():
		print("Warning          : images directory does not exist")
	if not stats.label_dir.exists():
		print("Warning          : labels directory does not exist")
	print(f"Total images     : {stats.total_images}")
	print(f"Labeled images   : {stats.labeled_images}")
	print(f"Missing labels   : {stats.missing_label_files}")
	print(f"Empty labels     : {stats.empty_label_files}")
	print(f"Orphan labels    : {stats.orphan_label_files}")
	print(f"Bad label lines  : {stats.bad_label_lines}")

	if stats.missing_label_examples:
		print("Missing label examples:")
		for name in stats.missing_label_examples:
			print(f"  - {name}")

	if stats.orphan_label_examples:
		print("Orphan label examples:")
		for name in stats.orphan_label_examples:
			print(f"  - {name}")

	if stats.bad_line_examples:
		print("Bad label examples:")
		for example in stats.bad_line_examples:
			print(f"  - {example}")

	if stats.class_instances:
		print("Class instance distribution:")
		for class_id in sorted(class_names.keys()):
			print(
				f"  - {class_names[class_id]:<10} (id={class_id:2d}): "
				f"{stats.class_instances[class_id]}"
			)


def load_data_yaml(yaml_path: Path) -> dict:
	if yaml is not None:
		with yaml_path.open("r", encoding="utf-8") as f:
			data = yaml.safe_load(f)
	else:
		data = parse_simple_data_yaml(yaml_path)

	required = ["train", "val", "test", "nc", "names"]
	missing = [k for k in required if k not in data]
	if missing:
		raise ValueError(f"Missing required keys in data.yaml: {missing}")
	return data


def parse_simple_data_yaml(yaml_path: Path) -> dict:
	"""Parse the minimal data.yaml structure used by this project without PyYAML."""
	text = yaml_path.read_text(encoding="utf-8")
	data = {}

	for raw_line in text.splitlines():
		line = raw_line.split("#", 1)[0].strip()
		if not line or ":" not in line:
			continue

		key, value = line.split(":", 1)
		key = key.strip()
		value = value.strip()

		if not value:
			continue

		if key == "nc":
			data[key] = int(value)
		elif key == "names":
			data[key] = ast.literal_eval(value)
		elif key in {"train", "val", "test"}:
			data[key] = value.strip("\"'")

	return data


def build_class_map(names: List[str], nc: int) -> Dict[int, str]:
	if len(names) != nc:
		raise ValueError(
			f"Mismatch between nc ({nc}) and number of names ({len(names)})"
		)
	return {i: name for i, name in enumerate(names)}


def to_serializable(stats: SplitStats, class_names: Dict[int, str]) -> dict:
	per_class = {
		class_names[i]: {
			"class_id": i,
			"instances": stats.class_instances[i],
			"images": stats.class_images[i],
		}
		for i in sorted(class_names.keys())
	}

	return {
		"split": stats.name,
		"image_dir": str(stats.image_dir),
		"label_dir": str(stats.label_dir),
		"total_images": stats.total_images,
		"labeled_images": stats.labeled_images,
		"missing_label_files": stats.missing_label_files,
		"empty_label_files": stats.empty_label_files,
		"orphan_label_files": stats.orphan_label_files,
		"bad_label_lines": stats.bad_label_lines,
		"examples": {
			"missing_labels": stats.missing_label_examples,
			"orphan_labels": stats.orphan_label_examples,
			"bad_lines": stats.bad_line_examples,
		},
		"per_class": per_class,
	}


def main() -> None:
	parser = argparse.ArgumentParser(description="Analyze YOLO dataset quality")
	parser.add_argument(
		"--data",
		type=str,
		required=True,
		help="Path to data.yaml",
	)
	parser.add_argument(
		"--json-out",
		type=str,
		default=None,
		help="Optional output path for JSON report",
	)
	args = parser.parse_args()

	data_yaml = Path(args.data).resolve()
	config = load_data_yaml(data_yaml)

	class_names = build_class_map(config["names"], int(config["nc"]))

	split_paths = {
		"train": resolve_split_image_dir(data_yaml.parent, "train", config["train"]),
		"val": resolve_split_image_dir(data_yaml.parent, "val", config["val"]),
		"test": resolve_split_image_dir(data_yaml.parent, "test", config["test"]),
	}

	print("Dataset analysis")
	print(f"Config: {data_yaml}")
	print(f"Classes ({len(class_names)}): {', '.join(class_names.values())}")

	all_stats = []
	total_instances = defaultdict(int)

	for split_name, image_dir in split_paths.items():
		stats = analyze_split(split_name, image_dir, len(class_names))
		print_split_report(stats, class_names)
		all_stats.append(stats)

		for cls_id, count in stats.class_instances.items():
			total_instances[cls_id] += count

	print("\n=== OVERALL ===")
	print(f"Total images      : {sum(s.total_images for s in all_stats)}")
	print(f"Total labeled     : {sum(s.labeled_images for s in all_stats)}")
	print(f"Total missing     : {sum(s.missing_label_files for s in all_stats)}")
	print(f"Total empty       : {sum(s.empty_label_files for s in all_stats)}")
	print(f"Total orphan      : {sum(s.orphan_label_files for s in all_stats)}")
	print(f"Total bad lines   : {sum(s.bad_label_lines for s in all_stats)}")

	print("Overall class instances:")
	for class_id in sorted(class_names.keys()):
		print(
			f"  - {class_names[class_id]:<10} (id={class_id:2d}): "
			f"{total_instances[class_id]}"
		)

	if args.json_out:
		report = {
			"config": str(data_yaml),
			"classes": class_names,
			"splits": [to_serializable(s, class_names) for s in all_stats],
			"overall": {
				"total_images": sum(s.total_images for s in all_stats),
				"total_labeled_images": sum(s.labeled_images for s in all_stats),
				"total_missing_labels": sum(s.missing_label_files for s in all_stats),
				"total_empty_labels": sum(s.empty_label_files for s in all_stats),
				"total_orphan_labels": sum(s.orphan_label_files for s in all_stats),
				"total_bad_lines": sum(s.bad_label_lines for s in all_stats),
				"instances_per_class": {
					class_names[i]: total_instances[i] for i in sorted(class_names.keys())
				},
			},
		}

		output_path = Path(args.json_out).resolve()
		output_path.parent.mkdir(parents=True, exist_ok=True)
		output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
		print(f"\nJSON report saved to: {output_path}")


if __name__ == "__main__":
	main()
