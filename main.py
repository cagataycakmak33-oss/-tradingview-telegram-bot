import os
import requests
import borsapy as bp
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed


# =========================================================
# AYARLAR
# =========================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GONDERILEN_DOSYA = "gonderilen_hisseler.txt"

EMA_PERIOD = 14
RSI_PERIOD = 14
BASE_PERIOD = 26

# Aynı anda taranacak hisse sayısı
MAX_WORKERS = 12


# =========================================================
# ANA PAZAR
# =========================================================

ANA_PAZAR = {
    "A1YEN", "CATES", "FRIGO", "LKMNH", "PRKAB",
    "ACSEL", "CELHA", "FRMPL", "LUKSK", "PRKME",
    "ADEL", "CEMAS", "GARFA", "LXGYO", "PRZMA",
    "ADESE", "CEMTS", "GEDZA", "LYDYE", "PSDTC",
    "AFYON", "CEOEM", "GENKM", "MAALT", "RAYSG",
    "AHSGY", "CMBTN", "GEREL", "MACKO", "RTALB",
    "AKENR", "CONSE", "GLRYH", "MAKIM", "RUBNS",
    "AKHAN", "CRFSA", "GOODY", "MAKTK", "RUZYE",
    "AKMGY", "CUSAN", "GSDDE", "MANAS", "SANFM",
    "AKSUE", "DAGI", "GSDHO", "MARBL", "SANKO",
    "ALCAR", "DARDL", "GUNDG", "MARKA", "SAYAS",
    "ALCTL", "DCTTR", "GZNMI", "MARMR", "SEGMN",
    "ALKA", "DENGE", "HATEK", "MARTI", "SEGYO",
    "ALKIM", "DERHL", "HDFGS", "MCARD", "SELVA",
    "ALKLC", "DERIM", "HEDEF", "MEDTR", "SERNT",
    "ALVES", "DESA", "HKTM", "MEKAG", "SKTAS",
    "ANELE", "DESPC", "HOROZ", "MERCN", "SKYMD",
    "ANGEN", "DGATE", "HUNER", "MERCN", "SMART",
    "ARENA", "DGNMO", "HURGZ", "METRO", "SMRVA",
    "ARFYE", "DITAS", "ICBCT", "MEYSU", "SNICA",
    "ARSAN", "DMRGD", "ICUGS", "IHAAS", "MHRGY",
    "ARTMS", "DMSAS", "IHAAS", "MNDRS", "SVGYO",
    "ARZUM", "DNISI", "IHGZT", "MNDTR", "TATGD",
    "AVGYO", "DOCO", "IHLGM", "MRGYO", "TBORG",
    "AVHOL", "DOFER", "IMASM", "MRSHL", "TEHOL",
    "AVOD", "DOKTA", "INFO", "MSGYO", "TEKTU",
    "AYCES", "DUNYH", "INGRM", "MTRKS", "TERA",
    "AYEN", "DURDO", "INTEM", "NETAS", "TGSAS",
    "AZTEK", "DURKN", "ISGSY", "NIBAS", "TKNSA",
    "BAGFS", "DYOBY", "DZGYO", "ISYAT", "OBASE",
    "BAHKM", "EDATA", "IZFAS", "OFSYM", "TSGYO",
    "BAKAB", "EDIP", "IZINV", "ONCSM", "TUCLK",
    "BANVT", "EGEGY", "IZMDC", "ONRYT", "TURGG",
    "BAYRK", "EGEPO", "JANTS", "OSMEN", "UFUK",
    "BEGYO", "EGSER", "KAPLM", "OSTIM", "ULUFA",
    "BESTE", "EKOS", "KARTN", "OTTO", "ULUSE",
    "BEYAZ", "EKSUN", "KFEIN", "OZGYO", "ULUUN",
    "BIGCH", "ELITE", "KGYO", "OZSUB", "UNLU",
    "BIGTK", "EMKEL", "KIMMR", "OZYSR", "VBTYZ",
    "BIZIM", "EMPAE", "KLMSN", "PAMEL", "VERTU",
    "BLCYT", "ENSRI", "KLSYN", "PCILT", "VERUS",
    "BLUME", "EPLAS", "KNFRT", "PEKGY", "VKING",
    "BMSCH", "ERBOS", "KONKA", "PENGD", "VRGYO",
    "BMSTL", "ERCB", "KRONT", "PETUN", "YAPRK",
    "BNTAS", "ESCOM", "KRPLS", "PINSU", "YAYLA",
    "BORSK", "ETILR", "KRSTL", "PKART", "YESIL",
    "BRKVY", "EYGYO", "KRVGD", "PKENT", "YIGIT",
    "BRLSM", "FADE", "KTSKR", "PLTUR", "YKSLN",
    "BULGS", "FMIZP", "KUTPO", "PNLSN", "YUNSA",
    "BURCE", "FONET", "PRDGS", "ZGYO",
    "FORTE", "LIDFA"
}


# =========================================================
# TELEGRAM
# =========================================================

def telegram_gonder(mesaj):

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

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
# PİVOT
# K1 - K2 - K3 İÇİN KULLANILIYOR
# STOP ARTIK PİVOT DEĞİL
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

    return {
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

        ticker = bp.Ticker(symbol)

        df = ticker.history(
            period="6mo"
        )

        if df is None:
            return None

        if len(df) < 60:
            return None

        df = df.copy()

        # =================================================
        # EMA 14
        # =================================================

        df["EMA14"] = (
            df["Close"]
            .ewm(
                span=EMA_PERIOD,
                adjust=False
            )
            .mean()
        )

        # =================================================
        # RSI 14
        # =================================================

        df["RSI14"] = rsi_hesapla(
            df["Close"]
        )

        # =================================================
        # ICHIMOKU BASE LINE
        # 9,26,52,26
        # Base Line = 26
        # =================================================

        base_yuksek = (
            df["High"]
            .rolling(
                BASE_PERIOD
            )
            .max()
        )

        base_dusuk = (
            df["Low"]
            .rolling(
                BASE_PERIOD
            )
            .min()
        )

        df["BASE"] = (
            base_yuksek
            + base_dusuk
        ) / 2

        # =================================================
        # SON 2 GÜN
        # =================================================

        onceki = df.iloc[-2]
        son = df.iloc[-1]

        # =================================================
        # 1 HAFTA
        # =================================================

        hafta_once = df.iloc[-6]

        bir_haftalik_degisim = (
            (
                son["Close"]
                / hafta_once["Close"]
            ) - 1
        ) * 100

        # =================================================
        # GÜNLÜK
        # =================================================

        gunluk_degisim = (
            (
                son["Close"]
                / onceki["Close"]
            ) - 1
        ) * 100

        # =================================================
        # HACİM
        # =================================================

        hacim = float(
            son["Volume"]
        )

        # =================================================
        # KÂR AL SEVİYELERİ
        # =================================================

        pivot = pivot_hesapla(
            float(onceki["High"]),
            float(onceki["Low"]),
            float(onceki["Close"])
        )

        # =================================================
        # ICHIMOKU SİNYALİ
        #
        # Önceki mum:
        # Base >= Fiyat
        #
        # Son mum:
        # Base < Fiyat
        # =================================================

        ichimoku_sinyal = (

            onceki["BASE"]
            >=
            onceki["Close"]

            and

            son["BASE"]
            <
            son["Close"]
        )

        # =================================================
        # EMA SİNYALİ
        #
        # Fiyat EMA14'ten %3 veya daha fazla yukarıda
        # =================================================

        ema_sinyal = (

            son["Close"]
            >=
            son["EMA14"] * 1.03
        )

        # =================================================
        # RSI SİNYALİ
        #
        # RSI14 >= 50
        # =================================================

        rsi_sinyal = (

            son["RSI14"]
            >=
            50
        )

        # =================================================
        # TÜM ŞARTLAR
        # =================================================

        if (
            ichimoku_sinyal
            and
            ema_sinyal
            and
            rsi_sinyal
        ):

            print(
                "🚨 SİNYAL:",
                symbol
            )

            # =================================================
            # STOP = EMA 14
            # =================================================

            stop_ema14 = float(
                son["EMA14"]
            )

            return {

                "symbol": symbol,

                "price": float(
                    son["Close"]
                ),

                "ema14": stop_ema14,

                "daily_change": float(
                    gunluk_degisim
                ),

                "weekly_change": float(
                    bir_haftalik_degisim
                ),

                "volume": hacim,

                "stop": stop_ema14,

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
    print("====================================")
    print("TRADING BOT BASLADI")
    print("====================================")

    now = datetime.now(
        ZoneInfo("Europe/Istanbul")
    )

    print(
        "Saat:",
        now.strftime(
            "%d.%m.%Y %H:%M"
        )
    )

    # =====================================================
    # PİYASA SAATİ
    # =====================================================

    if not piyasa_acik_mi():

        print(
            "Piyasa saati disinda."
        )

        print(
            "Tarama yapilmayacak."
        )

        return

    # =====================================================
    # BIST 100
    # =====================================================

    print(
        "BIST 100 listesi aliniyor..."
    )

    bist100 = bist100_listesi()

    # =====================================================
    # BIST 100 + ANA PAZAR
    # =====================================================

    tarama_listesi = sorted(
        bist100 | ANA_PAZAR
    )

    print(
        "BIST 100 hisse sayisi:",
        len(bist100)
    )

    print(
        "Ana Pazar hisse sayisi:",
        len(ANA_PAZAR)
    )

    print(
        "Toplam benzersiz taranacak hisse:",
        len(tarama_listesi)
    )

    # =====================================================
    # TARAMA BAŞLANGIÇ ZAMANI
    # =====================================================

    baslangic_zamani = datetime.now(
        ZoneInfo("Europe/Istanbul")
    )

    # =====================================================
    # GÖNDERİLENLER
    # =====================================================

    gonderilenler = (
        gonderilenleri_oku()
    )

    bulunan = []

    # =====================================================
    # HIZLI PARALEL TARAMA
    # =====================================================

    print(
        ""
    )

    print(
        f"⚡ Hızlı tarama başlıyor..."
    )

    print(
        f"⚡ Aynı anda {MAX_WORKERS} hisse taranacak."
    )

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        gelecekler = {
            executor.submit(
                analiz_et,
                symbol
            ): symbol
            for symbol in tarama_listesi
        }

        for gelecek in as_completed(
            gelecekler
        ):

            symbol = gelecekler[
                gelecek
            ]

            try:

                sonuc = gelecek.result()

                if sonuc:

                    if (
                        symbol
                        not in gonderilenler
                    ):

                        bulunan.append(
                            sonuc
                        )

                        gonderilenler.add(
                            symbol
                        )

            except Exception as hata:

                print(
                    symbol,
                    "PARALEL TARAMA HATASI:",
                    type(hata)._name_,
                    str(hata)
                )

    # =====================================================
    # TARAMA SÜRESİ
    # =====================================================

    bitis_zamani = datetime.now(
        ZoneInfo("Europe/Istanbul")
    )

    sure = (
        bitis_zamani
        - baslangic_zamani
    ).total_seconds()

    print(
        ""
    )

    print(
        f"⏱️ Tarama süresi: {sure:.1f} saniye"
    )

    # =====================================================
    # KAYDET
    # =====================================================

    gonderilenleri_kaydet(
        gonderilenler
    )

    # =====================================================
    # SONUÇ
    # =====================================================

    print("")
    print("====================================")
    print("TARAMA TAMAMLANDI")
    print("====================================")

    print(
        "Yeni bulunan hisse:",
        len(bulunan)
    )

    # =====================================================
    # TELEGRAM
    # =====================================================

    for sonuc in bulunan:

        symbol = sonuc["symbol"]

        if symbol in bist100:

            pazar_adi = "BIST 100"

        elif symbol in ANA_PAZAR:

            pazar_adi = "Ana Pazar"

        else:

            pazar_adi = "Bilinmiyor"

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

        # =================================================
        # FİYAT
        # =================================================

        fiyat = sonuc["price"]

        # =================================================
        # STOP = EMA14
        # =================================================

        stop_yuzde = (
            (
                sonuc["stop"]
                - fiyat
            )
            / fiyat
        ) * 100

        # =================================================
        # KÂR AL YÜZDELERİ
        # =================================================

        k1_yuzde = (
            (
                sonuc["k1"]
                - fiyat
            )
            / fiyat
        ) * 100

        k2_yuzde = (
            (
                sonuc["k2"]
                - fiyat
            )
            / fiyat
        ) * 100

        k3_yuzde = (
            (
                sonuc["k3"]
                - fiyat
            )
            / fiyat
        ) * 100

        # =================================================
        # TELEGRAM MESAJI
        # =================================================

        mesaj = (

            "🚨 YENİ HİSSE\n\n"

            f"📈 {symbol}\n"

            f"🕒 {now.strftime('%H:%M')}\n"

            f"💰 Giriş: "
            f"{fiyat:.2f} TL\n"

            f"{gunluk_isaret} Günlük: "
            f"{sonuc['daily_change']:+.2f}%\n"

            f"{hafta_isaret} 1 Hafta: "
            f"{sonuc['weekly_change']:+.2f}%\n\n"

            f"🏷️ Pazar: {pazar_adi}\n\n"

            f"📊 Hacim: "
            f"{sonuc['volume']:,.0f}\n\n"

            f"🛑 Stop EMA14: "
            f"{sonuc['stop']:.2f} TL "
            f"→ {stop_yuzde:+.2f}%\n\n"

            "🎯 Kâr Al:\n"

            f"K1: {sonuc['k1']:.2f} TL "
            f"→ {k1_yuzde:+.2f}%\n"

            f"K2: {sonuc['k2']:.2f} TL "
            f"→ {k2_yuzde:+.2f}%\n"

            f"K3: {sonuc['k3']:.2f} TL "
            f"→ {k3_yuzde:+.2f}%\n\n"

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
