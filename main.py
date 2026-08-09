import os
import requests
import borsapy as bp
from io import BytesIO
from pypdf import PdfReader
from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# AYARLAR
# =========================================================

PDF_URL = "https://www.borsaistanbul.com/files/duyuru-48375-TR.pdf"

EMA_PERIOD = 14
RSI_PERIOD = 14
KIJUN_PERIOD = 26

START_HOUR = 9
START_MINUTE = 40

END_HOUR = 18
END_MINUTE = 10


# =========================================================
# TELEGRAM
# =========================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def send_telegram(message):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    response = requests.post(
        url,
        data=data,
        timeout=20
    )

    print("Telegram:", response.status_code)

    return response.ok


# =========================================================
# ÇALIŞMA SAATİ
# =========================================================

def piyasa_saati():

    now = datetime.now(
        ZoneInfo("Europe/Istanbul")
    )

    # Cumartesi / Pazar
    if now.weekday() >= 5:
        return False

    dakika = now.hour * 60 + now.minute

    baslangic = START_HOUR * 60 + START_MINUTE
    bitis = END_HOUR * 60 + END_MINUTE

    return baslangic <= dakika <= bitis


# =========================================================
# BIST 100
# =========================================================

def bist100_listesi():

    index = bp.Index("XU100")

    return {
        x.upper()
        for x in index.component_symbols
    }


# =========================================================
# ANA PAZAR
# =========================================================

def ana_pazar_listesi():

    print("Borsa Istanbul resmi liste indiriliyor...")

    response = requests.get(
        PDF_URL,
        timeout=30
    )

    response.raise_for_status()

    reader = PdfReader(
        BytesIO(response.content)
    )

    ana_pazar = set()

    # Türkçe PDF'de pazar dağılımı 2. sayfadadır.
    page = reader.pages[1]

    text = page.extract_text() or ""

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        tokens = line.split()

        # Satırlarda düzen:
        # 5 Yıldız + 5 Ana Pazar + 1 Alt Pazar
        #
        # Dolayısıyla Ana Pazar sütunu:
        # tokens[5:10]

        if len(tokens) >= 6:

            adaylar = tokens[5:10]

            for symbol in adaylar:

                symbol = symbol.upper().strip()

                if (
                    3 <= len(symbol) <= 6
                    and symbol.isalnum()
                ):
                    ana_pazar.add(symbol)

    print(
        "Ana Pazar hissesi:",
        len(ana_pazar)
    )

    return ana_pazar


# =========================================================
# RSI
# =========================================================

def rsi_hesapla(close):

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / RSI_PERIOD,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / RSI_PERIOD,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss

    return 100 - (
        100 / (1 + rs)
    )


# =========================================================
# HISSE ANALİZİ
# =========================================================

def analiz(symbol):

    try:

        ticker = bp.Ticker(symbol)

        df = ticker.history(
            period="6mo"
        )

        if df is None or len(df) < 60:
            return None

        df = df.copy()

        # EMA 14
        df["EMA14"] = df["Close"].ewm(
            span=EMA_PERIOD,
            adjust=False
        ).mean()

        # RSI 14
        df["RSI14"] = rsi_hesapla(
            df["Close"]
        )

        # Ichimoku Base Line
        high_26 = df["High"].rolling(
            KIJUN_PERIOD
        ).max()

        low_26 = df["Low"].rolling(
            KIJUN_PERIOD
        ).min()

        df["BASE"] = (
            high_26 + low_26
        ) / 2

        onceki = df.iloc[-2]
        son = df.iloc[-1]

        # -------------------------------------------------
        # BASE LINE FIYATI ASAGI KESIYOR
        #
        # Önce:
        # Base <= Fiyat
        #
        # Sonra:
        # Base > Fiyat
        # -------------------------------------------------

        ichimoku = (
            onceki["BASE"] <= onceki["Close"]
            and
            son["BASE"] > son["Close"]
        )

        # EMA14
        ema = (
            son["Close"]
            >= son["EMA14"] * 1.03
        )

        # RSI
        rsi = (
            son["RSI14"] > 50
        )

        if ichimoku and ema and rsi:

            return {
                "symbol": symbol,
                "price": float(son["Close"]),
                "ema": float(son["EMA14"]),
                "rsi": float(son["RSI14"]),
                "base": float(son["BASE"])
            }

        return None

    except Exception as e:

        print(
            symbol,
            "HATA:",
            type(e)._name_,
            str(e)
        )

        return None


# =========================================================
# ANA PROGRAM
# =========================================================

def main():

    print("")
    print("====================================")
    print("TRADING BOT BASLADI")
    print("====================================")

    now = datetime.now(
        ZoneInfo("Europe/Istanbul")
    )

    print(
        "Saat:",
        now.strftime("%d.%m.%Y %H:%M")
    )

    # Hafta sonu / saat kontrolü
    if not piyasa_saati():

        print(
            "Piyasa saati disinda.",
            "Tarama yapilmayacak."
        )

        return

    # BIST 100
    bist100 = bist100_listesi()

    print(
        "BIST 100:",
        len(bist100)
    )

    # Ana Pazar
    ana_pazar = ana_pazar_listesi()

    # BIST 100 + Ana Pazar
    tarama_listesi = sorted(
        bist100 | ana_pazar
    )

    print(
        "TOPLAM TARAMA:",
        len(tarama_listesi)
    )

    bulunanlar = []

    for symbol in tarama_listesi:

        print(
            "Taranıyor:",
            symbol
        )

        sonuc = analiz(symbol)

        if sonuc:

            bulunanlar.append(
                sonuc
            )

            print(
                "🚨 SİNYAL:",
                symbol
            )

    print("")
    print("====================================")
    print("TARAMA TAMAMLANDI")
    print("====================================")

    print(
        "Bulunan:",
        len(bulunanlar)
    )

    # Telegram
    for sonuc in bulunanlar:

        mesaj = (
            "🚨 YENİ HİSSE\n\n"
            f"📈 {sonuc['symbol']}\n"
            f"🕒 {now.strftime('%H:%M')}\n\n"
            f"💰 Fiyat: {sonuc['price']:.2f} TL\n\n"
            "📊 Göstergeler\n"
            f"EMA14: {sonuc['ema']:.2f}\n"
            f"RSI14: {sonuc['rsi']:.2f}\n"
            f"Base Line: {sonuc['base']:.2f}\n\n"
            "📌 Taramaya yeni girdi."
        )

        send_telegram(
            mesaj
        )


if __name__ == "__main__":
    main()
