import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=data)
    print("Telegram:", response.status_code, response.text)


def main():
    now = datetime.now(ZoneInfo("Europe/Istanbul"))

    print("TRADING BOT BASLADI")
    print("Saat:", now.strftime("%H:%M"))

    # Şimdilik bağlantıyı test ediyoruz.
    # Gerçek hisse taraması bir sonraki adımda eklenecek.

    send_telegram(
        "🚀 Trading Bot çalışıyor!\n\n"
        f"🕒 {now.strftime('%H:%M')}\n"
        "📌 Otomatik tarama sistemi hazır."
    )


if _name_ == "_main__":
    main()
