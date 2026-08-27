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
# ADX RENK
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

            if len(df) < 60:
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
# DESTEK / DİRENÇ BUL
# =========================================================

def destek_direnc_bul(
    df,
    fiyat
):

    high = df["High"].astype(
        float
    )

    low = df["Low"].astype(
        float
    )

    direncler = []
    destekler = []

    pencere = 3

    for i in range(
        pencere,
        len(df) - pencere
    ):

        mevcut_high = high.iloc[i]

        sol_high = high.iloc[
            i - pencere:i
        ].max()

        sag_high = high.iloc[
            i + 1:i + pencere + 1
        ].max()

        if (
            mevcut_high >= sol_high
            and
            mevcut_high >= sag_high
        ):

            direncler.append(
                float(mevcut_high)
            )

        mevcut_low = low.iloc[i]

        sol_low = low.iloc[
            i - pencere:i
        ].min()

        sag_low = low.iloc[
            i + 1:i + pencere + 1
        ].min()

        if (
            mevcut_low <= sol_low
            and
            mevcut_low <= sag_low
        ):

            destekler.append(
                float(mevcut_low)
            )

    def seviyeleri_temizle(
        seviyeler
    ):

        if not seviyeler:
            return []

        seviyeler = sorted(
            seviyeler
        )

        temiz = [
            seviyeler[0]
        ]

        for seviye in seviyeler[1:]:

            son_seviye = temiz[-1]

            if son_seviye == 0:
                temiz.append(seviye)
                continue

            fark = (
                abs(
                    seviye
                    - son_seviye
                )
                / son_seviye
            ) * 100

            if fark >= 1.5:

                temiz.append(
                    seviye
                )

            else:

                temiz[-1] = (
                    son_seviye
                    + seviye
                ) / 2

        return temiz

    direncler = seviyeleri_temizle(
        direncler
    )

    destekler = seviyeleri_temizle(
        destekler
    )

    ust_direncler = [
        seviye
        for seviye in direncler
        if seviye > fiyat * 1.005
    ]

    ust_direncler.sort()

    alt_destekler = [
        seviye
        for seviye in destekler
        if seviye < fiyat * 0.995
    ]

    alt_destekler.sort(
        reverse=True
    )

    k1 = (
        ust_direncler[0]
        if len(ust_direncler) >= 1
        else None
    )

    k2 = (
        ust_direncler[1]
        if len(ust_direncler) >= 2
        else None
    )

    k3 = (
        ust_direncler[2]
        if len(ust_direncler) >= 3
        else None
    )

    s1 = (
        alt_destekler[0]
        if len(alt_destekler) >= 1
        else None
    )

    return (
        s1,
        k1,
        k2,
        k3
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

    if fiyat == 0:
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
# =========================================================

def sinyal_gucu_hesapla(
    fiyat,
    ema14,
    ema_onceki,
    rsi14,
    rsi_onceki,
    adx14,
    hacim,
    hacim_ort20,
    k1
):

    puan = 0.0

    # -----------------------------------------------------
    # 1. BASE yukarı kesişimi
    # Bu şart zaten filtre olduğu için 20 puan.
    # -----------------------------------------------------

    puan += 20


    # -----------------------------------------------------
    # 2. Fiyat EMA14 üzerinde ne kadar güçlü?
    # %3 = düşük puan
    # %8 ve üzeri = maksimum
    # -----------------------------------------------------

    if ema14 > 0:

        ema_mesafe = (
            (fiyat / ema14) - 1
        ) * 100

        ema_puan = min(
            15,
            max(
                0,
                (ema_mesafe - 3) / 5 * 15
            )
        )

        puan += ema_puan


    # -----------------------------------------------------
    # 3. EMA14 yükselişi
    # -----------------------------------------------------

    if ema_onceki > 0:

        ema_egim = (
            (
                ema14
                / ema_onceki
            ) - 1
        ) * 100

        ema_puan = min(
            15,
            max(
                0,
                ema_egim / 1.0 * 15
            )
        )

        puan += ema_puan


    # -----------------------------------------------------
    # 4. RSI gücü
    # 50 = düşük
    # 65+ = maksimum
    # -----------------------------------------------------

    rsi_puan = min(
        10,
        max(
            0,
            (rsi14 - 50) / 15 * 10
        )
    )

    puan += rsi_puan


    # -----------------------------------------------------
    # 5. RSI yükselişi
    # -----------------------------------------------------

    rsi_fark = (
        rsi14
        - rsi_onceki
    )

    rsi_puan = min(
        10,
        max(
            0,
            rsi_fark / 5 * 10
        )
    )

    puan += rsi_puan


    # -----------------------------------------------------
    # 6. Hacim / 20 günlük ortalama
    # Filtre DEĞİL.
    # Sadece puana katkı sağlar.
    # -----------------------------------------------------

    if (
        hacim_ort20 > 0
        and hacim > 0
    ):

        hacim_orani = (
            hacim
            / hacim_ort20
        )

        hacim_puan = min(
            15,
            max(
                0,
                (hacim_orani - 0.8)
                / 1.2
                * 15
            )
        )

        puan += hacim_puan


    # -----------------------------------------------------
    # 7. ADX
    # 15 = düşük
    # 30+ = maksimum
    # -----------------------------------------------------

    adx_puan = min(
        10,
        max(
            0,
            (adx14 - 15)
            / 15
            * 10
        )
    )

    puan += adx_puan


    # -----------------------------------------------------
    # 8. K1 mesafesi
    # K1 girişten yeterince yukarıdaysa puan artar.
    # -----------------------------------------------------

    if (
        k1 is not None
        and fiyat > 0
    ):

        k1_mesafe = (
            (
                k1
                / fiyat
            ) - 1
        ) * 100

        k1_puan = min(
            5,
            max(
                0,
                k1_mesafe / 10 * 5
            )
        )

        puan += k1_puan


    # -----------------------------------------------------
    # 0-100 aralığında tut
    # -----------------------------------------------------

    puan = max(
        0,
        min(
            100,
            puan
        )
    )

    return round(
        puan
    )


# =========================================================
# SİNYAL GÜCÜ YAZISI
# =========================================================

def sinyal_gucu_gosterge(
    puan
):

    if puan >= 80:
        return "🟢 ÇOK GÜÇLÜ"

    if puan >= 70:
        return "🟢 GÜÇLÜ"

    if puan >= 60:
        return "🟡 ORTA"

    if puan >= 50:
        return "🟠 ZAYIF"

    return "🔴 ÇOK ZAYIF"


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
        # 20 GÜNLÜK ORTALAMA HACİM
        # -------------------------------------------------

        df["VolumeAvg20"] = (
            df["Volume"]
            .rolling(
                VOLUME_AVG_PERIOD
            )
            .mean()
        )


        # -------------------------------------------------
        # SON VERİLER
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


        # -------------------------------------------------
        # HACİM
        # -------------------------------------------------

        try:

            hacim = float(
                son["Volume"]
            )

        except Exception:

            hacim = 0.0


        try:

            hacim_ort20 = float(
                son["VolumeAvg20"]
            )

        except Exception:

            hacim_ort20 = 0.0


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
        # ANA TARAMA ŞARTLARI
        # =================================================

        # 1️⃣ BASE yukarı kesildi

        ichimoku_sinyal = (
            onceki["BASE"]
            >= onceki["Close"]
            and
            son["BASE"]
            < son["Close"]
        )


        # 2️⃣ Fiyat EMA14'ün en az %3 üzerinde

        fiyat_ema_sinyal = (
            son["Close"]
            >= son["EMA14"] * 1.03
        )


        # 3️⃣ EMA14 yükseliyor

        ema_yukseliyor = (
            son["EMA14"]
            > onceki["EMA14"]
        )


        # 4️⃣ RSI 50'nin üzerinde

        rsi_50_ustu = (
            son["RSI14"]
            > 50
        )


        # 5️⃣ RSI yükseliyor

        rsi_yukseliyor = (
            son["RSI14"]
            > onceki["RSI14"]
        )


        # =================================================
        # TÜM ANA ŞARTLAR SAĞLANMALI
        # =================================================

        if not (
            ichimoku_sinyal
            and fiyat_ema_sinyal
            and ema_yukseliyor
            and rsi_50_ustu
            and rsi_yukseliyor
        ):

            return None


        fiyat = float(
            son["Close"]
        )

        ema14 = float(
            son["EMA14"]
        )

        ema_onceki = float(
            onceki["EMA14"]
        )

        rsi14 = float(
            son["RSI14"]
        )

        rsi_onceki = float(
            onceki["RSI14"]
        )


        # =================================================
        # DESTEK / DİRENÇ
        # =================================================

        (
            s1,
            k1,
            k2,
            k3
        ) = destek_direnc_bul(
            df,
            fiyat
        )


        # -------------------------------------------------
        # S1 yoksa sinyal gönderme
        # -------------------------------------------------

        if s1 is None:

            print(
                f"{symbol}: "
                f"S1 destek bulunamadı."
            )

            return None


        # -------------------------------------------------
        # K1 yoksa sinyal gönderme
        # -------------------------------------------------

        if k1 is None:

            print(
                f"{symbol}: "
                f"K1 direnç bulunamadı."
            )

            return None


        # =================================================
        # STOP
        # =================================================

        # S1'in %0.5 altında güvenlik payı

        stop = (
            s1 * 0.995
        )


        # =================================================
        # SİNYAL GÜCÜ
        # =================================================

        sinyal_puani = (
            sinyal_gucu_hesapla(
                fiyat=fiyat,
                ema14=ema14,
                ema_onceki=ema_onceki,
                rsi14=rsi14,
                rsi_onceki=rsi_onceki,
                adx14=adx,
                hacim=hacim,
                hacim_ort20=hacim_ort20,
                k1=k1
            )
        )


        # =================================================
        # HACİM YÜZDE FARKI
        # =================================================

        if hacim_ort20 > 0:

            hacim_farki = (
                (
                    hacim
                    / hacim_ort20
                ) - 1
            ) * 100

        else:

            hacim_farki = 0.0


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

            "volume_avg20": hacim_ort20,

            "volume_difference": float(
                hacim_farki
            ),

            "ema14": ema14,

            "rsi14": rsi14,

            "adx14": adx,

            "stop": float(
                stop
            ),

            "s1": float(
                s1
            ),

            "k1": (
                float(k1)
                if k1 is not None
                else None
            ),

            "k2": (
                float(k2)
                if k2 is not None
                else None
            ),

            "k3": (
                float(k3)
                if k3 is not None
                else None
            ),

            "signal_score": int(
                sinyal_puani
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


        adx_deger = (
            sonuc["adx14"]
        )


        adx_isaret = (
            adx_gosterge(
                adx_deger
            )
        )


        sinyal_puani = (
            sonuc["signal_score"]
        )


        sinyal_gucu = (
            sinyal_gucu_gosterge(
                sinyal_puani
            )
        )


        fiyat = (
            sonuc["price"]
        )


        s1 = (
            sonuc["s1"]
        )


        stop = (
            sonuc["stop"]
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


        # -------------------------------------------------
        # YÜZDELER
        # -------------------------------------------------

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
        )


        k3_yuzde = (
            yuzde_mesafe(
                k3,
                fiyat
            )
        )


        # -------------------------------------------------
        # HACİM
        # -------------------------------------------------

        hacim_farki = (
            sonuc[
                "volume_difference"
            ]
        )


        if hacim_farki >= 0:

            hacim_yazisi = (
                f"+{hacim_farki:.1f}% "
                f"Ort. üstü"
            )

        else:

            hacim_yazisi = (
                f"{hacim_farki:.1f}% "
                f"Ort. altı"
            )


        # -------------------------------------------------
        # GÜNLÜK / HAFTALIK İŞARET
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


        # =================================================
        # TELEGRAM MESAJI
        # =================================================

        mesaj = (

            f"🟢 YENİ : {symbol}"
            f"                    "
            f"ADX {adx_isaret} "
            f"{adx_deger:.1f}\n"

            f"⭐ Sinyal Gücü: "
            f"{sinyal_puani}/100 "
            f"{sinyal_gucu}\n\n"


            f"💰 Giriş: "
            f"{fiyat:.2f} TL\n"


            f"{gunluk_isaret} Günlük: "
            f"{sonuc['daily_change']:+.2f}%\n"


            f"{hafta_isaret} 1 Hafta: "
            f"{sonuc['weekly_change']:+.2f}%\n"


            f"📏 EMA14: "
            f"{sonuc['ema14']:.2f} TL\n"


            f"📊 RSI: "
            f"{sonuc['rsi14']:.1f}\n"


            f"🔊 Hacim: "
            f"{sonuc['volume']:,.0f}\n"


            f"📊 Hacim Ort.20: "
            f"{sonuc['volume_avg20']:,.0f}\n"


            f"📈 Hacim: "
            f"{hacim_yazisi}\n\n"


            f"🛑 S1 Destek: "
            f"{s1:.2f} TL\n"


            f"🛑 Stop: "
            f"{stop:.2f} TL "
            f"→ {stop_yuzde:+.2f}%\n\n"


            f"🎯 K1: "
            f"{k1:.2f} TL "
            f"→ {k1_yuzde:+.2f}%\n"
        )


        if k2 is not None:

            mesaj += (

                f"🎯 K2: "
                f"{k2:.2f} TL "
                f"→ {k2_yuzde:+.2f}%\n"
            )

        else:

            mesaj += (
                "🎯 K2: "
                "Bulunamadı\n"
            )


        if k3 is not None:

            mesaj += (

                f"🎯 K3: "
                f"{k3:.2f} TL "
                f"→ {k3_yuzde:+.2f}%"
            )

        else:

            mesaj += (
                "🎯 K3: "
                "Bulunamadı"
            )


        # -------------------------------------------------
        # TELEGRAM'A GÖNDER
        # -------------------------------------------------

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
