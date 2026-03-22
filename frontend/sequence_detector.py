"""
Sequence detector for tracking Naruto hand sign sequences.
Runs client-side in the Gradio frontend.
"""

import time
from dataclasses import dataclass, field
from jutsu_data import JUTSU_DATABASE


@dataclass
class SequenceState:
    current_sign: str = ""
    current_sign_start: float = 0.0
    current_confidence_sum: float = 0.0
    current_confidence_count: int = 0
    confirmed_signs: list = field(default_factory=list)
    last_sign_time: float = 0.0
    sequence_timeout: float = 5.0
    matched_jutsu: str = ""


class SequenceDetector:
    def __init__(self, hold_duration: float = 0.5, sequence_timeout: float = 5.0):
        self.hold_duration = hold_duration
        self.sequence_timeout = sequence_timeout
        self.state = SequenceState(sequence_timeout=sequence_timeout)

    def update(self, detected_sign: str, confidence: float) -> dict:
        now = time.time()
        result = {
            "current_sign": detected_sign,
            "confirmed_signs": list(self.state.confirmed_signs),
            "hold_progress": 0.0,
            "matched_jutsu": "",
            "candidates": [],
            "sign_just_confirmed": False,
        }

        if (self.state.confirmed_signs and
                now - self.state.last_sign_time > self.sequence_timeout):
            self.reset()
            result["confirmed_signs"] = []

        if not detected_sign:
            self.state.current_sign = ""
            self.state.current_sign_start = 0
            return result

        if detected_sign == self.state.current_sign:
            self.state.current_confidence_sum += confidence
            self.state.current_confidence_count += 1
            elapsed = now - self.state.current_sign_start
            result["hold_progress"] = min(1.0, elapsed / self.hold_duration)

            if elapsed >= self.hold_duration:
                last_confirmed = self.state.confirmed_signs[-1] if self.state.confirmed_signs else ""
                if detected_sign != last_confirmed:
                    self.state.confirmed_signs.append(detected_sign)
                    self.state.last_sign_time = now
                    result["sign_just_confirmed"] = True
                    result["confirmed_signs"] = list(self.state.confirmed_signs)

                    matched = self._check_jutsu_match()
                    if matched:
                        result["matched_jutsu"] = matched
        else:
            self.state.current_sign = detected_sign
            self.state.current_sign_start = now
            self.state.current_confidence_sum = confidence
            self.state.current_confidence_count = 1

        result["candidates"] = self._get_candidates()
        return result

    def _check_jutsu_match(self) -> str:
        for jutsu in JUTSU_DATABASE:
            if self.state.confirmed_signs == jutsu["signs"]:
                return jutsu["id"]
        return ""

    def _get_candidates(self) -> list[dict]:
        confirmed = self.state.confirmed_signs
        if not confirmed:
            return []
        candidates = []
        for jutsu in JUTSU_DATABASE:
            signs = jutsu["signs"]
            if len(confirmed) <= len(signs) and confirmed == signs[:len(confirmed)]:
                candidates.append({
                    "id": jutsu["id"], "name": jutsu["name"],
                    "progress": len(confirmed) / len(signs),
                    "current_step": len(confirmed), "total_steps": len(signs),
                    "next_sign": signs[len(confirmed)] if len(confirmed) < len(signs) else None,
                })
        return candidates

    def reset(self):
        self.state = SequenceState(sequence_timeout=self.sequence_timeout)

    def get_progress_text(self, result: dict) -> str:
        if result["matched_jutsu"]:
            jutsu = next((j for j in JUTSU_DATABASE if j["id"] == result["matched_jutsu"]), None)
            return f"🎯 **{jutsu['name']}** ACTIVATED!" if jutsu else ""
        if result["candidates"]:
            b = result["candidates"][0]
            bar = "█" * b["current_step"] + "░" * (b["total_steps"] - b["current_step"])
            next_s = b["next_sign"].upper() if b["next_sign"] else "DONE"
            return f"🔮 {b['name']} [{bar}] {b['current_step']}/{b['total_steps']} — Next: **{next_s}**"
        if result["confirmed_signs"]:
            return "Signs: " + " → ".join(s.upper() for s in result["confirmed_signs"])
        if result["current_sign"]:
            n = int(result["hold_progress"] * 10)
            return f"Detecting: **{result['current_sign'].upper()}** [{'▓'*n}{'░'*(10-n)}]"
        return "Waiting for hand signs..."
