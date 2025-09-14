# config.py

TOKEN = "
REQUEST_INTERVAL = 60  # секунд

ALLOWED_ADMINS = [297211090, 103527443]

SERVERS = [
    {
        "name": "7DTD PVE 1",
        "url": "http://109.106.138.168:8100",
        "auth": ("", ""),
        "channel_id": -1002695272288
    },
    {
        "name": "7DTD PVE 2",
        "url": "http://109.106.138.168:8200",
        "auth": ("", ""),
        "channel_id": -1002695272284
    },
    {
        "name": "7DTD PVE 3",
        "url": "http://109.106.138.168:8300",
        "auth": ("", ""),
        "channel_id": -1002695272289
    }
]

SERVERSRCON = [
    {
        "name": "Alpha",
        "host": "109.106.138.168",
        "port": ,
        "password": ""
    },
    {
        "name": "Bravo",
        "host": "192.168.1.100",
        "port": ,
        "password": ""
    }
]   
# Хранилище времени последнего запроса
last_request_time = {}
