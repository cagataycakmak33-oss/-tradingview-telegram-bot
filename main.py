import os
import requests
import pandas as pd
import borsapy as bp
from datetime import datetime
from zoneinfo import ZoneInfo
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GONDERILEN_DOSYA = "gonderilen_hisseler.txt"
EMA_PERIOD = 14
RSI_PERIOD = 14
BASE_PERIOD = 26
def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": mesaj
        },
        timeout=20
    )
    print("Telegram:", response.status_code)
    return response.ok
def gonderilenleri_oku():
    if not os.path.exists(GONDERILEN_DOSYA):
        return set()
    with open(GONDERILEN_DOSYA, "r", encoding="utf-8") as dosya:
        return {
            satir.strip()
            for satir in dosya
            if satir.strip()
        }
def gonderilenleri_kaydet(hisseler):
    with open(GONDERILEN_DOSYA, "w", encoding="utf-8") as dosya:
        for hisse in sorted(hisseler):
            dosya.write(hisse + "\n")
def piyasa_acik_mi():
    now = datetime.now(
        ZoneInfo("Europe/Istanbul")
    )
    if now.weekday() >= 5:
        return False
    dakika = now.hour * 60 + now.minute
    return 9 * 60 + 40 <= dakika <= 18 * 60 + 10
def bist100_listesi():
    index = bp.Index("XU100")
    return {
        str(hisse).upper()
        for hisse in index.component_symbols
    }
def ana_pazar_listesi():
    """
    Borsa İstanbul Ana Pazar listesini resmi web
    sayfasından almaya çalışır.
    Liste alınamazsa boş küme döner.
    Böylece bot tamamen durmaz.
    """
    print("Ana Pazar listesi aliniyor...")
    url = "https://www.borsaistanbul.com/tr/sayfa/88/pazarlar"
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )
        response.raise_for_status()
        tablolar = pd.read_html(
            response.text
        )
        semboller = set()
        for tablo in tablolar:
            for sutun in tablo.columns:
                for deger in tablo[sutun].astype(str):
                    deger = deger.strip().upper()
                    if (
                        2 <= len(deger) <= 6
                        and deger.replace(".", "").isalnum()
                    ):
                        semboller.add(deger)
        print(
            "Ana Pazar aday sembol sayisi:",
            len(semboller)
        )
        return semboller
    except Exception as hata:
        print(
            "Ana Pazar listesi alinamadi:",
            type(hata)._name_,
            str(hata)
        )
        return set()
def tarama_listesi_olustur():
    print("====================================")
    print("HISSE LISTESI HAZIRLANIYOR")
    print("====================================")
    bist100 = bist100_listesi()
    print(
        "BIST 100:",
        len(bist100)
    )
    ana_pazar = ana_pazar_listesi()
    # BIST 100 + Ana Pazar
    toplam = (
        bist100
        | ana_pazar
    )
    print(
        "Ana Pazar:",
        len(ana_pazar)
    )
    print(
        "TOPLAM:",
        len(toplam)
    )
    return sorted(toplam)
def rsi_hesapla(close):
    delta = close.diff()
    kazanc = delta.clip(
        lower=0
    )
    kayip = -delta.clip(
        upper=0
    )
    ort_kazanc = kazanc.ewm(
        alpha=1 / RSI_PERIOD,
        adjust=False
    ).mean()
    ort_kayip = kayip.ewm(
        alpha=1 / RSI_PERIOD,
        adjust=False
    ).mean()
    rs = (
        ort_kazanc
        / ort_kayip
    )
    return 100 - (
        100 / (1 + rs)
    )
def analiz_et(symbol):
    try:
        print(
            "Taranıyor:",
            symbol
        )
        ticker = bp.Ticker(
            symbol
        )
        df = ticker.history(
            period="6mo"
        )
        if df is None:
            return None
        if len(df) < 60:
            return None
        df = df.copy()
        # EMA 14
        df["EMA14"] = (
            df["Close"]
            .ewm(
                span=EMA_PERIOD,
                adjust=False
            )
            .mean()
        )
        # RSI 14
        df["RSI14"] = rsi_hesapla(
            df["Close"]
        )
        # Ichimoku Base Line
        en_yuksek = (
            df["High"]
            .rolling(
                BASE_PERIOD
            )
            .max()
        )
        en_dusuk = (
            df["Low"]
            .rolling(
                BASE_PERIOD
            )
            .min()
        )
        df["BASE"] = (
            en_yuksek
            + en_dusuk
        ) / 2
        onceki = df.iloc[-2]
        son = df.iloc[-1]
        # Fiyat Base Line'i aşağı kesiyor
        ichimoku_sinyal = (
            onceki["Close"]
            >=
            onceki["BASE"]
            and
            son["Close"]
            <
            son["BASE"]
        )
        # Fiyat EMA14'ün en az %3 üzerinde
        ema_sinyal = (
            son["Close"]
            >=
            son["EMA14"] * 1.03
        )
        # RSI 50 üzerinde
        rsi_sinyal = (
            son["RSI14"] > 50
        )
        if (
            ichimoku_sinyal
            and ema_sinyal
            and rsi_sinyal
        ):
            print(
                "🚨 SİNYAL:",
                symbol
            )
            return {
                "symbol": symbol,
                "price": float(
                    son["Close"]
                ),
                "ema": float(
                    son["EMA14"]
                ),
                "rsi": float(
                    son["RSI14"]
                ),
                "base": float(
                    son["BASE"]
                )
            }
        return None
    except Exception as hata:
        print(
            symbol,
            "HATA:",
            type(hata)._name_,
            str(hata)
        )
        return None
def main():
    print(
        "===================================="
    )
    print(
        "BIST 100 + ANA PAZAR"
    )
    print(
        "TARAMA BOTU BASLADI"
    )
    print(
        "===================================="
    )
    now = datetime.now(
        ZoneInfo("Europe/Istanbul")
    )
    print(
        "Saat:",
        now.strftime(
            "%d.%m.%Y %H:%M"
        )
    )
    if not piyasa_acik_mi():
        print(
            "Piyasa saati disinda."
        )
        print(
            "Tarama yapilmayacak."
        )
        return
    tarama_listesi = (
        tarama_listesi_olustur()
    )
    print(
        "Toplam taranacak hisse:",
        len(tarama_listesi)
    )
    gonderilenler = (
        gonderilenleri_oku()
    )
    bulunan = []
    for symbol in tarama_listesi:
        sonuc = analiz_et(
            symbol
        )
        if sonuc:
            if symbol not in gonderilenler:
                bulunan.append(
                    sonuc
                )
                gonderilenler.add(
                    symbol
                )
    gonderilenleri_kaydet(
        gonderilenler
    )
    print(
        "===================================="
    )
    print(
        "TARAMA TAMAMLANDI"
    )
    print(
        "===================================="
    )
    print(
        "Yeni bulunan hisse:",
        len(bulunan)
    )
    for sonuc in bulunan:
        mesaj = (
            "🚨 YENİ HİSSE\n\n"
            f"📈 {sonuc['symbol']}\n"
            f"🕒 {now.strftime('%H:%M')}\n\n"
            f"💰 Fiyat: "
            f"{sonuc['price']:.2f} TL\n\n"
            "📊 Göstergeler\n"
            f"EMA14: "
            f"{sonuc['ema']:.2f}\n"
            f"RSI14: "
            f"{sonuc['rsi']:.2f}\n"
            f"Base Line: "
            f"{sonuc['base']:.2f}\n\n"
            "📌 Taramaya yeni girdi."
        )
        telegram_gonder(
            mesaj
        )
if __name__ == "__main__":
    main()
