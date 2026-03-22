"""
Sequence detector for tracking Naruto hand sign sequences.
Detects when a user performs a complete jutsu hand sign sequence.
"""

import time
from dataclasses import dataclass, field
from jutsu_data import JUTSU_DATABASE


@dataclass
class SignEvent:
    """A confirmed hand sign event."""
    sign: str
    timestamp: float
    confidence: float


@dataclass 
class SequenceState:
    """Tracks the current state of sequence detection."""
    # Current sign being tracked
    current_sign: str = ""
    current_sign_start: float = 0.0
    current_confidence_sum: float = 0.0
    current_confidence_count: int = 0
    
    # Confirmed sign sequence
    confirmed_signs: list = field(default_factory=list)
    sign_events: list = field(default_factory=list)
    
    # Timing
    last_sign_time: float = 0.0
    sequence_timeout: float = 5.0  # Reset sequence after 5s of no signs
    
    # Match state
    matched_jutsu: str = ""
    matching_jutsu_candidates: list = field(default_factory=list)


class SequenceDetector:
    """
    Detects jutsu hand sign sequences from a stream of sign predictions.
    
    A sign must be held for `hold_duration` seconds to be confirmed.
    The sequence resets after `sequence_timeout` seconds of no new signs.
    """
    
    def __init__(self, hold_duration: float = 0.5, sequence_timeout: float = 5.0):
        """
        Args:
            hold_duration: How long a sign must be held to confirm (seconds)
            sequence_timeout: Reset sequence after this many seconds of inactivity
        """
        self.hold_duration = hold_duration
        self.sequence_timeout = sequence_timeout
        self.state = SequenceState(sequence_timeout=sequence_timeout)
    
    def update(self, detected_sign: str, confidence: float) -> dict:
        """
        Update the sequence detector with a new detection.
        
        Args:
            detected_sign: The detected hand sign class name (e.g., "tiger")
            confidence: Detection confidence (0-1)
            
        Returns:
            dict with keys:
                - current_sign: Currently detected sign
                - confirmed_signs: List of confirmed signs in sequence
                - hold_progress: Progress of current sign hold (0-1)
                - matched_jutsu: Name of matched jutsu (if complete)
                - candidates: List of possible jutsu being performed
                - sign_just_confirmed: True if a sign was just confirmed this frame
        """
        now = time.time()
        result = {
            "current_sign": detected_sign,
            "confirmed_signs": list(self.state.confirmed_signs),
            "hold_progress": 0.0,
            "matched_jutsu": "",
            "candidates": [],
            "sign_just_confirmed": False,
        }
        
        # Check for sequence timeout
        if (self.state.confirmed_signs and 
            now - self.state.last_sign_time > self.sequence_timeout):
            self.reset()
            result["confirmed_signs"] = []
        
        if not detected_sign:
            # No sign detected — reset current tracking but keep sequence
            self.state.current_sign = ""
            self.state.current_sign_start = 0
            return result
        
        # Same sign as currently tracking
        if detected_sign == self.state.current_sign:
            self.state.current_confidence_sum += confidence
            self.state.current_confidence_count += 1
            
            elapsed = now - self.state.current_sign_start
            progress = min(1.0, elapsed / self.hold_duration)
            result["hold_progress"] = progress
            
            # Check if sign has been held long enough
            if elapsed >= self.hold_duration:
                avg_conf = (self.state.current_confidence_sum / 
                           self.state.current_confidence_count)
                
                # Only confirm if it's a new sign (not the same as last confirmed)
                last_confirmed = (self.state.confirmed_signs[-1] 
                                 if self.state.confirmed_signs else "")
                
                if detected_sign != last_confirmed:
                    self.state.confirmed_signs.append(detected_sign)
                    self.state.sign_events.append(SignEvent(
                        sign=detected_sign,
                        timestamp=now,
                        confidence=avg_conf
                    ))
                    self.state.last_sign_time = now
                    result["sign_just_confirmed"] = True
                    result["confirmed_signs"] = list(self.state.confirmed_signs)
                    
                    # Check for jutsu match
                    matched = self._check_jutsu_match()
                    if matched:
                        result["matched_jutsu"] = matched
                        self.state.matched_jutsu = matched
        else:
            # Different sign — start tracking new sign
            self.state.current_sign = detected_sign
            self.state.current_sign_start = now
            self.state.current_confidence_sum = confidence
            self.state.current_confidence_count = 1
        
        # Update candidates
        result["candidates"] = self._get_candidates()
        
        return result
    
    def _check_jutsu_match(self) -> str:
        """Check if confirmed signs match any jutsu sequence."""
        confirmed = self.state.confirmed_signs
        
        for jutsu in JUTSU_DATABASE:
            if confirmed == jutsu["signs"]:
                return jutsu["id"]
        
        return ""
    
    def _get_candidates(self) -> list[dict]:
        """Get list of jutsu that could match the current sequence."""
        confirmed = self.state.confirmed_signs
        if not confirmed:
            return []
        
        candidates = []
        for jutsu in JUTSU_DATABASE:
            signs = jutsu["signs"]
            # Check if confirmed sequence is a prefix of this jutsu
            if len(confirmed) <= len(signs):
                if confirmed == signs[:len(confirmed)]:
                    candidates.append({
                        "id": jutsu["id"],
                        "name": jutsu["name"],
                        "progress": len(confirmed) / len(signs),
                        "current_step": len(confirmed),
                        "total_steps": len(signs),
                        "next_sign": signs[len(confirmed)] if len(confirmed) < len(signs) else None,
                    })
        
        return candidates
    
    def reset(self):
        """Reset the sequence detector state."""
        self.state = SequenceState(sequence_timeout=self.sequence_timeout)
    
    def get_progress_text(self, result: dict) -> str:
        """Generate a human-readable progress string."""
        if result["matched_jutsu"]:
            jutsu = next(
                (j for j in JUTSU_DATABASE if j["id"] == result["matched_jutsu"]), 
                None
            )
            if jutsu:
                return f"🎯 {jutsu['name']} ACTIVATED!"
        
        if result["candidates"]:
            best = result["candidates"][0]
            progress_bar = "█" * best["current_step"] + "░" * (best["total_steps"] - best["current_step"])
            return (f"🔮 {best['name']} [{progress_bar}] "
                    f"{best['current_step']}/{best['total_steps']}"
                    f" — Next: {best['next_sign'].upper() if best['next_sign'] else 'DONE'}")
        
        if result["confirmed_signs"]:
            signs = " → ".join(s.upper() for s in result["confirmed_signs"])
            return f"Signs: {signs}"
        
        if result["current_sign"]:
            bar_len = int(result["hold_progress"] * 10)
            bar = "▓" * bar_len + "░" * (10 - bar_len)
            return f"Detecting: {result['current_sign'].upper()} [{bar}]"
        
        return "Waiting for hand signs..."
