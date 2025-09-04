# config.py

TOKEN = "8115059684:AAGkb3_k7qxyi3RovgZLc1rfxX7ww41syjc"
REQUEST_INTERVAL = 60  # секунд

ALLOWED_ADMINS = [297211090, 103527443]

SERVERS = [
    {
        "name": "7DTD PVE 1",
        "url": "http://109.106.138.168:8100",
        "auth": ("Hoka1nBG96s5pdXE", "bnSje6v71jRvMnsS"),
        "channel_id": -1002695272288
    },
    {
        "name": "7DTD PVE 2",
        "url": "http://109.106.138.168:8200",
        "auth": ("DfLssUdrONBpocwJ", "TYUwZXdYd3qjCPEF"),
        "channel_id": -1002695272284
    },
    {
        "name": "7DTD PVE 3",
        "url": "http://109.106.138.168:8300",
        "auth": ("HafdasnBG96pdXE", "bne6v7RvMnsS"),
        "channel_id": -1002695272289
    }
]

SERVERSRCON = [
    {
        "name": "Alpha",
        "host": "109.106.138.168",
        "port": 6066,
        "password": "dm-nuS4yHsFI"
    },
    {
        "name": "Bravo",
        "host": "192.168.1.100",
        "port": 6066,
        "password": "anotherpass"
    }
]   
# Хранилище времени последнего запроса
last_request_time = {}
