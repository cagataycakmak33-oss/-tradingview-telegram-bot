import os
import requests
import borsapy as bp
from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# AYARLAR
# =========================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GONDERILEN_DOSYA = "gonderilen_hisseler.txt"

EMA_PERIOD = 14
RSI_PERIOD = 14
BASE_PERIOD = 26


# =========================================================
# TELEGRAM
# =========================================================

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

    print(
        "Telegram:",
        response.status_code
    )

    return response.ok


# =========================================================
# GÖNDERİLEN HİSSELER
# =========================================================

def gonderilenleri_oku():

    if not os.path.exists(GONDERILEN_DOSYA):
        return set()

    with open(
        GONDERILEN_DOSYA,
        "r",
        encoding="utf-8"
    ) as dosya:

        return {
            satir.strip()
            for satir in dosya
            if satir.strip()
        }


def gonderilenleri_kaydet(hisseler):

    with open(
        GONDERILEN_DOSYA,
        "w",
        encoding="utf-8"
    ) as dosya:

        for hisse in sorted(hisseler):
            dosya.write(hisse + "\n")


# =========================================================
# PİYASA SAATİ
# =========================================================

def piyasa_acik_mi():

    now = datetime.now(
        ZoneInfo("Europe/Istanbul")
    )

    # Cumartesi / Pazar
    if now.weekday() >= 5:
        return False

    dakika = (
        now.hour * 60
        + now.minute
    )

    baslangic = (
        9 * 60 + 40
    )

    bitis = (
        18 * 60 + 10
    )

    return (
        baslangic
        <= dakika
        <= bitis
    )


# =========================================================
# BIST 100
# =========================================================

def bist100_listesi():

    index = bp.Index("XU100")

    return {
        hisse.upper()
        for hisse in index.component_symbols
    }


# =========================================================
# RSI 14
# =========================================================

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


# =========================================================
# HİSSE ANALİZİ
# =========================================================

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

        # -------------------------------------------------
        # EMA 14
        # -------------------------------------------------

        df["EMA14"] = (
            df["Close"]
            .ewm(
                span=EMA_PERIOD,
                adjust=False
            )
            .mean()
        )

        # -------------------------------------------------
        # RSI 14
        # -------------------------------------------------

        df["RSI14"] = rsi_hesapla(
            df["Close"]
        )

        # -------------------------------------------------
        # ICHIMOKU BASE LINE
        # 9 / 26 / 52 / 26
        #
        # Base Line = 26 dönemlik
        # en yüksek + en düşük / 2
        # -------------------------------------------------

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

        # -------------------------------------------------
        # 1. ŞART
        #
        # FİYAT BASE LINE'I AŞAĞI KESİYOR
        #
        # Önce:
        # Fiyat >= Base Line
        #
        # Sonra:
        # Fiyat < Base Line
        # -------------------------------------------------

        ichimoku_sinyal = (
            onceki["Close"]
            >=
            onceki["BASE"]
            and
            son["Close"]
            <
            son["BASE"]
        )

        # -------------------------------------------------
        # 2. ŞART
        #
        # Fiyat EMA14'ün en az %3 üzerinde
        # -------------------------------------------------

        ema_sinyal = (
            son["Close"]
            >=
            son["EMA14"] * 1.03
        )

        # -------------------------------------------------
        # 3. ŞART
        #
        # RSI > 50
        # -------------------------------------------------

        rsi_sinyal = (
            son["RSI14"] > 50
        )

        # -------------------------------------------------
        # TÜM ŞARTLAR
        # -------------------------------------------------

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
            type(hata).__name__,
            str(hata)
        )

        return None


# =========================================================
# ANA PROGRAM
# =========================================================

def main():

    print("")
    print(
        "===================================="
    )

    print(
        "TRADING BOT BASLADI"
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

    # -----------------------------------------------------
    # PİYASA SAATİ KONTROLÜ
    # -----------------------------------------------------

    if not piyasa_acik_mi():

        print(
            "Piyasa saati disinda."
        )

        print(
            "Tarama yapilmayacak."
        )

        return

    # -----------------------------------------------------
    # BIST 100
    # -----------------------------------------------------

    print(
        "BIST 100 listesi aliniyor..."
    )

    bist100 = (
        bist100_listesi()
    )

    print(
        "BIST 100 hisse sayisi:",
        len(bist100)
    )

    # Şimdilik BIST 100
    tarama_listesi = sorted(
        bist100
    )

    print(
        "Toplam taranacak hisse:",
        len(tarama_listesi)
    )

    # -----------------------------------------------------
    # DAHA ÖNCE GÖNDERİLENLER
    # -----------------------------------------------------

    gonderilenler = (
        gonderilenleri_oku()
    )

    bulunan = []

    # -----------------------------------------------------
    # TARAMA
    # -----------------------------------------------------

    for symbol in tarama_listesi:

        sonuc = analiz_et(
            symbol
        )

        if sonuc:

            # Daha önce Telegram'a
            # gönderildiyse tekrar gönderme

            if symbol not in gonderilenler:

                bulunan.append(
                    sonuc
                )

                gonderilenler.add(
                    symbol
                )

    # -----------------------------------------------------
    # GÖNDERİLENLERİ KAYDET
    # -----------------------------------------------------

    gonderilenleri_kaydet(
        gonderilenler
    )

    # -----------------------------------------------------
    # SONUÇ
    # -----------------------------------------------------

    print("")
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

    # -----------------------------------------------------
    # TELEGRAM
    # -----------------------------------------------------

    for sonuc in bulunan:

        mesaj = (
            "🚨 YENİ HİSSE\n\n"

            f"📈 {sonuc['symbol']}\n"

            f"🕒 {now.strftime('%H:%M')}\n\n"

            f"💰 Giriş: "
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


# =========================================================
# PROGRAMI BAŞLAT
# =========================================================

if __name__ == "__main__":
    main()
