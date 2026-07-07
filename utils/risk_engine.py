"""
risk_engine.py
--------------
Rule-based AI Decision Engine for the SAGE Smart Stove system.

This module deliberately avoids machine learning. Every decision is made
from explicit, explainable rules so that judges / users can see exactly
why a risk score was produced. This is the "brain" referenced in the
project spec as Module 2 (Smart Risk Prediction Engine) and Module 3
(Decision Engine).
"""

from datetime import datetime

# ---- Rule weights (points added to the risk score) -------------------
RULES = {
    "gas_leak": 60,          # gas reading above critical threshold
    "flame_off_gas_on": 50,  # gas valve open / gas detected but no flame
    "high_temperature": 25,  # kitchen temperature above safe threshold
    "no_human_presence": 20, # PIR sensor reports no one in the kitchen
    "overflow_detected": 30, # boil-over / overflow sensor triggered
}

# ---- Risk level bands --------------------------------------------------
def risk_level_for_score(score: int) -> str:
    if score >= 61:
        return "EMERGENCY"
    if score >= 31:
        return "WARNING"
    return "SAFE"


def evaluate(sensor_data: dict, thresholds: dict) -> dict:
    """
    Evaluate a single sensor reading against the rule set.

    sensor_data: {
        "temperature": float,
        "gas": float,          # ppm-like reading from MQ-6
        "motion": bool,
        "flame": bool,
        "overflow": bool
    }
    thresholds: {
        "gas_threshold": float,
        "temperature_threshold": float,
        "risk_threshold": float   # not used for scoring, only alarms
    }

    Returns a dict with score, level, reasons, recommended actions and
    the raw command payload that should be sent back to the ESP32.
    """
    reasons = []
    score = 0

    temperature = float(sensor_data.get("temperature", 0))
    gas = float(sensor_data.get("gas", 0))
    motion = bool(sensor_data.get("motion", False))
    flame = bool(sensor_data.get("flame", False))
    overflow = bool(sensor_data.get("overflow", False))

    gas_threshold = thresholds.get("gas_threshold", 400)
    temp_threshold = thresholds.get("temperature_threshold", 80)

    # Rule 1: Gas leak
    if gas >= gas_threshold:
        score += RULES["gas_leak"]
        reasons.append(f"Gas concentration {gas:.0f} ppm exceeds threshold {gas_threshold:.0f} ppm")

    # Rule 2: Flame OFF while gas is ON (gas present but no flame = leak/unlit burner)
    if gas >= (gas_threshold * 0.5) and not flame:
        score += RULES["flame_off_gas_on"]
        reasons.append("Gas detected but flame is OFF (possible unlit burner or leak)")

    # Rule 3: High temperature
    if temperature >= temp_threshold:
        score += RULES["high_temperature"]
        reasons.append(f"Kitchen temperature {temperature:.0f}°C exceeds threshold {temp_threshold:.0f}°C")

    # Rule 4: No human presence while stove is active
    if not motion and (flame or gas >= (gas_threshold * 0.3)):
        score += RULES["no_human_presence"]
        reasons.append("No human presence detected while stove appears active")

    # Rule 5: Overflow detected
    if overflow:
        score += RULES["overflow_detected"]
        reasons.append("Overflow / boil-over detected")

    score = min(score, 100)
    level = risk_level_for_score(score)

    if not reasons:
        reasons.append("All readings within safe operating range")

    # Recommended actions & ESP32 command payload
    actions = []
    command = {
        "risk": level,
        "riskScore": score,
        "gasValve": "OPEN",
        "buzzer": False,
        "led": "GREEN",
    }

    if level == "WARNING":
        actions = ["Monitor closely", "Notify user"]
        command.update({"gasValve": "OPEN", "buzzer": False, "led": "YELLOW"})
    elif level == "EMERGENCY":
        actions = ["Close Gas Valve", "Activate Alarm", "Notify User", "Flash LEDs"]
        command.update({"gasValve": "CLOSE", "buzzer": True, "led": "RED"})
    else:
        actions = ["No action required"]

    safety_score = max(0, 100 - score)

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "riskScore": score,
        "riskLevel": level,
        "safetyScore": safety_score,
        "reasons": reasons,
        "recommendedActions": actions,
        "command": command,
    }
