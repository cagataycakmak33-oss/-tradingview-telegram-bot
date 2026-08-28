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

FIB_LOOKBACK = 100

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
    "BESTE", "EKOS", "KARTN", "OZGYO", "ULUUN",
    "BEYAZ", "EKSUN", "KFEIN", "OZGYO", "ULUSE",
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

def gonderilenleri_kaydet(hisseler):

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
                        mevcut.append(satir)

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

    except Exception as hata:

        print(
            "Gönderilenler kaydedilemedi:",
            type(hata)._name_,
            str(hata)
        )


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
# ADX
# =========================================================

def adx_hesapla(df):

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    onceki_close = close.shift(1)

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

def adx_gosterge(adx):

    if adx >= 25:
        return "🟢"

    if adx >= 20:
        return "🟡"

    return "🔴"


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

            if len(df) < 120:
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
# FIBONACCI SEVİYELERİ
# =========================================================

def fibonacci_seviyeleri(df):

    son_df = df.tail(
        FIB_LOOKBACK
    )

    high = float(
        son_df["High"].max()
    )

    low = float(
        son_df["Low"].min()
    )

    if high <= low:
        return None

    high_index = (
        son_df["High"].idxmax()
    )

    low_index = (
        son_df["Low"].idxmin()
    )

    aralik = high - low

    # -----------------------------------------------------
    # TradingView'deki mantığa uygun olarak,
    # son 100 mumdaki dip ve tepe kullanılır.
    #
    # Dip daha önce, tepe daha sonra oluştuysa
    # yükseliş hareketinin Fib seviyeleri:
    #
    # 0 = dip
    # 1 = tepe
    #
    # Tepe daha önce, dip daha sonra oluştuysa
    # seviyeleri ters yönde ele alıyoruz.
    # -----------------------------------------------------

    if low_index < high_index:

        yon = "yukselis"

        seviyeler = {
            "0.000": low,
            "0.236": low + aralik * 0.236,
            "0.382": low + aralik * 0.382,
            "0.500": low + aralik * 0.500,
            "0.618": low + aralik * 0.618,
            "0.786": low + aralik * 0.786,
            "1.000": high
        }

        uzatma = {
            "1.272": high + aralik * 0.272,
            "1.618": high + aralik * 0.618,
            "2.000": high + aralik,
            "2.618": high + aralik * 1.618
        }

    else:

        yon = "dus

us"

        seviyeler = {
            "0.000": high,
            "0.236": high - aralik * 0.236,
            "0.382": high - aralik * 0.382,
            "0.500": high - aralik * 0.500,
            "0.618": high - aralik * 0.618,
            "0.786": high - aralik * 0.786,
            "1.000": low
        }

        uzatma = {
            "1.272": low - aralik * 0.272,
            "1.618": low - aralik * 0.618,
            "2.000": low - aralik,
            "2.618": low - aralik * 1.618
        }

    seviyeler.update(
        uzatma
    )

    return {
        "yon": yon,
        "high": high,
        "low": low,
        "seviyeler": seviyeler
    }


# =========================================================
# FIB DESTEK / DİRENÇ
# =========================================================

def fib_destek_direnc_bul(
    df,
    fiyat
):

    fib = fibonacci_seviyeleri(
        df
    )

    if fib is None:
        return None

    seviyeler = fib[
        "seviyeler"
    ]

    # -----------------------------------------------------
    # Fiyatın altında kalan Fib seviyeleri = destek
    # -----------------------------------------------------

    destekler = []

    for oran, seviye in seviyeler.items():

        if seviye < fiyat * 0.999:

            destekler.append(
                (
                    float(seviye),
                    oran
                )
            )

    destekler.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # -----------------------------------------------------
    # Fiyatın üzerindeki Fib seviyeleri = direnç
    # -----------------------------------------------------

    direncler = []

    for oran, seviye in seviyeler.items():

        if seviye > fiyat * 1.001:

            direncler.append(
                (
                    float(seviye),
                    oran
                )
            )

    direncler.sort(
        key=lambda x: x[0]
    )

    s1 = (
        destekler[0]
        if len(destekler) >= 1
        else None
    )

    k1 = (
        direncler[0]
        if len(direncler) >= 1
        else None
    )

    k2 = (
        direncler[1]
        if len(direncler) >= 2
        else None
    )

    k3 = (
        direncler[2]
        if len(direncler) >= 3
        else None
    )

    k4 = (
        direncler[3]
        if len(direncler) >= 4
        else None
    )

    return {
        "s1": s1,
        "k1": k1,
        "k2": k2,
        "k3": k3,
        "k4": k4,
        "fib": fib
    }


# =========================================================
# SİNYAL GÜCÜ
# =========================================================

def sinyal_gucu_hesapla(
    rsi,
    adx,
    ema_mesafe,
    haftalik_degisim,
    hacim,
    ortalama_hacim
):

    puan = 0

    # RSI
    if rsi >= 70:
        puan += 20
    elif rsi >= 60:
        puan += 17
    elif rsi >= 55:
        puan += 14
    elif rsi > 50:
        puan += 10

    # ADX
    if adx >= 30:
        puan += 20
    elif adx >= 25:
        puan += 17
    elif adx >= 20:
        puan += 14
    elif adx >= 15:
        puan += 9

    # EMA mesafesi
    if ema_mesafe >= 7:
        puan += 20
    elif ema_mesafe >= 5:
        puan += 17
    elif ema_mesafe >= 3:
        puan += 14
    else:
        puan += 8

    # Haftalık performans
    if haftalik_degisim >= 10:
        puan += 20
    elif haftalik_degisim >= 7:
        puan += 17
    elif haftalik_degisim >= 4:
        puan += 14
    elif haftalik_degisim > 0:
        puan += 9

    # Hacim burada FILTRE DEĞİL.
    # Sadece sinyal gücünü desteklemek için kullanılıyor.
    if ortalama_hacim > 0:

        hacim_orani = (
            hacim
            / ortalama_hacim
        )

        if hacim_orani >= 2:
            puan += 20
        elif hacim_orani >= 1.5:
            puan += 17
        elif hacim_orani >= 1.0:
            puan += 14
        else:
            puan += 8

    else:

        puan += 8

    return min(
        100,
        max(0, puan)
    )


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
# ANALİZ
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
        # 20 GÜNLÜK ORTALAMA HACİM
        # -------------------------------------------------

        df["AVG_VOLUME_20"] = (
            df["Volume"]
            .rolling(20)
            .mean()
        )

        if len(df) < 120:
            return None

        onceki = df.iloc[-2]

        son = df.iloc[-1]

        hafta_once = df.iloc[-6]

        # -------------------------------------------------
        # DEĞİŞİMLER
        # -------------------------------------------------

        bir_haftalik_degisim = (
            (
                son["Close"]
                / hafta_once["Close"]
            )
            - 1
        ) * 100

        gunluk_degisim = (
            (
                son["Close"]
                / onceki["Close"]
            )
            - 1
        ) * 100

        try:

            hacim = float(
                son["Volume"]
            )

        except Exception:

            hacim = 0.0

        try:

            ortalama_hacim_20 = float(
                son["AVG_VOLUME_20"]
            )

        except Exception:

            ortalama_hacim_20 = 0.0

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

        # 2 - Fiyat EMA14'ün en az %3 üzerinde
        fiyat_ema_sinyal = (
            son["Close"]
            >= son["EMA14"] * 1.03
        )

        # 3 - EMA14 yükseliyor
        ema_yukseliyor = (
            son["EMA14"]
            > onceki["EMA14"]
        )

        # 4 - RSI14, 50 seviyesini
        # aşağıdan yukarı kesiyor
        rsi_50_cross = (
            onceki["RSI14"] <= 50
            and
            son["RSI14"] > 50
        )

        # 5 - RSI yükseliyor
        rsi_yukseliyor = (
            son["RSI14"]
            > onceki["RSI14"]
        )

        # -------------------------------------------------
        # TÜM ŞARTLAR
        # -------------------------------------------------

        if not (
            ichimoku_sinyal
            and
            fiyat_ema_sinyal
            and
            ema_yukseliyor
            and
            rsi_50_cross
            and
            rsi_yukseliyor
        ):

            return None

        fiyat = float(
            son["Close"]
        )

        ema14 = float(
            son["EMA14"]
        )

        rsi14 = float(
            son["RSI14"]
        )

        # =================================================
        # FIB DESTEK / DİRENÇ
        # =================================================

        fib_sonuclari = (
            fib_destek_direnc_bul(
                df,
                fiyat
            )
        )

        if fib_sonuclari is None:
            return None

        s1_bilgi = (
            fib_sonuclari["s1"]
        )

        k1_bilgi = (
            fib_sonuclari["k1"]
        )

        k2_bilgi = (
            fib_sonuclari["k2"]
        )

        k3_bilgi = (
            fib_sonuclari["k3"]
        )

        k4_bilgi = (
            fib_sonuclari["k4"]
        )

        # -------------------------------------------------
        # En az S1 ve K1 olmalı
        # -------------------------------------------------

        if s1_bilgi is None:
            print(
                f"{symbol}: S1 bulunamadı."
            )
            return None

        if k1_bilgi is None:
            print(
                f"{symbol}: K1 bulunamadı."
            )
            return None

        s1 = s1_bilgi[0]
        s1_fib = s1_bilgi[1]

        k1 = k1_bilgi[0]
        k1_fib = k1_bilgi[1]

        k2 = (
            k2_bilgi[0]
            if k2_bilgi is not None
            else None
        )

        k2_fib = (
            k2_bilgi[1]
            if k2_bilgi is not None
            else None
        )

        k3 = (
            k3_bilgi[0]
            if k3_bilgi is not None
            else None
        )

        k3_fib = (
            k3_bilgi[1]
            if k3_bilgi is not None
            else None
        )

        k4 = (
            k4_bilgi[0]
            if k4_bilgi is not None
            else None
        )

        k4_fib = (
            k4_bilgi[1]
            if k4_bilgi is not None
            else None
        )

        # =================================================
        # STOP
        # =================================================

        stop = (
            s1 * 0.995
        )

        # =================================================
        # EMA MESAFESİ
        # =================================================

        ema_mesafe = (
            (
                fiyat
                / ema14
            ) - 1
        ) * 100

        # =================================================
        # SİNYAL GÜCÜ
        # =================================================

        sinyal_gucu = (
            sinyal_gucu_hesapla(
                rsi14,
                adx,
                ema_mesafe,
                bir_haftalik_degisim,
                hacim,
                ortalama_hacim_20
            )
        )

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

            "avg_volume_20": (
                ortalama_hacim_20
            ),

            "ema14": ema14,

            "ema_mesafe": (
                ema_mesafe
            ),

            "rsi14": rsi14,

            "adx14": adx,

            "sinyal_gucu": (
                sinyal_gucu
            ),

            "s1": s1,

            "s1_fib": s1_fib,

            "stop": stop,

            "k1": k1,

            "k1_fib": k1_fib,

            "k2": k2,

            "k2_fib": k2_fib,

            "k3": k3,

            "k3_fib": k3_fib,

            "k4": k4,

            "k4_fib": k4_fib
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

        adx_deger = (
            sonuc["adx14"]
        )

        adx_isaret = (
            adx_gosterge(
                adx_deger
            )
        )

        fiyat = (
            sonuc["price"]
        )

        stop = (
            sonuc["stop"]
        )

        s1 = (
            sonuc["s1"]
        )

        k1 = (
            sonuc["k1"]
        )

        k2 = (
            sonuc["k2"]
        )

        k3 = (
            sonuc["k3"]
        )

        k4 = (
            sonuc["k4"]
        )

        stop_yuzde = (
            yuzde_mesafe(
                stop,
                fiyat
            )
        )

        k1_yuzde = (
            yuzde_mesafe(
                k1,
                fiyat
            )
        )

        k2_yuzde = (
            yuzde_mesafe(
                k2,
                fiyat
            )
            if k2 is not None
            else None
        )

        k3_yuzde = (
            yuzde_mesafe(
                k3,
                fiyat
            )
            if k3 is not None
            else None
        )

        k4_yuzde = (
            yuzde_mesafe(
                k4,
                fiyat
            )
            if k4 is not None
            else None
        )

        # =================================================
        # TELEGRAM MESAJI
        # =================================================

        mesaj = (
            f"🟢 YENİ : {symbol}"
            f"                    "
            f"ADX {adx_isaret} "
            f"{adx_deger:.1f}\n"

            f"⭐ Sinyal Gücü: "
            f"{sonuc['sinyal_gucu']}/100\n\n"

            f"💰 Giriş: "
            f"{fiyat:.2f} TL\n"

            f"{gunluk_isaret} Günlük: "
            f"{sonuc['daily_change']:+.2f}%\n"

            f"{hafta_isaret} 1 Hafta: "
            f"{sonuc['weekly_change']:+.2f}%\n"

            f"📏 EMA14: "
            f"{sonuc['ema14']:.2f} TL "
            f"({sonuc['ema_mesafe']:+.2f}%)\n"

            f"📊 RSI: "
            f"{sonuc['rsi14']:.1f}\n"

            f"🔊 Hacim: "
            f"{sonuc['volume']:,.0f}\n"

            f"📊 20G Ort. Hacim: "
            f"{sonuc['avg_volume_20']:,.0f}\n\n"

            f"🛑 S1 Destek: "
            f"{s1:.2f} TL "
            f"(Fib {sonuc['s1_fib']})\n"

            f"🛑 Stop: "
            f"{stop:.2f} TL "
            f"→ {stop_yuzde:+.2f}%\n\n"

            f"🎯 K1: "
            f"{k1:.2f} TL "
            f"(Fib {sonuc['k1_fib']}) "
            f"→ {k1_yuzde:+.2f}%\n"
        )

        if k2 is not None:

            mesaj += (
                f"🎯 K2: "
                f"{k2:.2f} TL "
                f"(Fib {sonuc['k2_fib']}) "
                f"→ {k2_yuzde:+.2f}%\n"
            )

        else:

            mesaj += (
                "🎯 K2: Bulunamadı\n"
            )

        if k3 is not None:

            mesaj += (
                f"🎯 K3: "
                f"{k3:.2f} TL "
                f"(Fib {sonuc['k3_fib']}) "
                f"→ {k3_yuzde:+.2f}%\n"
            )

        else:

            mesaj += (
                "🎯 K3: Bulunamadı\n"
            )

        if k4 is not None:

            mesaj += (
                f"🎯 K4: "
                f"{k4:.2f} TL "
                f"(Fib {sonuc['k4_fib']}) "
                f"→ {k4_yuzde:+.2f}%"
            )

        else:

            mesaj += (
                "🎯 K4: Bulunamadı"
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
