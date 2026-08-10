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

    print("Telegram:", response.status_code)

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

    baslangic = 9 * 60 + 40
    bitis = 18 * 60 + 10

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
        str(hisse).upper()
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
# PİVOT HESAPLAMA
# =========================================================

def pivot_hesapla(high, low, close):

    pivot = (
        high
        + low
        + close
    ) / 3

    r1 = (
        2 * pivot
        - low
    )

    r2 = (
        pivot
        + (high - low)
    )

    r3 = (
        high
        + 2 * (pivot - low)
    )

    s1 = (
        2 * pivot
        - high
    )

    return {
        "stop": s1,
        "k1": r1,
        "k2": r2,
        "k3": r3
    }


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
        #
        # Base Line = (26 günlük en yüksek + en düşük) / 2
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


        # -------------------------------------------------
        # SON 2 GÜN
        # -------------------------------------------------

        onceki = df.iloc[-2]

        son = df.iloc[-1]


        # -------------------------------------------------
        # 1 HAFTALIK DEĞİŞİM
        # Yaklaşık 5 işlem günü
        # -------------------------------------------------

        hafta_once = df.iloc[-6]

        bir_haftalik_degisim = (
            (
                son["Close"]
                / hafta_once["Close"]
            ) - 1
        ) * 100


        # -------------------------------------------------
        # GÜNLÜK DEĞİŞİM
        # -------------------------------------------------

        gunluk_degisim = (
            (
                son["Close"]
                / onceki["Close"]
            ) - 1
        ) * 100


        # -------------------------------------------------
        # HACİM
        # -------------------------------------------------

        hacim = float(
            son["Volume"]
        )


        # -------------------------------------------------
        # PİVOT
        #
        # Bir önceki işlem gününün
        # High / Low / Close değerleri kullanılır.
        # -------------------------------------------------

        pivot = pivot_hesapla(
            float(onceki["High"]),
            float(onceki["Low"]),
            float(onceki["Close"])
        )


        # =================================================
        # 1. ŞART - ICHIMOKU BASE LINE AL SİNYALİ
        #
        # Fiyat Base Line'ı aşağıdan yukarı kesmeli.
        #
        # Önceki gün:
        # Fiyat Base Line'ın altında/eşit
        #
        # Bugün:
        # Fiyat Base Line'ın üzerinde
        # =================================================

        ichimoku_sinyal = (
            onceki["Close"]
            <=
            onceki["BASE"]
            and
            son["Close"]
            >
            son["BASE"]
        )


        # =================================================
        # 2. ŞART
        #
        # Fiyat EMA14'ün en az %3 üzerinde
        # =================================================

        ema_sinyal = (
            son["Close"]
            >=
            son["EMA14"] * 1.03
        )


        # =================================================
        # 3. ŞART
        #
        # RSI > 50
        # =================================================

        rsi_sinyal = (
            son["RSI14"] > 50
        )


        # =================================================
        # TÜM ŞARTLAR
        # =================================================

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

                "daily_change": float(
                    gunluk_degisim
                ),

                "weekly_change": float(
                    bir_haftalik_degisim
                ),

                "volume": hacim,

                "stop": float(
                    pivot["stop"]
                ),

                "k1": float(
                    pivot["k1"]
                ),

                "k2": float(
                    pivot["k2"]
                ),

                "k3": float(
                    pivot["k3"]
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
    # PİYASA SAATİ
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

    bist100 = bist100_listesi()


    print(
        "BIST 100 hisse sayisi:",
        len(bist100)
    )


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

            if symbol not in gonderilenler:

                bulunan.append(
                    sonuc
                )

                gonderilenler.add(
                    symbol
                )


    # -----------------------------------------------------
    # KAYDET
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

        gunluk_isaret = (
            "🟢"
            if sonuc["daily_change"] >= 0
            else "🔴"
        )


        hafta_isaret = (
            "🟢"
            if sonuc["weekly_change"] >= 0
            else "🔴"
        )


        mesaj = (

            "🚨 YENİ HİSSE\n\n"

            f"📈 {sonuc['symbol']}\n"

            f"🕒 {now.strftime('%H:%M')}\n"

            f"💰 Giriş: "
            f"{sonuc['price']:.2f} TL\n"

            f"{gunluk_isaret} Günlük: "
            f"{sonuc['daily_change']:+.2f}%\n"

            f"{hafta_isaret} 1 Hafta: "
            f"{sonuc['weekly_change']:+.2f}%\n\n"

            "🏷️ Pazar: BIST 100\n\n"

            f"📊 Hacim: "
            f"{sonuc['volume']:,.0f}\n\n"

            f"🛑 Stop: "
            f"{sonuc['stop']:.2f} TL\n\n"

            "🎯 Kâr Al:\n"

            f"K1: {sonuc['k1']:.2f} TL\n"

            f"K2: {sonuc['k2']:.2f} TL\n"

            f"K3: {sonuc['k3']:.2f} TL\n\n"

            "📌 Ichimoku Base Line yukarı kesişimi.\n"

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
