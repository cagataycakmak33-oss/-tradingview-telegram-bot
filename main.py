from config import TELEGRAM_TOKEN, CHAT_ID
import requests

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": mesaj
    }
    r = requests.post(url, data=data)
print(r.text)

telegram_gonder("🚀 Trading bot bağlantı testi başarılı!")
