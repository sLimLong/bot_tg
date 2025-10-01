import telnetlib
import re
import os
import json
from config import SERVERSRCON

SYNC_PATH = os.path.join("data", "ban_sync.json")

def fetch_banlist(server):
    try:
        tn = telnetlib.Telnet(server["host"], server["port"], timeout=5)
        tn.read_until(b"Please enter password:", timeout=3)
        tn.write(server["password"].encode("utf-8") + b"\n")
        tn.write(b"ban list\n")
        raw = tn.read_until(b">", timeout=5).decode("utf-8")
        tn.write(b"exit\n")

        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\S+) \((.*?)\) - (.+)"
        matches = re.findall(pattern, raw)

        return [
            {
                "date": date,
                "steamid": userid,
                "name": name,
                "reason": reason
            }
            for date, userid, name, reason in matches
        ]
    except:
        return []

def send_ban(server, entry):
    try:
        tn = telnetlib.Telnet(server["host"], server["port"], timeout=5)
        tn.read_until(b"Please enter password:", timeout=3)
        tn.write(server["password"].encode("utf-8") + b"\n")

        cmd = f"ban add {entry['steamid']} 365 days {entry['reason']} {entry['name']}"
        tn.write(cmd.encode("utf-8") + b"\n")
        tn.read_until(b">", timeout=5)
        tn.write(b"exit\n")
    except:
        pass

def sync_banlists():
    if len(SERVERSRCON) < 2:
        return

    bans_0 = fetch_banlist(SERVERSRCON[0])
    bans_1 = fetch_banlist(SERVERSRCON[1])

    ids_0 = {ban["steamid"]: ban for ban in bans_0}
    ids_1 = {ban["steamid"]: ban for ban in bans_1}

    # Баны, которых нет на втором сервере
    for steamid, entry in ids_0.items():
        if steamid not in ids_1:
            send_ban(SERVERSRCON[1], entry)

    for steamid, entry in ids_1.items():
        if steamid not in ids_0:
            send_ban(SERVERSRCON[0], entry)

    # Сохраняем текущую синхронизированную копию
    with open(SYNC_PATH, "w", encoding="utf-8") as f:
        json.dump({
            SERVERSRCON[0]["name"]: bans_0,
            SERVERSRCON[1]["name"]: bans_1
        }, f, indent=2, ensure_ascii=False)
