[00:19, 10.08.2026] Çağatay: import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
print("YENI MAIN.PY CALISIYOR")
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=data)
    print("TELEGRAM CEVABI:")
    print(response.status_code)
    print(response.text)
def main():
    now = datetime.now(ZoneInfo("Europe/Istanbul"))
    print("TRADING BOT BASLADI")
    print("SAAT:", now.strftime("%H:%M"))
    send_telegram(
        "🚀 YENİ MAIN.PY ÇALIŞIYOR!\n\n"
        f"🕒 Saat: {now.strftime('%H:%M')}\n"
        "📌 T…
[00:20, 10.08.2026] Çağatay: import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
print("YENI MAIN.PY CALISIYOR")
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=data)
    print("TELEGRAM CEVABI:")
    print(response.status_code)
    print(response.text)
def main():
    now = datetime.now(ZoneInfo("Europe/Istanbul"))
    print("TRADING BOT BASLADI")
    print("SAAT:", now.strftime("%H:%M"))
    send_telegram(
        "🚀 YENİ MAIN.PY ÇALIŞIYOR!\n\n"
        f"🕒 Saat: {now.strftime('%H:%M')}\n"
        "📌 Telegram bağlantısı başarılı.\n"
        "📊 Gerçek hisse taraması için hazır."
    )
if _name_ == "_main__":
    main()
