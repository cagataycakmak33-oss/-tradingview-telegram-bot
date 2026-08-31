import os
import time
import requests
import borsapy as bp
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GONDERILEN_DOSYA = "gonderilen_hisseler.txt"

EMA_PERIOD = 14
RSI_PERIOD = 14
BASE_PERIOD = 26
ADX_PERIOD = 14

EMA_MIN_DISTANCE = 0.02

# TradingView ile aynı mantık:
# Son 100 günlük mum içerisindeki dip ve tepe
FIB_LOOKBACK = 100

MAX_WORKERS = 4
MAX_RETRIES = 3

ISTANBUL = ZoneInfo("Europe/Istanbul")


ANA_PAZAR = {
    "A1YEN","CATES","FRIGO","LKMNH","PRKAB","ACSEL","CELHA","FRMPL","LUKSK","PRKME",
    "ADEL","CEMAS","GARFA","LXGYO","PRZMA","ADESE","CEMTS","GEDZA","LYDYE","PSDTC",
    "AFYON","CEOEM","GENKM","MAALT","RAYSG","AHSGY","CMBTN","GEREL","MACKO","RTALB",
    "AKENR","CONSE","GLRYH","MAKIM","RUBNS","AKHAN","CRFSA","GOODY","MAKTK","RUZYE",
    "AKMGY","CUSAN","GSDDE","MANAS","SANFM","AKSUE","DAGI","GSDHO","MARBL","SANKO",
    "ALCAR","DARDL","GUNDG","MARKA","SAYAS","ALCTL","DCTTR","GZNMI","MARMR","SEGMN",
    "ALKA","DENGE","HATEK","MARTI","SEGYO","ALKIM","DERHL","HDFGS","MCARD","SELVA",
    "ALKLC","DERIM","HEDEF","MEDTR","SERNT","ALVES","DESA","HKTM","MEKAG","SKTAS",
    "ANELE","DESPC","HOROZ","MERCN","SKYMD","ANGEN","DGATE","HUNER","MERCN","SMART",
    "ARENA","DGNMO","HURGZ","METRO","SMRVA","ARFYE","DITAS","ICBCT","MEYSU","SNICA",
    "ARSAN","DMRGD","ICUGS","IHAAS","MHRGY","ARTMS","DMSAS","ICUGS","MNDRS","SVGYO",
    "ARZUM","DNISI","IHGZT","MNDTR","TATGD","AVGYO","DOCO","IHLGM","MRGYO","TBORG",
    "AVOD","DOKTA","IMASM","MRSHL","TEHOL","AYCES","DUNYH","INFO","MSGYO","TEKTU",
    "AYEN","DURDO","INGRM","MTRKS","TERA","AZTEK","DURKN","INTEM","NETAS","TGSAS",
    "BAGFS","DYOBY","DZGYO","ISYAT","OBASE","BAHKM","EDATA","IZFAS","OFSYM","TSGYO",
    "BAKAB","EDIP","IZINV","ONCSM","TUCLK","BANVT","EGEGY","IZMDC","ONRYT","TURGG",
    "BAYRK","EGEPO","JANTS","KAPLM","OSTIM","UFUK","BEGYO","EGSER","KARTN","OZGYO",
    "ULUFA","BESTE","EKOS","KFEIN","ULUUN","BEYAZ","EKSUN","KGYO","OZSUB","UNLU",
    "BIGCH","ELITE","KIMMR","OZYSR","VBTYZ","BIGTK","EMKEL","KLMSN","PAMEL","VERTU",
    "BIZIM","EMPAE","KIMMR","PCILT","VERUS","BLCYT","ENSRI","KLSYN","PEKGY","VKING",
    "BLUME","EPLAS","KNFRT","PENGD","VRGYO","BMSCH","ERBOS","KONKA","PETUN","YAPRK",
    "BMSTL","ERCB","KRONT","KRPLS","PINSU","YIGIT","BNTAS","ESCOM","ETILR","KRSTL",
    "YAYLA","BRKVY","EYGYO","KRVGD","PKENT","YESIL","BRLSM","FADE","KTSKR","PLTUR",
    "YKSLN","BULGS","FMIZP","KUTPO","PNLSN","BURCE","FONET","PRDGS","ZGYO","BVSAN",
    "FORMT","FORTE","LIDFA"
}


def gonderilenleri_oku():

    bugun = datetime.now(ISTANBUL).strftime("%Y-%m-%d")

    if not os.path.exists(GONDERILEN_DOSYA):
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
                        kayitlar.add(hisse.upper())

        return kayitlar

    except Exception as hata:

        print(
            "Gönderilenler okunamadı:",
            type(hata)._name_,
            str(hata)
        )

        return set()


def gonderilenleri_kaydet(hisseler):

    bugun = datetime.now(
        ISTANBUL
    ).strftime("%Y-%m-%d")

    try:

        mevcut = []

        if os.path.exists(GONDERILEN_DOSYA):

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


def telegram_gonder(mesaj):

    url = (
        "https://api.telegram.org/"
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


def bist100_listesi():

    try:

        index = bp.Index("XU100")

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

    true_range = (
        tr1
        .combine(tr2, max)
        .combine(tr3, max)
    )

    atr = true_range.ewm(
        alpha=1 / ADX_PERIOD,
        adjust=False
    ).mean()

    plus_di = (
        100
        *
        plus_dm.ewm(
            alpha=1 / ADX_PERIOD,
            adjust=False
        ).mean()
        / atr
    )

    minus_di = (
        100
        *
        minus_dm.ewm(
            alpha=1 / ADX_PERIOD,
            adjust=False
        ).mean()
        / atr
    )

    di_toplam = (
        plus_di + minus_di
    )

    dx = (
        100
        *
        (
            plus_di
            - minus_di
        ).abs()
        / di_toplam
    )

    return dx.ewm(
        alpha=1 / ADX_PERIOD,
        adjust=False
    ).mean()


def adx_gosterge(adx):

    if adx >= 25:
        return "🟢"

    if adx >= 20:
        return "🟡"

    return "🔴"


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

            if (
                df is None
                or len(df) < 120
            ):
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

                bekleme = 2 ** deneme

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


# =====================================================
# FIBONACCI
# =====================================================

def fibonacci_seviyeleri(df):

    if len(df) < FIB_LOOKBACK:
        return None

    son_df = df.tail(
        FIB_LOOKBACK
    ).copy()

    high_series = (
        son_df["High"]
    )

    low_series = (
        son_df["Low"]
    )

    fib_high = float(
        high_series.max()
    )

    fib_low = float(
        low_series.min()
    )

    if fib_high <= fib_low:
        return None

    # Gerçek dip / tepe konumları
    high_index = (
        high_series.idxmax()
    )

    low_index = (
        low_series.idxmin()
    )

    # Kronolojik yön
    # Dip daha eskiyse yükseliş
    # Tepe daha eskiyse düşüş
    yukselis = (
        low_index < high_index
    )

    aralik = (
        fib_high - fib_low
    )

    oranlar = [
        ("0.000", 0.000),
        ("0.236", 0.236),
        ("0.382", 0.382),
        ("0.500", 0.500),
        ("0.618", 0.618),
        ("0.786", 0.786),
        ("1.000", 1.000)
    ]

    seviyeler = {}

    for oran, katsayi in oranlar:

        if yukselis:

            seviye = (
                fib_low
                +
                aralik * katsayi
            )

        else:

            seviye = (
                fib_high
                -
                aralik * katsayi
            )

        seviyeler[oran] = float(
            seviye
        )

    return {
        "high": fib_high,
        "low": fib_low,
        "yon": (
            "yukselis"
            if yukselis
            else "dus"
        ),
        "seviyeler": seviyeler
    }


def fib_analiz(df, fiyat):

    fib = fibonacci_seviyeleri(
        df
    )

    if fib is None:
        return None

    seviyeler = fib[
        "seviyeler"
    ]

    # Fiyatın altındaki en yakın Fib
    alt = []

    for oran, seviye in seviyeler.items():

        if seviye < fiyat:
            alt.append(
                (
                    seviye,
                    oran
                )
            )

    alt.sort(
        key=lambda x: x[0],
        reverse=True
    )

    stop_bilgi = (
        alt[0]
        if alt
        else None
    )

    # Fiyatın üstündeki Fib seviyeleri
    ust = []

    for oran, seviye in seviyeler.items():

        if seviye > fiyat:

            kar_yuzdesi = (
                (seviye - fiyat)
                / fiyat
            ) * 100

            ust.append(
                (
                    seviye,
                    oran,
                    kar_yuzdesi
                )
            )

    ust.sort(
        key=lambda x: x[0]
    )

    # Fiyatın üzerinde bulunan en yakın Fib
    yakin_ust = (
        ust[0]
        if ust
        else None
    )

    # Tepe / 1.000 potansiyeli
    fib100 = seviyeler[
        "1.000"
    ]

    tepe_potansiyel = (
        (fib100 - fiyat)
        / fiyat
    ) * 100

    # Fiyat hangi iki Fib arasında?
    fiyat_seviyesi = None

    en_yakin_mesafe = None

    for oran, seviye in seviyeler.items():

        mesafe = abs(
            fiyat - seviye
        )

        if (
            en_yakin_mesafe is None
            or mesafe < en_yakin_mesafe
        ):

            en_yakin_mesafe = mesafe
            fiyat_seviyesi = oran

    return {
        "fib": fib,
        "seviyeler": seviyeler,
        "stop": stop_bilgi,
        "yakin_ust": yakin_ust,
        "tepe_potansiyel": tepe_potansiyel,
        "fiyat_seviyesi": fiyat_seviyesi
    }


def sinyal_gucu_hesapla(
    rsi,
    adx,
    ema_mesafe,
    haftalik_degisim,
    hacim,
    ortalama_hacim
):

    puan = 0

    if rsi >= 70:
        puan += 20

    elif rsi >= 60:
        puan += 17

    elif rsi >= 55:
        puan += 14

    elif rsi > 50:
        puan += 10

    if adx >= 30:
        puan += 20

    elif adx >= 25:
        puan += 17

    elif adx >= 20:
        puan += 14

    elif adx >= 15:
        puan += 9

    if ema_mesafe >= 7:
        puan += 20

    elif ema_mesafe >= 5:
        puan += 17

    elif ema_mesafe >= 3:
        puan += 14

    else:
        puan += 8

    if haftalik_degisim >= 10:
        puan += 20

    elif haftalik_degisim >= 7:
        puan += 17

    elif haftalik_degisim >= 4:
        puan += 14

    elif haftalik_degisim > 0:
        puan += 9

    if ortalama_hacim > 0:

        hacim_orani = (
            hacim
            /
            ortalama_hacim
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

        df["EMA14"] = (
            df["Close"].ewm(
                span=EMA_PERIOD,
                adjust=False
            ).mean()
        )

        df["RSI14"] = (
            rsi_hesapla(
                df["Close"]
            )
        )

        df["ADX14"] = (
            adx_hesapla(
                df
            )
        )

        df["BASE"] = (
            df["High"]
            .rolling(
                BASE_PERIOD
            )
            .max()
            +
            df["Low"]
            .rolling(
                BASE_PERIOD
            )
            .min()
        ) / 2

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

        bir_haftalik_degisim = (
            (
                son["Close"]
                /
                hafta_once["Close"]
            )
            - 1
        ) * 100

        gunluk_degisim = (
            (
                son["Close"]
                /
                onceki["Close"]
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
                son[
                    "AVG_VOLUME_20"
                ]
            )
        except Exception:
            ortalama_hacim_20 = 0.0

        try:
            adx = float(
                son["ADX14"]
            )
        except Exception:
            adx = 0.0

        ichimoku_sinyal = (
            onceki["BASE"]
            >=
            onceki["Close"]
            and
            son["BASE"]
            <
            son["Close"]
        )

        fiyat_ema_sinyal = (
            son["Close"]
            >=
            son["EMA14"]
            *
            (1 + EMA_MIN_DISTANCE)
        )

        ema_yukseliyor = (
            son["EMA14"]
            >
            onceki["EMA14"]
        )

        rsi_50_cross = (
            onceki["RSI14"]
            <= 50
            and
            son["RSI14"]
            > 50
        )

        rsi_yukseliyor = (
            son["RSI14"]
            >
            onceki["RSI14"]
        )

        if not (
            ichimoku_sinyal
            and fiyat_ema_sinyal
            and ema_yukseliyor
            and rsi_50_cross
            and rsi_yukseliyor
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
        # YENİ FIB ANALİZİ
        # =================================================

        fib_sonuc = fib_analiz(
            df,
            fiyat
        )

        if fib_sonuc is None:
            return None

        stop_bilgi = (
            fib_sonuc["stop"]
        )

        if stop_bilgi is None:
            print(
                f"{symbol}: "
                "Fiyat altında Fib stop bulunamadı."
            )
            return None

        stop_fiyat = (
            stop_bilgi[0]
        )

        stop_fib = (
            stop_bilgi[1]
        )

        sonuc = {

            "symbol": symbol,

            "price": fiyat,

            "daily_change":
                float(
                    gunluk_degisim
                ),

            "weekly_change":
                float(
                    bir_haftalik_degisim
                ),

            "volume": hacim,

            "avg_volume_20":
                ortalama_hacim_20,

            "ema14": ema14,

            "ema_mesafe": (
                (
                    fiyat
                    /
                    ema14
                )
                - 1
            ) * 100,

            "rsi14": rsi14,

            "adx14": adx,

            "stop":
                stop_fiyat,

            "stop_fib":
                stop_fib,

            "fib_levels":
                fib_sonuc[
                    "seviyeler"
                ],

            "fib_low":
                fib_sonuc[
                    "fib"
                ]["low"],

            "fib_high":
                fib_sonuc[
                    "fib"
                ]["high"],

            "fib_yon":
                fib_sonuc[
                    "fib"
                ]["yon"],

            "fiyat_fib":
                fib_sonuc[
                    "fiyat_seviyesi"
                ],

            "tepe_potansiyel":
                fib_sonuc[
                    "tepe_potansiyel"
                ],

            "yakin_ust":
                fib_sonuc[
                    "yakin_ust"
                ]
        }

        sonuc["sinyal_gucu"] = (
            sinyal_gucu_hesapla(
                rsi14,
                adx,
                sonuc["ema_mesafe"],
                bir_haftalik_degisim,
                hacim,
                ortalama_hacim_20
            )
        )

        return sonuc

    except Exception as hata:

        print(
            symbol,
            "HATA:",
            type(hata)._name_,
            str(hata)
        )

        return None


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
        /
        fiyat
    ) * 100


def fib_satiri(
    oran,
    seviye,
    fiyat,
    fiyat_fib
):

    # Fiyatın bulunduğu seviyeyi
    # yeşil ok ile gösteriyoruz.

    if oran == fiyat_fib:

        potansiyel = (
            (
                seviye
                - fiyat
            )
            /
            fiyat
        ) * 100

        return (
            f"🟢 ➜ {oran} → "
            f"{seviye:.2f} TL"
            f"  |  "
            f"{potansiyel:+.2f}%"
        )

    # Fiyatın üzerindeki seviyelerde
    # kâr yüzdesini göster.

    if seviye > fiyat:

        potansiyel = (
            (
                seviye
                - fiyat
            )
            /
            fiyat
        ) * 100

        return (
            f"{oran} → "
            f"{seviye:.2f} TL"
            f"  |  "
            f"{potansiyel:+.2f}%"
        )

    return (
        f"{oran} → "
        f"{seviye:.2f} TL"
    )


def main():

    print(
        "\n===================================="
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

    print(
        "\n⚡ Hızlı tarama başlıyor..."
    )

    print(
        f"⚡ Aynı anda "
        f"{MAX_WORKERS} hisse taranacak."
    )

    print(
        "📏 EMA14 minimum mesafe: +2%"
    )

    print(
        "📊 RSI14: 50 yukarı kesiş + yükseliş"
    )

    print(
        "📈 EMA14: yükseliş"
    )

    print(
        "☁️ Ichimoku Base: yukarı kırılım"
    )

    print(
        "📐 Fibonacci: Son 100 günlük dip/tepe"
    )

    print(
        "🛑 STOP: Fiyatın altındaki en yakın Fib"
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

            symbol = gelecekler[
                gelecek
            ]

            try:

                sonuc = (
                    gelecek.result()
                )

                tamamlanan += 1

                if sonuc:

                    if symbol in gonderilenler:

                        print(
                            f"⏭️ {symbol} "
                            "bugün zaten gönderildi."
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

    sure = (
        datetime.now(
            ISTANBUL
        )
        - baslangic_zamani
    ).total_seconds()

    print(
        f"\n⏱️ Tarama süresi: "
        f"{int(sure // 60)} dakika "
        f"{int(sure % 60)} saniye"
    )

    print(
        "\n===================================="
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

    basariyla_gonderilenler = set()

    for sonuc in bulunan:

        symbol = sonuc[
            "symbol"
        ]

        if symbol in bist100:

            pazar_adi = "BIST 100"

        elif symbol in ANA_PAZAR:

            pazar_adi = "Ana Pazar"

        else:

            pazar_adi = "Bilinmiyor"

        gunluk_isaret = (
            "🟢"
            if sonuc[
                "daily_change"
            ] >= 0
            else "🔴"
        )

        hafta_isaret = (
            "🟢"
            if sonuc[
                "weekly_change"
            ] >= 0
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

        stop_fib = (
            sonuc["stop_fib"]
        )

        fibler = (
            sonuc["fib_levels"]
        )

        fiyat_fib = (
            sonuc["fiyat_fib"]
        )

        # =================================================
        # TELEGRAM MESAJI
        # =================================================

        mesaj = (

            f"🟢 YENİ : {symbol}"
            f"                   ADX "
            f"{adx_isaret} "
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
            f"{sonuc['rsi14']:.1f}\n\n"

            f"📐 FIB SEVİYELERİ\n\n"

            f"{fib_satiri('0.000', fibler['0.000'], fiyat, fiyat_fib)}\n"

            f"{fib_satiri('0.236', fibler['0.236'], fiyat, fiyat_fib)}\n"

            f"{fib_satiri('0.382', fibler['0.382'], fiyat, fiyat_fib)}\n"

            f"{fib_satiri('0.500', fibler['0.500'], fiyat, fiyat_fib)}\n"

            f"{fib_satiri('0.618', fibler['0.618'], fiyat, fiyat_fib)}\n"

            f"{fib_satiri('0.786', fibler['0.786'], fiyat, fiyat_fib)}\n"

            f"{fib_satiri('1.000', fibler['1.000'], fiyat, fiyat_fib)}\n\n"

            f"🛑 STOP\n"

            f"{stop_fib} → "
            f"{stop:.2f} TL\n\n"

            f"🎯 TEPE POTANSİYELİ\n"

            f"1.000 → "
            f"{fibler['1.000']:.2f} TL"
            f"  |  "
            f"{sonuc['tepe_potansiyel']:+.2f}%\n\n"

            f"🏦 Pazar: "
            f"{pazar_adi}\n"

            f"🔊 Hacim: "
            f"{sonuc['volume'] / 1_000_000:.1f}M"
        )

        if telegram_gonder(
            mesaj
        ):

            basariyla_gonderilenler.add(
                symbol
            )

    if basariyla_gonderilenler:

        gonderilenleri_kaydet(
            basariyla_gonderilenler
        )

    else:

        print(
            "Yeni gönderilen hisse yok."
        )


if __name__ == "__main__":

    main()
