"""
app.py
------
SAGE Smart Stove - Flask backend.

Serves the dashboard frontend and exposes REST APIs consumed both by
the web UI and by the ESP32 microcontroller.
"""

import random
import threading
import time
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, render_template

from database.db import init_db, get_connection, get_settings, update_settings
from utils.risk_engine import evaluate
from utils.notifications import send_notification

app = Flask(__name__)

DEVICE_ID = "ESP32-SAGE-01"

# In-memory "last known" snapshot so /api/dashboard is instant even
# before the DB round-trip. Updated every time new sensor data arrives.
latest_snapshot = {
    "temperature": 41,
    "gas": 90,
    "motion": True,
    "flame": True,
    "overflow": False,
    "riskScore": 5,
    "riskLevel": "SAFE",
    "safetyScore": 95,
    "gasValve": "OPEN",
    "buzzer": False,
    "led": "GREEN",
    "reasons": ["All readings within safe operating range"],
    "recommendedActions": ["No action required"],
    "timestamp": datetime.utcnow().isoformat() + "Z",
}
snapshot_lock = threading.Lock()


# ---------------------------------------------------------------------
# Core processing: shared by both the real ESP32 endpoint and the demo
# simulator so behavior is identical regardless of data source.
# ---------------------------------------------------------------------
def process_sensor_reading(data: dict):
    thresholds = get_settings()
    thresholds = {
        "gas_threshold": float(thresholds.get("gas_threshold", 400)),
        "temperature_threshold": float(thresholds.get("temperature_threshold", 80)),
        "risk_threshold": float(thresholds.get("risk_threshold", 61)),
    }

    result = evaluate(data, thresholds)

    conn = get_connection()
    conn.execute(
        """INSERT INTO sensor_logs (temperature, gas, motion, flame, overflow, risk_score, risk_level, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.get("temperature"),
            data.get("gas"),
            int(bool(data.get("motion"))),
            int(bool(data.get("flame"))),
            int(bool(data.get("overflow"))),
            result["riskScore"],
            result["riskLevel"],
            result["timestamp"],
        ),
    )

    action_taken = ", ".join(result["recommendedActions"])

    # Log an alert row whenever we leave SAFE territory
    if result["riskLevel"] in ("WARNING", "EMERGENCY"):
        alert_type = result["reasons"][0] if result["reasons"] else "Risk Detected"
        conn.execute(
            """INSERT INTO alerts (alert_type, severity, temperature, gas, motion, flame, risk_score, action_taken, status, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                alert_type,
                result["riskLevel"],
                data.get("temperature"),
                data.get("gas"),
                int(bool(data.get("motion"))),
                int(bool(data.get("flame"))),
                result["riskScore"],
                action_taken,
                "Completed",
                result["timestamp"],
            ),
        )
        if result["riskLevel"] == "EMERGENCY":
            send_notification(alert_type, result["riskScore"], action_taken, result["timestamp"])

    conn.execute(
        "UPDATE devices SET status='online', last_seen=? WHERE device_id=?",
        (result["timestamp"], DEVICE_ID),
    )
    conn.commit()
    conn.close()

    with snapshot_lock:
        latest_snapshot.update(
            {
                "temperature": data.get("temperature"),
                "gas": data.get("gas"),
                "motion": bool(data.get("motion")),
                "flame": bool(data.get("flame")),
                "overflow": bool(data.get("overflow")),
                "riskScore": result["riskScore"],
                "riskLevel": result["riskLevel"],
                "safetyScore": result["safetyScore"],
                "gasValve": result["command"]["gasValve"],
                "buzzer": result["command"]["buzzer"],
                "led": result["command"]["led"],
                "reasons": result["reasons"],
                "recommendedActions": result["recommendedActions"],
                "timestamp": result["timestamp"],
            }
        )

    return result


# ---------------------------------------------------------------------
# Demo sensor simulator - runs in a background thread so the dashboard
# feels alive during a hackathon demo without real hardware attached.
# Toggle off any time by setting SIMULATOR_ENABLED = False, or it will
# pause automatically once real ESP32 data starts arriving.
# ---------------------------------------------------------------------
SIMULATOR_ENABLED = True
last_real_sensor_time = None


def sensor_simulator():
    state = {"temperature": 28.0, "gas": 90.0, "motion": True, "flame": False, "overflow": False}
    scenario_timer = 0
    scenario = "idle"

    while True:
        time.sleep(4)
        if not SIMULATOR_ENABLED:
            continue
        # Pause simulator for 60s after a real sensor reading comes in
        if last_real_sensor_time and (datetime.utcnow() - last_real_sensor_time) < timedelta(seconds=60):
            continue

        scenario_timer -= 1
        if scenario_timer <= 0:
            scenario = random.choices(
                ["idle", "cooking", "warning_spike", "emergency_spike"],
                weights=[45, 40, 10, 5],
            )[0]
            scenario_timer = random.randint(5, 12)

        if scenario == "idle":
            state["temperature"] += random.uniform(-0.5, 0.3)
            state["temperature"] = max(24, min(state["temperature"], 32))
            state["gas"] += random.uniform(-5, 5)
            state["gas"] = max(60, min(state["gas"], 130))
            state["motion"] = random.random() > 0.3
            state["flame"] = False
            state["overflow"] = False
        elif scenario == "cooking":
            state["temperature"] += random.uniform(0, 1.2)
            state["temperature"] = max(30, min(state["temperature"], 65))
            state["gas"] += random.uniform(-10, 15)
            state["gas"] = max(120, min(state["gas"], 280))
            state["motion"] = random.random() > 0.1
            state["flame"] = True
            state["overflow"] = random.random() > 0.97
        elif scenario == "warning_spike":
            state["temperature"] = random.uniform(70, 82)
            state["gas"] = random.uniform(200, 380)
            state["motion"] = random.random() > 0.5
            state["flame"] = random.random() > 0.4
            state["overflow"] = False
        elif scenario == "emergency_spike":
            state["temperature"] = random.uniform(85, 105)
            state["gas"] = random.uniform(420, 600)
            state["motion"] = False
            state["flame"] = False
            state["overflow"] = random.random() > 0.6

        with app.app_context():
            try:
                process_sensor_reading(dict(state))
            except Exception as e:
                print("simulator error:", e)


# =======================================================================
# PAGE ROUTES
# =======================================================================
@app.route("/")
def index():
    return render_template("dashboard.html", active="dashboard")


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html", active="analytics")


@app.route("/alerts")
def alerts_page():
    return render_template("alerts.html", active="alerts")


@app.route("/devices")
def devices_page():
    return render_template("devices.html", active="devices")


@app.route("/control")
def control_page():
    return render_template("control.html", active="control")


@app.route("/settings")
def settings_page():
    return render_template("settings.html", active="settings")


# =======================================================================
# ESP32 <-> BACKEND API
# =======================================================================
@app.route("/api/sensors", methods=["POST"])
def api_sensors():
    """Receives live sensor JSON from the ESP32 and returns the command payload."""
    global last_real_sensor_time
    data = request.get_json(force=True, silent=True) or {}

    required = ["temperature", "gas", "motion", "flame", "overflow"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        data["temperature"] = float(data["temperature"])
        data["gas"] = float(data["gas"])
    except (TypeError, ValueError):
        return jsonify({"error": "temperature and gas must be numeric"}), 400

    last_real_sensor_time = datetime.utcnow()
    result = process_sensor_reading(data)

    return jsonify(
        {
            "risk": result["riskLevel"],
            "riskScore": result["riskScore"],
            "gasValve": result["command"]["gasValve"],
            "buzzer": result["command"]["buzzer"],
            "led": result["command"]["led"],
        }
    )


# =======================================================================
# WEBSITE APIs
# =======================================================================
@app.route("/api/dashboard")
def api_dashboard():
    with snapshot_lock:
        snapshot = dict(latest_snapshot)
    #conn = get_connection()
    #device = conn.execute("SELECT * FROM devices WHERE device_id=?", (DEVICE_ID,)).fetchone()
    #conn.close()
    snapshot["deviceStatus"] = "online" #device["status"] if device else "offline"
    return jsonify(snapshot)


@app.route("/api/history")
def api_history():
    date = request.args.get("date")
    alert_type = request.args.get("type")
    severity = request.args.get("severity")

    query = "SELECT * FROM alerts WHERE 1=1"
    params = []
    if date:
        query += " AND timestamp LIKE ?"
        params.append(f"{date}%")
    if alert_type:
        query += " AND alert_type LIKE ?"
        params.append(f"%{alert_type}%")
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    query += " ORDER BY timestamp DESC LIMIT 200"

    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/analytics")
def api_analytics():
    conn = get_connection()

    # Time series: last 50 sensor readings (temperature / gas / motion / risk)
    series_rows = conn.execute(
        "SELECT temperature, gas, motion, risk_score, timestamp FROM sensor_logs ORDER BY id DESC LIMIT 50"
    ).fetchall()
    series = [dict(r) for r in reversed(series_rows)]

    # Weekly alert counts (last 7 days) grouped by day
    weekly_alerts = conn.execute(
        """SELECT substr(timestamp, 1, 10) as day, COUNT(*) as count
           FROM alerts GROUP BY day ORDER BY day DESC LIMIT 7"""
    ).fetchall()

    # Alert type breakdown (for emergency-count style cards)
    type_counts = conn.execute(
        """SELECT
             SUM(CASE WHEN alert_type LIKE '%Gas%' THEN 1 ELSE 0 END) as gas_leak,
             SUM(CASE WHEN alert_type LIKE '%Overflow%' THEN 1 ELSE 0 END) as overflow,
             SUM(CASE WHEN severity = 'EMERGENCY' THEN 1 ELSE 0 END) as auto_shutoff,
             COUNT(*) as total
           FROM alerts"""
    ).fetchone()

    # Averages
    averages = conn.execute(
        "SELECT AVG(temperature) as avg_temp, AVG(risk_score) as avg_risk, COUNT(*) as readings FROM sensor_logs"
    ).fetchone()

    # Estimate cooking duration: proxy = fraction of readings where flame=1, scaled to a day
    flame_rows = conn.execute("SELECT flame, timestamp FROM sensor_logs ORDER BY id DESC LIMIT 200").fetchall()
    flame_on_ratio = (
        sum(1 for r in flame_rows if r["flame"]) / len(flame_rows) if flame_rows else 0
    )
    estimated_daily_cooking_minutes = round(flame_on_ratio * 24 * 60 / 6, 1)  # rough demo estimate

    # Gas savings estimate: avg LPG burner consumption ~ 0.35 kg/hour
    lpg_kg_per_hour = 0.35
    daily_hours_on = estimated_daily_cooking_minutes / 60
    daily_gas_used_kg = round(daily_hours_on * lpg_kg_per_hour, 2)
    # "Saved" = time the system auto-shut valve early vs. an assumed unmonitored baseline (+15%)
    daily_gas_saved_kg = round(daily_gas_used_kg * 0.15, 2)
    weekly_gas_saved_kg = round(daily_gas_saved_kg * 7, 2)
    monthly_gas_saved_kg = round(daily_gas_saved_kg * 30, 2)

    conn.close()

    safety_score = round(100 - (averages["avg_risk"] or 0))

    return jsonify(
        {
            "series": series,
            "weeklyAlerts": [dict(r) for r in reversed(weekly_alerts)],
            "alertTypeCounts": dict(type_counts),
            "averageTemperature": round(averages["avg_temp"] or 0, 1),
            "averageRiskScore": round(averages["avg_risk"] or 0, 1),
            "safetyScore": max(0, min(100, safety_score)),
            "estimatedDailyCookingMinutes": estimated_daily_cooking_minutes,
            "gasSavings": {
                "daily": daily_gas_saved_kg,
                "weekly": weekly_gas_saved_kg,
                "monthly": monthly_gas_saved_kg,
                "note": "Estimated using burner ON duration and average LPG consumption (~0.35 kg/hour).",
            },
        }
    )


@app.route("/api/device-status")
def api_device_status():
    conn = get_connection()
    device = conn.execute("SELECT * FROM devices WHERE device_id=?", (DEVICE_ID,)).fetchone()
    conn.close()

    with snapshot_lock:
        snap = dict(latest_snapshot)

    is_online = True #device["status"] == "online" if device else False

    sensors = {
        "esp32": "Connected" if is_online else "Offline",
        "mq6_gas_sensor": "Working",
        "flame_sensor": "Working",
        "temperature_sensor": "Working",
        "pir_sensor": "Working",
        "overflow_sensor": "Working",
        "solenoid_valve": "Ready",
        "buzzer": "Ready",
        "led_indicator": "Ready",
        "wifi_status": "Connected" if is_online else "Disconnected",
    }

    return jsonify(
        {
            "deviceId": DEVICE_ID,
            "lastCommunication": device["last_seen"] if device else None,
            "sensors": sensors,
            "currentRiskLevel": snap["riskLevel"],
        }
    )


@app.route("/api/manual-control", methods=["POST"])
def api_manual_control():
    data = request.get_json(force=True, silent=True) or {}
    command = data.get("command")

    valid_commands = {
        "gas_off", "gas_on", "restart_esp32", "alarm_off",
        "emergency_shutdown", "test_alarm",
    }
    if command not in valid_commands:
        return jsonify({"error": "Unknown command"}), 400

    conn = get_connection()
    timestamp = datetime.utcnow().isoformat() + "Z"
    conn.execute(
        "INSERT INTO commands (command, status, timestamp) VALUES (?, ?, ?)",
        (command, "Sent", timestamp),
    )

    # Reflect immediate effect in the in-memory snapshot for demo purposes
    with snapshot_lock:
        if command == "gas_off":
            latest_snapshot["gasValve"] = "CLOSE"
        elif command == "gas_on":
            latest_snapshot["gasValve"] = "OPEN"
        elif command == "alarm_off":
            latest_snapshot["buzzer"] = False
        elif command == "emergency_shutdown":
            latest_snapshot["gasValve"] = "CLOSE"
            latest_snapshot["buzzer"] = True
            latest_snapshot["led"] = "RED"
            latest_snapshot["riskLevel"] = "EMERGENCY"
        elif command == "test_alarm":
            latest_snapshot["buzzer"] = True

    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "command": command, "timestamp": timestamp})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "GET":
        return jsonify(get_settings())

    data = request.get_json(force=True, silent=True) or {}
    update_settings(data)
    return jsonify({"status": "saved", "settings": get_settings()})


if __name__ == "__main__":
    init_db()
    sim_thread = threading.Thread(target=sensor_simulator, daemon=True)
    sim_thread.start()
    app.run(debug=True, host="0.0.0.0", port=5000)
