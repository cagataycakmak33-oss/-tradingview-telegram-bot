
print("BOT TESTI BASLADI")
print("CHAT_ID:", CHAT_ID)

url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": "🚀 TEST MESAJI - Trading bot bağlantısı çalışıyor!"
}

response = requests.post(url, data=data)

print("TELEGRAM CEVABI:")
print(response.status_code)
print(response.text)
