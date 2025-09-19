import json
import random
import string
from datetime import datetime, timedelta
import os

REG_FILE = "data/registrations.json"

def load_data():
    if not os.path.exists(REG_FILE):
        return {"codes": {}, "linked": {}}
    with open(REG_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(REG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def generate_code(length=10):
    return ''.join(random.choices(string.digits, k=length))

def create_registration_code(steamid, ttl_minutes=30):
    data = load_data()
    code = generate_code()
    expires = (datetime.now() + timedelta(minutes=ttl_minutes)).isoformat()

    data["codes"][code] = {
        "steamid": steamid,
        "expires": expires
    }

    save_data(data)
    return code

def link_telegram_to_steam(user_id, code):
    data = load_data()
    entry = data["codes"].get(code)

    if not entry:
        return None, "❌ Код не найден."

    if datetime.fromisoformat(entry["expires"]) < datetime.now():
        return None, "⌛ Срок действия кода истёк."

    steamid = entry["steamid"]
    data["linked"][str(user_id)] = steamid
    del data["codes"][code]
    save_data(data)

    return steamid, None

def get_steamid_by_user(user_id):
    data = load_data()
    return data["linked"].get(str(user_id))

def cleanup_expired_codes():
    data = load_data()
    now = datetime.now()
    expired = [code for code, entry in data["codes"].items()
               if datetime.fromisoformat(entry["expires"]) < now]

    for code in expired:
        del data["codes"][code]

    if expired:
        save_data(data)
        print(f"🧹 Удалено просроченных кодов: {len(expired)}")
