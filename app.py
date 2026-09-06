from flask import Flask, jsonify, request, render_template, session
import time
import json
import os
import secrets

app = Flask(__name__)
app.secret_key = "onax-session-2026"

KEY_FILE = "keys.json"
ADMIN_KEY = "vanloconax24"

def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_keys(keys):
    with open(KEY_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2)

@app.route("/")
def index():
    if not session.get("admin_login"):
        return render_template("login.html")
    return render_template("index.html")

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    key = data.get("key", "").strip()

    if key != ADMIN_KEY:
        return jsonify({
            "success": False,
            "error": "Sai Admin Key"
        }), 403

    session["admin_login"] = True
    return jsonify({"success": True})

@app.route("/api/admin/logout")
def admin_logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/create_key")
def create_key():
    if not session.get("admin_login"):
        return jsonify({
            "success": False,
            "error": "Chưa đăng nhập Admin"
        }), 403

    try:
        days = int(request.args.get("days", "1"))
        if days <= 0:
            return jsonify({
                "success": False,
                "error": "Số ngày không hợp lệ"
            }), 400
    except:
        return jsonify({
            "success": False,
            "error": "Số ngày không hợp lệ"
        }), 400

    key = "ONAX-" + secrets.token_hex(8).upper()

    keys = load_keys()
    keys[key] = {
        "days": days,
        "created": int(time.time()),
        "activated": False,
        "activated_at": None
    }
    save_keys(keys)

    return jsonify({
        "success": True,
        "key": key,
        "days": days
    })

@app.route("/api/check_key")
def check_key():
    key = request.args.get("key", "").strip()

    if not key:
        return jsonify({
            "success": False,
            "valid": False,
            "error": "Thiếu key"
        }), 400

    keys = load_keys()

    if key not in keys:
        return jsonify({
            "success": False,
            "valid": False,
            "error": "Key không tồn tại"
        }), 404

    data = keys[key]
    now = int(time.time())

    if not data.get("activated", False):
        data["activated"] = True
        data["activated_at"] = now
        save_keys(keys)

        expires = now + data["days"] * 86400

        return jsonify({
            "success": True,
            "valid": True,
            "first_use": True,
            "days": data["days"],
            "activated_at": now,
            "expires": expires
        })

    activated_at = data["activated_at"]
    expires = activated_at + data["days"] * 86400

    if now >= expires:
        return jsonify({
            "success": False,
            "valid": False,
            "error": "Key đã hết hạn"
        }), 403

    return jsonify({
        "success": True,
        "valid": True,
        "first_use": False,
        "days": data["days"],
        "activated_at": activated_at,
        "expires": expires,
        "remaining": expires - now
    })

@app.route("/api/status")
def status():
    return jsonify({
        "online": True,
        "time": int(time.time())
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
