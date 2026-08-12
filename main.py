import os
import time
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

# 429 almamak için şimdilik 4 paralel
MAX_WORKERS = 4

# 429 tekrar deneme
MAX_RETRIES = 3


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
    "BURCE", "FONET", "KZGYO", "PNSUT", "ZEDUR",
    "BVSAN", "FORMT", "PRDGS", "ZGYO",
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

    try:

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

    except Exception as hata:

        print(
            "Telegram HATA:",
            type(hata)._name_,
            str(hata)
        )

        return False


# =========================================================
# GÖNDERİLENLERİ OKU
# =========================================================

def gonderilenleri_oku():

    if not os.path.exists(
        GONDERILEN_DOSYA
    ):
        return set()

    try:

        with open(
            GONDERILEN_DOSYA,
            "r",
            encoding="utf-8"
        ) as dosya:

            return {
                satir.strip().upper()
                for satir in dosya
                if satir.strip()
            }

    except Exception as hata:

        print(
            "Gönderilenler okunamadı:",
            type(hata)._name_,
            str(hata)
        )

        return set()


# =========================================================
# GÖNDERİLENLERİ KAYDET
# =========================================================

def gonderilenleri_kaydet(hisseler):

    try:

        with open(
            GONDERILEN_DOSYA,
            "w",
            encoding="utf-8"
        ) as dosya:

            for hisse in sorted(hisseler):

                dosya.write(
                    hisse + "\n"
                )

    except Exception as hata:

        print(
            "Gönderilenler kaydedilemedi:",
            type(hata)._name_,
            str(hata)
        )


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

    baslangic = (
        9 * 60
        + 40
    )

    bitis = (
        18 * 60
        + 10
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

    try:

        index = bp.Index(
            "XU100"
        )

        return {
            str(hisse).upper()
            for hisse in index.component_symbols
        }

    except Exception as hata:

        print(
            "BIST 100 HATA:",
            type(hata)._name_,
            str(hata)
        )

        return set()


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

    return (
        100
        - (
            100
            / (1 + rs)
        )
    )


# =========================================================
# VERİ AL
# =========================================================

def veri_al(symbol):

    for deneme in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

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

            return df.copy()

        except Exception as hata:

            hata_metni = str(hata)

            if (
                "429" in hata_metni
                or
                "Too Many Requests"
                in hata_metni
            ):

                bekleme = (
                    2 ** deneme
                )

                print(
                    f"{symbol}: 429 - "
                    f"{bekleme} sn bekleniyor "
                    f"(deneme "
                    f"{deneme}/{MAX_RETRIES})"
                )

                time.sleep(
                    bekleme
                )

                continue

            print(
                symbol,
                "VERİ HATASI:",
                type(hata)._name_,
                str(hata)
            )

            return None

    print(
        symbol,
        "429 nedeniyle atlandı."
    )

    return None


# =========================================================
# HİSSE ANALİZİ
# =========================================================

def analiz_et(symbol):

    try:

        print(
            "Taranıyor:",
            symbol
        )

        df = veri_al(
            symbol
        )

        if df is None:
            return None

        gerekli = {
            "High",
            "Low",
            "Close",
            "Volume"
        }

        if not gerekli.issubset(
            df.columns
        ):

            print(
                symbol,
                "Gerekli veri eksik."
            )

            return None

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
        # ICHIMOKU BASE
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
        # SON İKİ GÜN
        # =================================================

        onceki = df.iloc[-2]
        son = df.iloc[-1]

        # =================================================
        # HAFTALIK DEĞİŞİM
        # =================================================

        hafta_once = df.iloc[-6]

        bir_haftalik_degisim = (
            (
                son["Close"]
                /
                hafta_once["Close"]
            )
            - 1
        ) * 100

        # =================================================
        # GÜNLÜK DEĞİŞİM
        # =================================================

        gunluk_degisim = (
            (
                son["Close"]
                /
                onceki["Close"]
            )
            - 1
        ) * 100

        # =================================================
        # HACİM
        # =================================================

        try:

            hacim = float(
                son["Volume"]
            )

        except Exception:

            hacim = 0.0

        # =================================================
        # ICHIMOKU SİNYALİ
        #
        # Önceki:
        # Base >= Fiyat
        #
        # Son:
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
        # Fiyat EMA14'ün %3 veya daha fazla üzerinde
        # =================================================

        ema_sinyal = (
            son["Close"]
            >=
            son["EMA14"] * 1.03
        )

        # =================================================
        # RSI SİNYALİ
        # =================================================

        rsi_sinyal = (
            son["RSI14"]
            >=
            50
        )

        # =================================================
        # TÜM ŞARTLAR
        # =================================================

        if not (
            ichimoku_sinyal
            and
            ema_sinyal
            and
            rsi_sinyal
        ):

            return None

        print(
            "🚨 SİNYAL:",
            symbol
        )

        # =================================================
        # STOP = EMA14
        # =================================================

        stop = float(
            son["EMA14"]
        )

        # =================================================
        # PİVOT
        # K1 K2 K3
        # =================================================

        high = float(
            onceki["High"]
        )

        low = float(
            onceki["Low"]
        )

        close = float(
            onceki["Close"]
        )

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
            + high
            - low
        )

        r3 = (
            high
            + 2 * (
                pivot
                - low
            )
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

            "ema14": float(
                son["EMA14"]
            ),

            "rsi14": float(
                son["RSI14"]
            ),

            "stop": stop,

            "k1": float(
                r1
            ),

            "k2": float(
                r2
            ),

            "k3": float(
                r3
            )
        }

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

    # =====================================================
    # PİYASA KONTROLÜ
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

    bist100 = (
        bist100_listesi()
    )

    if not bist100:

        print(
            "BIST 100 listesi alınamadı."
        )

        return

    # =====================================================
    # TARAMA LİSTESİ
    # =====================================================

    tarama_listesi = sorted(
        bist100
        |
        ANA_PAZAR
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
    # SÜRE BAŞLANGICI
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

    tamamlanan = 0

    # =====================================================
    # PARALEL TARAMA
    # =====================================================

    print("")
    print(
        "⚡ Hızlı tarama başlıyor..."
    )

    print(
        f"⚡ Aynı anda "
        f"{MAX_WORKERS} hisse taranacak."
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

            symbol = (
                gelecekler[gelecek]
            )

            try:

                sonuc = (
                    gelecek.result()
                )

                tamamlanan += 1

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

                tamamlanan += 1

                print(
                    symbol,
                    "PARALEL HATA:",
                    type(hata)._name_,
                    str(hata)
                )

            if (
                tamamlanan % 25 == 0
            ):

                print(
                    f"İlerleme: "
                    f"{tamamlanan}/"
                    f"{len(tarama_listesi)}"
                )

    # =====================================================
    # SÜRE
    # =====================================================

    bitis_zamani = datetime.now(
        ZoneInfo("Europe/Istanbul")
    )

    sure = (
        bitis_zamani
        -
        baslangic_zamani
    ).total_seconds()

    dakika = int(
        sure // 60
    )

    saniye = int(
        sure % 60
    )

    print("")
    print(
        f"⏱️ Tarama süresi: "
        f"{dakika} dakika "
        f"{saniye} saniye "
        f"({sure:.1f} saniye)"
    )

    # =====================================================
    # GÖNDERİLENLERİ KAYDET
    # =====================================================

    gonderilenleri_kaydet(
        gonderilenler
    )

    # =====================================================
    # SONUÇ
    # =====================================================

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

    # =====================================================
    # TELEGRAM
    # =====================================================

    for sonuc in bulunan:

        symbol = (
            sonuc["symbol"]
        )

        if symbol in bist100:

            pazar_adi = "BIST 100"

        elif symbol in ANA_PAZAR:

            pazar_adi = "Ana Pazar"

        else:

            pazar_adi = "Bilinmiyor"

        # =================================================
        # İŞARETLER
        # =================================================

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

        fiyat = (
            sonuc["price"]
        )

        # =================================================
        # STOP YÜZDESİ
        # =================================================

        stop_yuzde = (
            (
                sonuc["stop"]
                -
                fiyat
            )
            /
            fiyat
        ) * 100

        # =================================================
        # KÂR YÜZDELERİ
        # =================================================

        k1_yuzde = (
            (
                sonuc["k1"]
                -
                fiyat
            )
            /
            fiyat
        ) * 100

        k2_yuzde = (
            (
                sonuc["k2"]
                -
                fiyat
            )
            /
            fiyat
        ) * 100

        k3_yuzde = (
            (
                sonuc["k3"]
                -
                fiyat
            )
            /
            fiyat
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

            f"🏷️ Pazar: "
            f"{pazar_adi}\n\n"

            f"📊 Hacim: "
            f"{sonuc['volume']:,.0f}\n\n"

            f"📉 EMA14: "
            f"{sonuc['ema14']:.2f} TL\n"

            f"📊 RSI14: "
            f"{sonuc['rsi14']:.2f}\n\n"

            f"🛑 Stop (EMA14): "
            f"{sonuc['stop']:.2f} TL "
            f"→ {stop_yuzde:+.2f}%\n\n"

            "🎯 Kâr Al:\n"

            f"K1: "
            f"{sonuc['k1']:.2f} TL "
            f"→ {k1_yuzde:+.2f}%\n"

            f"K2: "
            f"{sonuc['k2']:.2f} TL "
            f"→ {k2_yuzde:+.2f}%\n"

            f"K3: "
            f"{sonuc['k3']:.2f} TL "
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
