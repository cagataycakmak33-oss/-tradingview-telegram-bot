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
ADX_PERIOD = 14

# Fibonacci indikatöründeki lookback
FIB_LOOKBACK = 100

# 20 günlük ortalama hacim
VOLUME_AVG_PERIOD = 20

MAX_WORKERS = 4
MAX_RETRIES = 3

ISTANBUL = ZoneInfo("Europe/Istanbul")


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
    "ARTMS", "DMSAS", "ICUGS", "MNDRS", "SVGYO",
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
    "BNTAS", "ESCOM", "KRPLS", "PETUN", "YIGIT",
    "BORSK", "ETILR", "KRSTL", "PINSU", "YAYLA",
    "BRKVY", "EYGYO", "KRVGD", "PKENT", "YESIL",
    "BRLSM", "FADE", "KTSKR", "PLTUR", "YKSLN",
    "BULGS", "FMIZP", "KUTPO", "PNLSN", "PNSUT",
    "BURCE", "FONET", "KZGYO", "ZEDUR",
    "BVSAN", "FORMT", "PRDGS", "ZGYO",
    "FORTE", "LIDFA"
}


# =========================================================
# GÖNDERİLENLERİ OKU
# =========================================================

def gonderilenleri_oku():

    bugun = datetime.now(
        ISTANBUL
    ).strftime("%Y-%m-%d")

    if not os.path.exists(
        GONDERILEN_DOSYA
    ):
        return set()

    try:

        kayitlar = set()

        with open(
            GONDERILEN_DOSYA,
            "r",
            encoding="utf-8"
        ) as dosya:

            for satir in dosya:

                satir = satir.strip()

                if not satir:
                    continue

                parcalar = satir.split("|")

                if len(parcalar) == 2:

                    tarih, hisse = parcalar

                    if tarih == bugun:
                        kayitlar.add(
                            hisse.upper()
                        )

        return kayitlar

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

def gonderilenleri_kaydet(
    hisseler
):

    bugun = datetime.now(
        ISTANBUL
    ).strftime("%Y-%m-%d")

    try:

        mevcut = []

        if os.path.exists(
            GONDERILEN_DOSYA
        ):

            with open(
                GONDERILEN_DOSYA,
                "r",
                encoding="utf-8"
            ) as dosya:

                for satir in dosya:

                    satir = satir.strip()

                    if satir:
                        mevcut.append(
                            satir
                        )

        bugunku = {
            satir
            for satir in mevcut
            if satir.startswith(
                bugun + "|"
            )
        }

        for hisse in hisseler:

            bugunku.add(
                f"{bugun}|{hisse.upper()}"
            )

        eski = [
            satir
            for satir in mevcut
            if not satir.startswith(
                bugun + "|"
            )
        ]

        with open(
            GONDERILEN_DOSYA,
            "w",
            encoding="utf-8"
        ) as dosya:

            for satir in sorted(
                eski + list(bugunku)
            ):

                dosya.write(
                    satir + "\n"
                )

        print(
            "Kayıt dosyası güncellendi."
        )

        print(
            "Bugün gönderilen:",
            sorted(hisseler)
        )

    except Exception as hata:

        print(
            "Gönderilenler kaydedilemedi:",
            type(hata)._name_,
            str(hata)
        )


# =========================================================
# TELEGRAM
# =========================================================

def telegram_gonder(
    mesaj
):

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
# PİYASA SAATİ
# =========================================================

def piyasa_acik_mi():

    now = datetime.now(
        ISTANBUL
    )

    if now.weekday() >= 5:
        return False

    dakika = (
        now.hour * 60
        + now.minute
    )

    return (
        9 * 60 + 40
        <= dakika
        <= 18 * 60 + 10
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
            for hisse in
            index.component_symbols
        }

    except Exception as hata:

        print(
            "BIST 100 HATA:",
            type(hata)._name_,
            str(hata)
        )

        return set()


# =========================================================
# RSI
# =========================================================

def rsi_hesapla(
    close
):

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
# ADX
# =========================================================

def adx_hesapla(
    df
):

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    onceki_close = close.shift(
        1
    )

    yukari_hareket = high.diff()

    asagi_hareket = -low.diff()

    plus_dm = yukari_hareket.where(
        (
            yukari_hareket
            > asagi_hareket
        )
        &
        (
            yukari_hareket > 0
        ),
        0.0
    )

    minus_dm = asagi_hareket.where(
        (
            asagi_hareket
            > yukari_hareket
        )
        &
        (
            asagi_hareket > 0
        ),
        0.0
    )

    tr1 = high - low

    tr2 = (
        high
        - onceki_close
    ).abs()

    tr3 = (
        low
        - onceki_close
    ).abs()

    true_range = tr1.combine(
        tr2,
        max
    ).combine(
        tr3,
        max
    )

    atr = true_range.ewm(
        alpha=1 / ADX_PERIOD,
        adjust=False
    ).mean()

    plus_di = (
        100
        * plus_dm.ewm(
            alpha=1 / ADX_PERIOD,
            adjust=False
        ).mean()
        / atr
    )

    minus_di = (
        100
        * minus_dm.ewm(
            alpha=1 / ADX_PERIOD,
            adjust=False
        ).mean()
        / atr
    )

    di_toplam = (
        plus_di
        + minus_di
    )

    dx = (
        100
        * (
            plus_di
            - minus_di
        ).abs()
        / di_toplam
    )

    adx = dx.ewm(
        alpha=1 / ADX_PERIOD,
        adjust=False
    ).mean()

    return adx


# =========================================================
# ADX GÖSTERGE
# =========================================================

def adx_gosterge(
    adx
):

    if adx >= 25:
        return "🟢"

    if adx >= 20:
        return "🟡"

    return "🔴"


# =========================================================
# VERİ AL
# =========================================================

def veri_al(
    symbol
):

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

            if len(df) < 120:
                return None

            return df.copy()

        except Exception as hata:

            hata_metni = str(
                hata
            )

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
                    f"{bekleme} sn bekleniyor"
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

    return None


# =========================================================
# FIBONACCI
#
# TradingView'daki gönderdiğin indikatörün mantığı:
#
# Fhigh = son 100 mumun en yüksek High değeri
# Flow  = son 100 mumun en düşük Low değeri
#
# highestbars / lowestbars mantığıyla:
#
# Eğer dip daha eskiyse:
#     0 = tepe
#     1 = dip
#
# Eğer tepe daha eskiyse:
#     0 = dip
#     1 = tepe
#
# Böylece Fib yönü otomatik belirlenir.
# =========================================================

def fibonacci_hesapla(
    df,
    fiyat
):

    fib_df = df.tail(
        FIB_LOOKBACK
    ).copy()

    if len(fib_df) < FIB_LOOKBACK:
        return None

    high = fib_df["High"].astype(
        float
    )

    low = fib_df["Low"].astype(
        float
    )

    # -----------------------------------------------------
    # Son 100 mumdaki ekstrem değerler
    # -----------------------------------------------------

    fhigh = float(
        high.max()
    )

    flow = float(
        low.min()
    )

    # -----------------------------------------------------
    # En yüksek ve en düşük değerlerin
    # 100 mum içindeki konumları
    #
    # TradingView highestbars / lowestbars:
    # mevcut mum = 0
    # geçmişe gittikçe negatif
    # -----------------------------------------------------

    high_position = (
        len(fib_df)
        - 1
        - high.values.argmax()
    )

    low_position = (
        len(fib_df)
        - 1
        - low.values.argmin()
    )

    # TradingView:
    #
    # revfibs = FL > FH
    #
    # Yani düşük değer daha yakın zamanda
    # oluşmuşsa Fib yönü tersine döner.

    revfibs = (
        low_position
        > high_position
    )

    # -----------------------------------------------------
    # Fib değerlerini TradingView mantığıyla hesapla
    # -----------------------------------------------------

    def fib_x(n):

        if revfibs:

            return (
                (fhigh - flow) * n
                + flow
            )

        else:

            return (
                fhigh
                - (
                    (fhigh - flow)
                    * n
                )
            )

    fib_oranlari = [
        0.000,
        0.236,
        0.382,
        0.500,
        0.618,
        0.786,
        1.000
    ]

    seviyeler = []

    for oran in fib_oranlari:

        seviye = float(
            fib_x(oran)
        )

        seviyeler.append({
            "fib": oran,
            "price": seviye
        })

    # -----------------------------------------------------
    # Fiyatın altındaki Fib seviyeleri
    # S1 = fiyata en yakın destek
    # -----------------------------------------------------

    destekler = [
        seviye
        for seviye in seviyeler
        if seviye["price"] < fiyat
    ]

    destekler.sort(
        key=lambda x: x["price"],
        reverse=True
    )

    # -----------------------------------------------------
    # Fiyatın üstündeki Fib seviyeleri
    # K1 = fiyata en yakın direnç
    # -----------------------------------------------------

    direncler = [
        seviye
        for seviye in seviyeler
        if seviye["price"] > fiyat
    ]

    direncler.sort(
        key=lambda x: x["price"]
    )

    return {
        "high": fhigh,
        "low": flow,
        "revfibs": revfibs,
        "supports": destekler,
        "resistances": direncler
    }


# =========================================================
# YÜZDE MESAFE
# =========================================================

def yuzde_mesafe(
    seviye,
    fiyat
):

    if seviye is None:
        return None

    return (
        (
            seviye
            - fiyat
        )
        / fiyat
    ) * 100


# =========================================================
# SİNYAL GÜCÜ
#
# 100 puan üzerinden:
#
# BASE yukarı kesişimi       = 30
# Fiyat EMA14 +%3 veya üstü = 20
# EMA14 yükseliyor           = 15
# RSI > 50                   = 15
# RSI yükseliyor             = 10
# Hacim / 20G ort.           = 10
#
# Hacim puana katkı sağlar
# ancak filtre değildir.
# =========================================================

def sinyal_gucu_hesapla(
    df,
    son,
    onceki,
    hacim,
    ortalama_hacim
):

    puan = 0

    # BASE yukarı kesildi
    base_cross = (
        onceki["BASE"]
        >= onceki["Close"]
        and
        son["BASE"]
        < son["Close"]
    )

    if base_cross:
        puan += 30

    # Fiyat EMA14 üzerinde
    ema_orani = (
        son["Close"]
        / son["EMA14"]
    )

    if ema_orani >= 1.03:

        puan += 20

    elif ema_orani >= 1.02:

        puan += 15

    elif ema_orani >= 1.01:

        puan += 10

    # EMA yükseliyor
    if (
        son["EMA14"]
        > onceki["EMA14"]
    ):

        puan += 15

    # RSI > 50
    if son["RSI14"] > 50:

        puan += 15

    # RSI yükseliyor
    if (
        son["RSI14"]
        > onceki["RSI14"]
    ):

        puan += 10

    # -----------------------------------------------------
    # Hacim puanı
    #
    # Filtre DEĞİL.
    # Sadece sinyal gücüne katkı verir.
    # -----------------------------------------------------

    if (
        ortalama_hacim > 0
    ):

        hacim_orani = (
            hacim
            / ortalama_hacim
        )

        if hacim_orani >= 2.0:

            puan += 10

        elif hacim_orani >= 1.5:

            puan += 8

        elif hacim_orani >= 1.2:

            puan += 6

        elif hacim_orani >= 1.0:

            puan += 4

        elif hacim_orani >= 0.8:

            puan += 2

    return min(
        puan,
        100
    )


# =========================================================
# ANALİZ
# =========================================================

def analiz_et(
    symbol
):

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
            return None

        # -------------------------------------------------
        # EMA14
        # -------------------------------------------------

        df["EMA14"] = (
            df["Close"].ewm(
                span=EMA_PERIOD,
                adjust=False
            ).mean()
        )

        # -------------------------------------------------
        # RSI14
        # -------------------------------------------------

        df["RSI14"] = (
            rsi_hesapla(
                df["Close"]
            )
        )

        # -------------------------------------------------
        # ADX14
        # -------------------------------------------------

        df["ADX14"] = (
            adx_hesapla(
                df
            )
        )

        # -------------------------------------------------
        # ICHIMOKU BASE
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Son veriler
        # -------------------------------------------------

        onceki = df.iloc[
            -2
        ]

        son = df.iloc[
            -1
        ]

        hafta_once = df.iloc[
            -6
        ]

        # -------------------------------------------------
        # Haftalık değişim
        # -------------------------------------------------

        bir_haftalik_degisim = (
            (
                son["Close"]
                / hafta_once["Close"]
            )
            - 1
        ) * 100

        # -------------------------------------------------
        # Günlük değişim
        # -------------------------------------------------

        gunluk_degisim = (
            (
                son["Close"]
                / onceki["Close"]
            )
            - 1
        ) * 100

        # -------------------------------------------------
        # Hacim
        # -------------------------------------------------

        try:

            hacim = float(
                son["Volume"]
            )

        except Exception:

            hacim = 0.0

        # -------------------------------------------------
        # 20 GÜNLÜK ORTALAMA HACİM
        #
        # Son gün dahil.
        # Sadece gösterge ve sinyal gücü için.
        # Filtre değil.
        # -------------------------------------------------

        try:

            ortalama_hacim = float(
                df["Volume"]
                .tail(
                    VOLUME_AVG_PERIOD
                )
                .mean()
            )

        except Exception:

            ortalama_hacim = 0.0

        if (
            ortalama_hacim > 0
        ):

            hacim_orani = (
                hacim
                / ortalama_hacim
            )

        else:

            hacim_orani = 0.0

        # -------------------------------------------------
        # ADX
        # -------------------------------------------------

        try:

            adx = float(
                son["ADX14"]
            )

        except Exception:

            adx = 0.0

        # =================================================
        # TARAMA ŞARTLARI
        # =================================================

        # 1 - BASE yukarı kesildi
        ichimoku_sinyal = (
            onceki["BASE"]
            >= onceki["Close"]
            and
            son["BASE"]
            < son["Close"]
        )

        # 2 - Fiyat EMA14 üzerinde en az %3
        fiyat_ema_sinyal = (
            son["Close"]
            >= son["EMA14"] * 1.03
        )

        # 3 - EMA14 yükseliyor
        ema_yukseliyor = (
            son["EMA14"]
            > onceki["EMA14"]
        )

        # 4 - RSI > 50
        rsi_50_ustu = (
            son["RSI14"]
            > 50
        )

        # 5 - RSI yükseliyor
        rsi_yukseliyor = (
            son["RSI14"]
            > onceki["RSI14"]
        )

        # -------------------------------------------------
        # TÜM ŞARTLAR AYNI ANDA SAĞLANMALI
        #
        # Hacim burada filtre değil.
        # -------------------------------------------------

        if not (
            ichimoku_sinyal
            and
            fiyat_ema_sinyal
            and
            ema_yukseliyor
            and
            rsi_50_ustu
            and
            rsi_yukseliyor
        ):

            return None

        fiyat = float(
            son["Close"]
        )

        # =================================================
        # FIBONACCI
        # =================================================

        fibonacci = fibonacci_hesapla(
            df,
            fiyat
        )

        if fibonacci is None:
            return None

        destekler = (
            fibonacci["supports"]
        )

        direncler = (
            fibonacci["resistances"]
        )

        # -------------------------------------------------
        # En az bir destek ve bir direnç
        # -------------------------------------------------

        if not destekler:

            print(
                f"{symbol}: "
                "Fib destek bulunamadı."
            )

            return None

        if not direncler:

            print(
                f"{symbol}: "
                "Fib direnç bulunamadı."
            )

            return None

        # =================================================
        # SİNYAL GÜCÜ
        # =================================================

        sinyal_gucu = sinyal_gucu_hesapla(
            df,
            son,
            onceki,
            hacim,
            ortalama_hacim
        )

        # =================================================
        # S1
        # =================================================

        s1 = destekler[0]["price"]

        # -------------------------------------------------
        # STOP
        #
        # S1'in %0.5 altında.
        # -------------------------------------------------

        stop = (
            s1 * 0.995
        )

        # =================================================
        # SONUÇ
        # =================================================

        return {
            "symbol": symbol,

            "price": fiyat,

            "daily_change": float(
                gunluk_degisim
            ),

            "weekly_change": float(
                bir_haftalik_degisim
            ),

            "volume": hacim,

            "volume_avg20": float(
                ortalama_hacim
            ),

            "volume_ratio": float(
                hacim_orani
            ),

            "ema14": float(
                son["EMA14"]
            ),

            "rsi14": float(
                son["RSI14"]
            ),

            "adx14": adx,

            "s1": float(
                s1
            ),

            "stop": float(
                stop
            ),

            "supports": destekler,

            "resistances": direncler,

            "fib_high": float(
                fibonacci["high"]
            ),

            "fib_low": float(
                fibonacci["low"]
            ),

            "fib_reverse": bool(
                fibonacci["revfibs"]
            ),

            "signal_strength": int(
                sinyal_gucu
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
        ISTANBUL
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

        return

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

    gonderilenler = (
        gonderilenleri_oku()
    )

    print(
        "Bugün daha önce gönderilen:",
        len(gonderilenler)
    )

    bulunan = []

    tamamlanan = 0

    baslangic_zamani = (
        datetime.now(
            ISTANBUL
        )
    )

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

            for symbol
            in tarama_listesi
        }

        for gelecek in as_completed(
            gelecekler
        ):

            symbol = (
                gelecekler[
                    gelecek
                ]
            )

            try:

                sonuc = (
                    gelecek.result()
                )

                tamamlanan += 1

                if sonuc:

                    if (
                        symbol
                        in gonderilenler
                    ):

                        print(
                            f"⏭️ {symbol} "
                            f"bugün zaten gönderildi."
                        )

                    else:

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

            if tamamlanan % 25 == 0:

                print(
                    f"İlerleme: "
                    f"{tamamlanan}/"
                    f"{len(tarama_listesi)}"
                )

    bitis_zamani = (
        datetime.now(
            ISTANBUL
        )
    )

    sure = (
        bitis_zamani
        - baslangic_zamani
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
        f"{saniye} saniye"
    )

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

    basariyla_gonderilenler = set()

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

        # -------------------------------------------------
        # ADX
        # -------------------------------------------------

        adx_deger = (
            sonuc["adx14"]
        )

        adx_isaret = (
            adx_gosterge(
                adx_deger
            )
        )

        # -------------------------------------------------
        # Günlük / Haftalık
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Değerler
        # -------------------------------------------------

        fiyat = (
            sonuc["price"]
        )

        stop = (
            sonuc["stop"]
        )

        s1 = (
            sonuc["s1"]
        )

        stop_yuzde = (
            yuzde_mesafe(
                stop,
                fiyat
            )
        )

        sinyal_gucu = (
            sonuc["signal_strength"]
        )

        hacim = (
            sonuc["volume"]
        )

        ortalama_hacim = (
            sonuc["volume_avg20"]
        )

        hacim_orani = (
            sonuc["volume_ratio"]
        )

        # =================================================
        # TELEGRAM MESAJ BAŞLANGICI
        # =================================================

        mesaj = (
            f"🟢 YENİ : {symbol}"
            f"                    "
            f"ADX {adx_isaret} "
            f"{adx_deger:.1f}\n"

            f"⭐ Sinyal Gücü: "
            f"{sinyal_gucu}/100\n\n"

            f"💰 Giriş: "
            f"{fiyat:.2f} TL\n"

            f"{gunluk_isaret} Günlük: "
            f"{sonuc['daily_change']:+.2f}%\n"

            f"{hafta_isaret} 1 Hafta: "
            f"{sonuc['weekly_change']:+.2f}%\n"

            f"📏 EMA14: "
            f"{sonuc['ema14']:.2f} TL\n"

            f"📊 RSI: "
            f"{sonuc['rsi14']:.1f}\n\n"

            f"🔊 Hacim: "
            f"{hacim:,.0f}\n"

            f"📊 20G Ort. Hacim: "
            f"{ortalama_hacim:,.0f}\n"

            f"📈 Hacim/Ort.: "
            f"{hacim_orani:.2f}x\n\n"

            f"🛑 DESTEKLER\n"
        )

        # =================================================
        # TÜM DESTEKLER
        # =================================================

        destekler = (
            sonuc["supports"]
        )

        for index, destek in enumerate(
            destekler,
            start=1
        ):

            destek_fiyat = (
                destek["price"]
            )

            fib_orani = (
                destek["fib"]
            )

            mesafe = (
                yuzde_mesafe(
                    destek_fiyat,
                    fiyat
                )
            )

            mesaj += (
                f"S{index}: "
                f"{destek_fiyat:.2f} TL "
                f"— Fib {fib_orani:.3f} "
                f"→ {mesafe:+.2f}%\n"
            )

        # =================================================
        # STOP
        # =================================================

        mesaj += (
            f"\n🛑 STOP\n"
            f"{stop:.2f} TL "
            f"→ {stop_yuzde:+.2f}%\n\n"
        )

        # =================================================
        # TÜM DİRENÇLER
        # =================================================

        mesaj += (
            "🎯 HEDEFLER\n"
        )

        direncler = (
            sonuc["resistances"]
        )

        for index, direnç in enumerate(
            direncler,
            start=1
        ):

            direnç_fiyat = (
                direnç["price"]
            )

            fib_orani = (
                direnç["fib"]
            )

            mesafe = (
                yuzde_mesafe(
                    direnç_fiyat,
                    fiyat
                )
            )

            mesaj += (
                f"K{index}: "
                f"{direnç_fiyat:.2f} TL "
                f"— Fib {fib_orani:.3f} "
                f"→ {mesafe:+.2f}%\n"
            )

        # =================================================
        # FIBO ANA ARALIK
        # =================================================

        mesaj += (
            f"\n📐 100G FIB ARALIĞI\n"
            f"🔻 Dip: "
            f"{sonuc['fib_low']:.2f} TL\n"
            f"🔺 Tepe: "
            f"{sonuc['fib_high']:.2f} TL"
        )

        # =================================================
        # TELEGRAM GÖNDER
        # =================================================

        print("")
        print(
            "Telegram gönderiliyor:",
            symbol
        )

        if telegram_gonder(
            mesaj
        ):

            basariyla_gonderilenler.add(
                symbol
            )

    # =====================================================
    # SADECE BAŞARILI GİDENLERİ KAYDET
    # =====================================================

    if basariyla_gonderilenler:

        gonderilenleri_kaydet(
            basariyla_gonderilenler
        )

    else:

        print(
            "Yeni gönderilen hisse yok."
        )


# =========================================================
# BAŞLAT
# =========================================================

if __name__ == "__main__":

    main()
