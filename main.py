import os
import time
import requests
import pandas as pd
import borsapy as bp

from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================
# AYARLAR
# ============================================================

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GONDERILEN_DOSYA = "gonderilen_hisseler.txt"
AYLIK_MACD_DOSYA = "gonderilen_aylik_macd.txt"

EMA_PERIOD = 14
RSI_PERIOD = 14
BASE_PERIOD = 26
ADX_PERIOD = 14

EMA_MIN_DISTANCE = 0.02
FIB_LOOKBACK = 100

MAX_WORKERS = 4
MAX_RETRIES = 3

ISTANBUL = ZoneInfo("Europe/Istanbul")


# ============================================================
# ANA PAZAR
# ============================================================

ANA_PAZAR = {
    "A1CAP", "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES",
    "AFYON", "AGESA", "AGHOL", "AGROT", "AGYO", "AHGAZ",
    "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT",
    "AKMGY", "AKSA", "AKSEN", "AKSGY", "ALARK", "ALBRK",
    "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKIM", "ALKLC",
    "ALTNY", "ALVES", "ANELE", "ANGEN", "ANHYT", "ANSGR",
    "ARASE", "ARCLK", "ARDYZ", "ARENA", "ARSAN", "ARTMS",
    "ARZUM", "ASELS", "ASGYO", "ASTOR", "ATAGY", "ATAKP",
    "ATATP", "ATEKS", "AVGYO", "AVHOL", "AVOD", "AVPGY",
    "AYCES", "AYDEM", "AYEN", "AYES", "AYGAZ", "AZTEK",
    "BAGFS", "BAHKM", "BAKAB", "BALAT", "BANVT", "BARMA",
    "BASCM", "BASGZ", "BAYRK", "BEGYO", "BERA", "BEYAZ",
    "BFREN", "BIGEN", "BIGCH", "BIMAS", "BINBN", "BINHO",
    "BIOEN", "BIZIM", "BJKAS", "BLCYT", "BMSCH", "BMSTL",
    "BNTAS", "BOBET", "BORLS", "BORSK", "BOSSA", "BRISA",
    "BRKSN", "BRKVY", "BRLSM", "BRMEN", "BRSAN", "BRYAT",
    "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN",
    "BYDNR", "CANTE", "CASA", "CATES", "CCOLA", "CELHA",
    "CEMAS", "CEMTS", "CEMZY", "CEOEM", "CGCAM", "CIMSA",
    "CLEBI", "CMBTN", "CONSE", "COSMO", "CRDFA", "CRFSA",
    "CUSAN", "CVKMD", "CWENE", "DAGI", "DAPGM", "DARDL",
    "DCTTR", "DENGE", "DERHL", "DERIM", "DESA", "DESPC",
    "DEVA", "DGATE", "DGGYO", "DGNMO", "DITAS", "DMRGD",
    "DMSAS", "DNISI", "DOAS", "DOBUR", "DOCO", "DOFER",
    "DOGUB", "DOHOL", "DOKTA", "DSTKF", "DUNYH", "DYOBY",
    "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP",
    "EFORC", "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER",
    "EKGYO", "EKOS", "EKSUN", "ELITE", "EMKEL", "ENDAE",
    "ENERY", "ENJSA", "ENKAI", "ENSRI", "ENTRA", "ERBOS",
    "EREGL", "ERSU", "ESCAR", "ESCOM", "ESEN", "ETILR",
    "ETYAT", "EUHOL", "EUKYO", "EUPWR", "EUREN", "EUYO",
    "EYGYO", "FADE", "FENER", "FLAP", "FMIZP", "FONET",
    "FORMT", "FORTE", "FRIGO", "FROTO", "FZLGY", "GARAN",
    "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN",
    "GIPTA", "GLBMD", "GLCVY", "GLRMK", "GLYHO", "GMTAS",
    "GOKNR", "GOLTS", "GOODY", "GOZDE", "GRNYO", "GRSEL",
    "GRTHO", "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND",
    "HATEK", "HATSN", "HDFGS", "HEDEF", "HEKTS", "HKTM",
    "HLGYO", "HOROZ", "HRKET", "HTTBT", "HUBVC", "HUNER",
    "HURGZ", "ICBCT", "ICUGS", "IDGYO", "IEYHO", "IHAAS",
    "IHEVA", "IHGZT", "IHLAS", "IHLGM", "IHYAY", "IMASM",
    "INDES", "INFO", "INGRM", "INTEM", "INVEO", "INVES",
    "IPEKE", "ISATR", "ISBIR", "ISBTR", "ISCTR", "ISDMR",
    "ISFIN", "ISGSY", "ISGYO", "ISKPL", "ISKUR", "ISMEN",
    "ISSEN", "IZENR", "IZFAS", "IZINV", "IZMDC", "JANTS",
    "KAPLM", "KAREL", "KARSN", "KARTN", "KARYE", "KATMR",
    "KAYSE", "KBORU", "KCAER", "KCHOL", "KENT", "KERVT",
    "KFEIN", "KGYO", "KIMMR", "KLGYO", "KLKIM", "KLMSN",
    "KLRHO", "KLSER", "KLYPV", "KMPUR", "KNFRT", "KONKA",
    "KONTR", "KONYA", "KOPOL", "KORDS", "KOTON", "KOZAA",
    "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT",
    "KRPLS", "KRSTL", "KRTEK", "KRVGD", "KTSKR", "KUTPO",
    "KUYAS", "KZBGY", "LIDER", "LIDFA", "LINK", "LMKDC",
    "LOGO", "LRSHO", "LUKSK", "LYDHO", "LYDYE", "MAALT",
    "MACKO", "MAGEN", "MAKIM", "MAKTK", "MANAS", "MARBL",
    "MAVI", "MEDTR", "MEGMT", "MEKAG", "MEPET", "MERCN",
    "MERIT", "MERKO", "METRO", "MGROS", "MIATK", "MIPAZ",
    "MNDRS", "MNDTR", "MOBTL", "MOGAN", "MPARK", "MRGYO",
    "MRSHL", "MSGYO", "MTRKS", "MTRYO", "MZHLD", "NATEN",
    "NETAS", "NIBAS", "NTGAZ", "NTHOL", "NUHCM", "OBAMS",
    "ODAS", "ODINE", "OFSYM", "ONCSM", "ONRYT", "ORCAY",
    "ORGE", "OSMEN", "OSTIM", "OTKAR", "OTTO", "OYAKC",
    "OYAYO", "OYLUM", "OYYAT", "OZKGY", "OZRDN", "OZSUB",
    "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU", "PCILT",
    "PEGYO", "PEKGY", "PENTA", "PETKM", "PETUN", "PGSUS",
    "PINSU", "PKART", "PKENT", "PLTUR", "PNLSN", "PNSUT",
    "POLHO", "POLTK", "PRDGS", "PRKAB", "PRKME", "PSGYO",
    "QNBFL", "QNBTR", "QUAGR", "RALYH", "RAYSG", "REEDR",
    "RGYAS", "RNPOL", "RODRG", "RTALB", "RUBNS", "RUZYE",
    "SAFKR", "SAHOL", "SAMAT", "SANEL", "SANFM", "SANKO",
    "SARKY", "SASA", "SAYAS", "SDTTR", "SEGYO", "SEKFK",
    "SEKUR", "SELEC", "SELGD", "SELVA", "SEYKM", "SILVR",
    "SISE", "SKBNK", "SKTAS", "SMART", "SMRTG", "SNGYO",
    "SNICA", "SOKE", "SOKM", "SONME", "SRVGY", "SUMAS",
    "SUNTK", "SURGY", "SUWEN", "TABGD", "TARKM", "TATEN",
    "TATGD", "TAVHL", "TCELL", "TDGYO", "TEKTU", "TERA",
    "TEZOL", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TLMAN",
    "TMPOL", "TMSN", "TNZTP", "TOASO", "TRCAS", "TRGYO",
    "TRILC", "TSGYO", "TSKB", "TSPOR", "TTKOM", "TTRAK",
    "TUCLK", "TUKAS", "TUPRS", "TUREX", "TURGG", "TURSG",
    "UFUK", "ULAS", "ULKER", "ULUSE", "ULUUN", "UNLU",
    "USAK", "VAKBN", "VAKFN", "VAKKO", "VANGD", "VERTU",
    "VERUS", "VESBE", "VESTL", "VKFYO", "VKGYO", "VKING",
    "VRGYO", "YAPRK", "YATAS", "YAYLA", "YBTAS", "YEOTK",
    "YESIL", "YGGYO", "YKBNK", "YKSLN", "YONGA", "YUNSA",
    "YYAPI", "YYLGD", "ZEDUR", "ZOREN"
}


# ============================================================
# GÜNLÜK GÖNDERİLENLER
# ============================================================

def gonderilenleri_oku():
    if not os.path.exists(GONDERILEN_DOSYA):
        return set()

    sonuc = set()
    bugun = datetime.now(ISTANBUL).strftime("%Y-%m-%d")

    try:
        with open(GONDERILEN_DOSYA, "r", encoding="utf-8") as f:
            for satir in f:
                satir = satir.strip()

                if not satir:
                    continue

                parcalar = satir.split("|")

                if len(parcalar) >= 2:
                    if parcalar[0] == bugun:
                        sonuc.add(parcalar[1])

    except Exception as e:
        print("Günlük gönderilen dosyası okunamadı:", e)

    return sonuc


def gonderilen_kaydet(symbol):
    bugun = datetime.now(ISTANBUL).strftime("%Y-%m-%d")

    try:
        with open(GONDERILEN_DOSYA, "a", encoding="utf-8") as f:
            f.write(f"{bugun}|{symbol}\n")

    except Exception as e:
        print("Günlük gönderim kaydı yazılamadı:", e)


# ============================================================
# AYLIK MACD KAYIT
# ============================================================

def aylik_macd_kayitlari_oku():
    if not os.path.exists(AYLIK_MACD_DOSYA):
        return set()

    sonuc = set()

    try:
        with open(AYLIK_MACD_DOSYA, "r", encoding="utf-8") as f:
            for satir in f:
                satir = satir.strip()

                if satir:
                    sonuc.add(satir)

    except Exception as e:
        print("Aylık MACD kayıt dosyası okunamadı:", e)

    return sonuc


def aylik_macd_kaydet(sinyal_tipi, symbol, ay):
    anahtar = f"{sinyal_tipi}|{symbol}|{ay}"

    try:
        with open(AYLIK_MACD_DOSYA, "a", encoding="utf-8") as f:
            f.write(anahtar + "\n")

    except Exception as e:
        print("Aylık MACD kayıt yazılamadı:", e)


# ============================================================
# TELEGRAM
# ============================================================

def telegram_gonder(mesaj):
    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": mesaj
    }

    for deneme in range(MAX_RETRIES):
        try:
            response = requests.post(
                url,
                data=payload,
                timeout=20
            )

            if response.status_code == 200:
                return True

            print(
                "Telegram hata:",
                response.status_code,
                response.text
            )

        except Exception as e:
            print(
                f"Telegram gönderim hatası "
                f"({deneme + 1}/{MAX_RETRIES}):",
                e
            )

        time.sleep(2)

    return False


# ============================================================
# SAYISAL VERİ TEMİZLEME
# ============================================================

def numeric_temizle(df, kolonlar):
    """
    Borsapy / TradingView'den gelen object, pd.NA,
    string veya bozuk değerleri numeric hale getirir.
    """

    df = df.copy()

    for kolon in kolonlar:
        if kolon in df.columns:
            df[kolon] = pd.to_numeric(
                df[kolon],
                errors="coerce"
            )

    return df


# ============================================================
# VERİ GEÇERLİ Mİ?
# ============================================================

def veri_gecerli_mi(df, kolonlar, minimum):
    if df is None or df.empty:
        return False

    for kolon in kolonlar:
        if kolon not in df.columns:
            return False

    df = numeric_temizle(
        df,
        kolonlar
    )

    df = df.dropna(
        subset=kolonlar
    )

    return len(df) >= minimum


# ============================================================
# PİYASA AÇIK MI
# ============================================================

def piyasa_acik_mi():
    simdi = datetime.now(ISTANBUL)

    if simdi.weekday() >= 5:
        return False

    dakika = simdi.hour * 60 + simdi.minute

    acilis = 9 * 60 + 40
    kapanis = 18 * 60 + 10

    return acilis <= dakika <= kapanis


# ============================================================
# BIST100
# ============================================================

def bist100_listesi():
    try:
        index = bp.Index("XU100")

        semboller = index.component_symbols

        if not semboller:
            return set()

        return {
            str(x).upper().replace(".IS", "")
            for x in semboller
        }

    except Exception as e:
        print("BIST100 alınamadı:", e)
        return set()


# ============================================================
# RSI
# ============================================================

def rsi_hesapla(close, period=14):
    close = pd.to_numeric(
        close,
        errors="coerce"
    )

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    avg_loss = avg_loss.replace(
        0,
        float("nan")
    )

    rs = avg_gain / avg_loss

    rsi = 100 - (
        100 / (1 + rs)
    )

    return pd.to_numeric(
        rsi,
        errors="coerce"
    )


# ============================================================
# ADX
# ============================================================

def adx_hesapla(df, period=14):
    high = pd.to_numeric(
        df["High"],
        errors="coerce"
    )

    low = pd.to_numeric(
        df["Low"],
        errors="coerce"
    )

    close = pd.to_numeric(
        df["Close"],
        errors="coerce"
    )

    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(
        0.0,
        index=df.index
    )

    minus_dm = pd.Series(
        0.0,
        index=df.index
    )

    plus_mask = (
        (up_move > down_move) &
        (up_move > 0)
    )

    minus_mask = (
        (down_move > up_move) &
        (down_move > 0)
    )

    plus_dm.loc[plus_mask] = up_move.loc[plus_mask]
    minus_dm.loc[minus_mask] = down_move.loc[minus_mask]

    atr = tr.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    atr_safe = atr.replace(
        0,
        float("nan")
    )

    plus_di = (
        100 *
        plus_dm.ewm(
            alpha=1 / period,
            adjust=False
        ).mean() /
        atr_safe
    )

    minus_di = (
        100 *
        minus_dm.ewm(
            alpha=1 / period,
            adjust=False
        ).mean() /
        atr_safe
    )

    di_sum = (
        plus_di + minus_di
    ).replace(
        0,
        float("nan")
    )

    dx = (
        100 *
        (plus_di - minus_di).abs() /
        di_sum
    )

    adx = dx.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    return pd.to_numeric(
        adx,
        errors="coerce"
    )


def adx_gosterge(adx):
    if pd.isna(adx):
        return "⚪"

    if adx >= 25:
        return "🟢"

    return "⚪"


# ============================================================
# GÜNLÜK VERİ
# ============================================================

def veri_al(symbol):

    for deneme in range(MAX_RETRIES):

        try:

            ticker = bp.Ticker(symbol)

            df = ticker.history(
                period="6mo",
                interval="1d"
            )

            if df is None or df.empty:
                raise ValueError(
                    "Boş veri"
                )

            df = df.copy()

            gerekli = [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]

            df = numeric_temizle(
                df,
                gerekli
            )

            df = df.dropna(
                subset=gerekli
            )

            if len(df) >= 60:
                return df

            raise ValueError(
                f"Yetersiz veri: {len(df)}"
            )

        except Exception as e:

            print(
                f"{symbol} günlük veri hatası "
                f"({deneme + 1}/{MAX_RETRIES}): {e}"
            )

            if deneme < MAX_RETRIES - 1:
                time.sleep(1)

    return None


# ============================================================
# FIBONACCI
# ============================================================

def fibonacci_hesapla(df, lookback=100):

    if len(df) < lookback:
        return None

    fib_df = df.tail(
        lookback
    ).copy()

    fib_df["High"] = pd.to_numeric(
        fib_df["High"],
        errors="coerce"
    )

    fib_df["Low"] = pd.to_numeric(
        fib_df["Low"],
        errors="coerce"
    )

    fib_df = fib_df.dropna(
        subset=["High", "Low"]
    )

    if len(fib_df) < lookback:
        return None

    try:
        fib_high = float(
            fib_df["High"].max()
        )

        fib_low = float(
            fib_df["Low"].min()
        )

    except Exception:
        return None

    if pd.isna(fib_high) or pd.isna(fib_low):
        return None

    fib_range = fib_high - fib_low

    if fib_range <= 0:
        return None

    high_values = fib_df["High"].tolist()
    low_values = fib_df["Low"].tolist()

    high_offset = None
    low_offset = None

    for i in range(
        len(high_values) - 1,
        -1,
        -1
    ):

        try:
            if float(high_values[i]) == fib_high:
                high_offset = (
                    len(high_values) - 1 - i
                )
                break
        except Exception:
            continue

    for i in range(
        len(low_values) - 1,
        -1,
        -1
    ):

        try:
            if float(low_values[i]) == fib_low:
                low_offset = (
                    len(low_values) - 1 - i
                )
                break
        except Exception:
            continue

    if high_offset is None or low_offset is None:
        return None

    revfibs = low_offset > high_offset

    oranlar = [
        0.000,
        0.236,
        0.382,
        0.500,
        0.618,
        0.786,
        1.000
    ]

    seviyeler = {}

    if revfibs:

        for oran in oranlar:

            seviyeler[oran] = (
                fib_low +
                fib_range * oran
            )

    else:

        for oran in oranlar:

            seviyeler[oran] = (
                fib_high -
                fib_range * oran
            )

    return {
        "high": fib_high,
        "low": fib_low,
        "levels": seviyeler
    }


# ============================================================
# PINE RSI
# ============================================================

def pine_rsi(series, length):

    series = pd.to_numeric(
        series,
        errors="coerce"
    )

    delta = series.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.ewm(
        alpha=1 / length,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / length,
        adjust=False
    ).mean()

    avg_loss = avg_loss.replace(
        0,
        float("nan")
    )

    rs = avg_gain / avg_loss

    return 100 - (
        100 / (1 + rs)
    )


# ============================================================
# QQE MOD
# ============================================================

def calculate_qqe(
    source,
    rsi_length,
    smoothing,
    qqe_factor
):

    wilders_length = (
        rsi_length * 2 - 1
    )

    rsi = pine_rsi(
        source,
        rsi_length
    )

    smoothed_rsi = rsi.ewm(
        span=smoothing,
        adjust=False
    ).mean()

    atr_rsi = (
        smoothed_rsi.shift(1) -
        smoothed_rsi
    ).abs()

    smoothed_atr_rsi = atr_rsi.ewm(
        span=wilders_length,
        adjust=False
    ).mean()

    dynamic_atr_rsi = (
        smoothed_atr_rsi *
        qqe_factor
    )

    long_band = pd.Series(
        index=source.index,
        dtype=float
    )

    short_band = pd.Series(
        index=source.index,
        dtype=float
    )

    trend_direction = pd.Series(
        index=source.index,
        dtype=float
    )

    trend_line = pd.Series(
        index=source.index,
        dtype=float
    )

    for i in range(len(source)):

        current_rsi = smoothed_rsi.iloc[i]
        current_atr = dynamic_atr_rsi.iloc[i]

        if pd.isna(current_rsi):
            continue

        if pd.isna(current_atr):
            current_atr = 0.0

        if i == 0:

            long_band.iloc[i] = (
                current_rsi -
                current_atr
            )

            short_band.iloc[i] = (
                current_rsi +
                current_atr
            )

            trend_direction.iloc[i] = 1

            trend_line.iloc[i] = (
                long_band.iloc[i]
            )

            continue

        prev_long = long_band.iloc[i - 1]
        prev_short = short_band.iloc[i - 1]
        prev_rsi = smoothed_rsi.iloc[i - 1]

        if pd.isna(prev_long):
            prev_long = (
                current_rsi -
                current_atr
            )

        if pd.isna(prev_short):
            prev_short = (
                current_rsi +
                current_atr
            )

        if pd.isna(prev_rsi):
            prev_rsi = current_rsi

        new_long = (
            current_rsi -
            current_atr
        )

        new_short = (
            current_rsi +
            current_atr
        )

        if (
            current_rsi > prev_long and
            prev_rsi > prev_long
        ):

            long_band.iloc[i] = max(
                prev_long,
                new_long
            )

        else:

            long_band.iloc[i] = new_long

        if (
            current_rsi < prev_short and
            prev_rsi < prev_short
        ):

            short_band.iloc[i] = min(
                prev_short,
                new_short
            )

        else:

            short_band.iloc[i] = new_short

        direction = trend_direction.iloc[i - 1]

        if pd.isna(direction):
            direction = 1

        cross_up = (
            current_rsi > prev_short and
            prev_rsi <= prev_short
        )

        cross_down = (
            current_rsi < prev_long and
            prev_rsi >= prev_long
        )

        if cross_up:
            direction = 1

        elif cross_down:
            direction = -1

        trend_direction.iloc[i] = direction

        if direction == 1:

            trend_line.iloc[i] = (
                long_band.iloc[i]
            )

        else:

            trend_line.iloc[i] = (
                short_band.iloc[i]
            )

    return (
        rsi,
        smoothed_rsi,
        trend_line
    )


def qqe_hesapla(df):

    source = pd.to_numeric(
        df["Close"],
        errors="coerce"
    )

    (
        primary_rsi_raw,
        primary_rsi,
        primary_trend_line
    ) = calculate_qqe(
        source,
        6,
        5,
        3.0
    )

    (
        secondary_rsi_raw,
        secondary_rsi,
        secondary_trend_line
    ) = calculate_qqe(
        source,
        6,
        5,
        1.61
    )

    bollinger_source = (
        primary_trend_line - 50
    )

    basis = bollinger_source.rolling(
        50,
        min_periods=20
    ).mean()

    deviation = (
        bollinger_source.rolling(
            50,
            min_periods=20
        ).std() * 0.35
    )

    bollinger_upper = (
        basis + deviation
    )

    bollinger_lower = (
        basis - deviation
    )

    primary_renk = pd.Series(
        "GRI",
        index=df.index,
        dtype=object
    )

    mavi_mask = (
        (primary_rsi - 50) >
        bollinger_upper
    )

    kirmizi_mask = (
        (primary_rsi - 50) <
        bollinger_lower
    )

    primary_renk.loc[mavi_mask] = "MAVI"
    primary_renk.loc[kirmizi_mask] = "KIRMIZI"

    secondary_hist = (
        secondary_rsi - 50
    )

    yeni_mavi = (
        (secondary_hist > 3) &
        (primary_rsi - 50 > bollinger_upper)
    )

    yeni_kirmizi = (
        (secondary_hist < -3) &
        (primary_rsi - 50 < bollinger_lower)
    )

    return {
        "primary_rsi": primary_rsi,
        "secondary_rsi": secondary_rsi,
        "primary_trend_line": primary_trend_line,
        "bollinger_upper": bollinger_upper,
        "bollinger_lower": bollinger_lower,
        "qqe_mavi": mavi_mask,
        "qqe_kirmizi": kirmizi_mask,
        "qqe_yeni_mavi": yeni_mavi,
        "qqe_yeni_kirmizi": yeni_kirmizi,
        "qqe_renk": primary_renk
    }


def qqe_renk_goster(renk):

    if renk == "MAVI":
        return "🔵 QQE: MAVİ"

    if renk == "KIRMIZI":
        return "🔴 QQE: KIRMIZI"

    return "⚪ QQE: GRİ"


# ============================================================
# GÜNLÜK ANALİZ
# ============================================================

def analiz_et(symbol, sadece_sinyal=False):

    try:

        df = veri_al(symbol)

        if df is None or len(df) < 60:
            return None

        df = numeric_temizle(
            df,
            [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]
        )

        df = df.dropna(
            subset=[
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]
        )

        if len(df) < 60:
            return None

        close = df["Close"]

        ema = close.ewm(
            span=EMA_PERIOD,
            adjust=False
        ).mean()

        rsi = rsi_hesapla(
            close,
            RSI_PERIOD
        )

        adx = adx_hesapla(
            df,
            ADX_PERIOD
        )

        base = (
            df["High"].rolling(
                BASE_PERIOD
            ).max()
            +
            df["Low"].rolling(
                BASE_PERIOD
            ).min()
        ) / 2

        qqe = qqe_hesapla(df)

        # ----------------------------------------------------
        # SON DEĞERLER
        # ----------------------------------------------------

        values = [
            close.iloc[-1],
            close.iloc[-2],
            ema.iloc[-1],
            ema.iloc[-2],
            rsi.iloc[-1],
            rsi.iloc[-2],
            base.iloc[-1],
            base.iloc[-2],
            adx.iloc[-1]
        ]

        if any(
            pd.isna(x)
            for x in values
        ):
            return None

        son_close = float(
            close.iloc[-1]
        )

        onceki_close = float(
            close.iloc[-2]
        )

        son_ema = float(
            ema.iloc[-1]
        )

        onceki_ema = float(
            ema.iloc[-2]
        )

        son_rsi = float(
            rsi.iloc[-1]
        )

        onceki_rsi = float(
            rsi.iloc[-2]
        )

        son_base = float(
            base.iloc[-1]
        )

        onceki_base = float(
            base.iloc[-2]
        )

        son_adx = float(
            adx.iloc[-1]
        )

        # ====================================================
        # GÜNLÜK ANA KRİTERLER
        # ====================================================

        base_yukari_kesti = (
            onceki_base >= onceki_close and
            son_base < son_close
        )

        ema_mesafe = (
            son_close >=
            son_ema *
            (1 + EMA_MIN_DISTANCE)
        )

        ema_yukseliyor = (
            son_ema > onceki_ema
        )

        rsi_yukari_kesti = (
            onceki_rsi <= 50 and
            son_rsi > 50
        )

        rsi_yukseliyor = (
            son_rsi > onceki_rsi
        )

        # ----------------------------------------------------
        # GÜNLÜK FİLTRE
        # ----------------------------------------------------

        if not sadece_sinyal:

            if not (
                base_yukari_kesti and
                ema_mesafe and
                ema_yukseliyor and
                rsi_yukari_kesti and
                rsi_yukseliyor
            ):
                return None

        # ====================================================
        # FIB
        # ====================================================

        fib = fibonacci_hesapla(
            df,
            FIB_LOOKBACK
        )

        if fib is None:
            return None

        seviyeler = fib["levels"]

        # ====================================================
        # STOP
        # ====================================================

        stop = None
        stop_oran = None

        alttaki = []

        for oran, seviye in seviyeler.items():

            if seviye < son_close:
                alttaki.append(
                    (oran, seviye)
                )

        if alttaki:

            stop_oran, stop = max(
                alttaki,
                key=lambda x: x[1]
            )

        # ====================================================
        # FİYAT FIB
        # ====================================================

        fiyat_fib_oran, fiyat_fib = min(
            seviyeler.items(),
            key=lambda x: abs(
                x[1] - son_close
            )
        )

        # ====================================================
        # TEPE
        # ====================================================

        tepe = seviyeler.get(
            1.000
        )

        if tepe is not None:

            tepe_potansiyel = (
                (tepe / son_close) - 1
            ) * 100

        else:

            tepe_potansiyel = 0

        # ====================================================
        # GÜNLÜK DEĞİŞİM
        # ====================================================

        if len(close) >= 2:

            gunluk_yuzde = (
                (son_close /
                 float(close.iloc[-2])) - 1
            ) * 100

        else:

            gunluk_yuzde = 0

        # ====================================================
        # HAFTALIK
        # ====================================================

        if len(close) >= 6:

            haftalik_yuzde = (
                (son_close /
                 float(close.iloc[-6])) - 1
            ) * 100

        else:

            haftalik_yuzde = 0

        # ====================================================
        # HACİM
        # ====================================================

        volume = pd.to_numeric(
            df["Volume"],
            errors="coerce"
        )

        ort_hacim = (
            volume
            .rolling(
                20,
                min_periods=1
            )
            .mean()
            .iloc[-1]
        )

        hacim = volume.iloc[-1]

        if pd.isna(hacim):
            return None

        hacim = float(hacim)

        if pd.isna(ort_hacim):
            ort_hacim = hacim
        else:
            ort_hacim = float(ort_hacim)

        # ====================================================
        # QQE
        # ====================================================

        qqe_renk = qqe[
            "qqe_renk"
        ].iloc[-1]

        if pd.isna(qqe_renk):
            qqe_renk = "GRI"

        return {
            "symbol": symbol,
            "fiyat": son_close,

            "gunluk_yuzde": gunluk_yuzde,
            "haftalik_yuzde": haftalik_yuzde,

            "ema": son_ema,

            "ema_yuzde": (
                (son_close / son_ema) - 1
            ) * 100,

            "rsi": son_rsi,
            "adx": son_adx,

            "fib": seviyeler,

            "fiyat_fib_oran": fiyat_fib_oran,
            "fiyat_fib": fiyat_fib,

            "stop_oran": stop_oran,
            "stop": stop,

            "tepe": tepe,
            "tepe_potansiyel": tepe_potansiyel,

            "hacim": hacim,
            "ort_hacim": ort_hacim,

            "qqe_renk": qqe_renk
        }

    except Exception as e:

        print(
            f"{symbol} analiz hatası: {e}"
        )

        return None


# ============================================================
# YÜZDE MESAFE
# ============================================================

def yuzde_mesafe(seviye, fiyat):

    if fiyat == 0:
        return 0

    return (
        (seviye / fiyat) - 1
    ) * 100


# ============================================================
# FIB SATIRI
# ============================================================

def fib_satiri(oran, seviye, fiyat):

    yuzde = yuzde_mesafe(
        seviye,
        fiyat
    )

    if seviye <= fiyat:
        ikon = "🟢 ➜"
    else:
        ikon = "   "

    return (
        f"{ikon} {oran:.3f} → "
        f"{seviye:.2f} TL  |  "
        f"{yuzde:+.2f}%"
    )


# ============================================================
# TELEGRAM MESAJ
# ============================================================

def mesaj_olustur(
    sonuc,
    baslik
):

    symbol = sonuc["symbol"]
    fiyat = sonuc["fiyat"]
    adx = sonuc["adx"]

    adx_ikon = adx_gosterge(
        adx
    )

    qqe_durum = qqe_renk_goster(
        sonuc["qqe_renk"]
    )

    pazar = (
        "Ana Pazar"
        if symbol in ANA_PAZAR
        else "BIST100"
    )

    mesaj = (
        f"{baslik} : {symbol:<20} "
        f"ADX {adx_ikon} {adx:.1f}\n\n"

        f"💰 Giriş: {fiyat:.2f} TL"
        f"{' ' * 18}"
        f"{qqe_durum}\n"

        f"🟢 Günlük: "
        f"{sonuc['gunluk_yuzde']:+.2f}%\n"

        f"🟢 1 Hafta: "
        f"{sonuc['haftalik_yuzde']:+.2f}%\n\n"

        f"📏 EMA14: "
        f"{sonuc['ema']:.2f} TL "
        f"({sonuc['ema_yuzde']:+.2f}%)\n"

        f"📊 RSI: "
        f"{sonuc['rsi']:.1f}\n\n"

        f"📐 FIB SEVİYELERİ\n\n"
    )

    for oran in sorted(
        sonuc["fib"].keys(),
        reverse=True
    ):

        seviye = sonuc["fib"][oran]

        mesaj += (
            f"{fib_satiri(oran, seviye, fiyat)}\n"
        )

    mesaj += "\n🛑 STOP\n"

    if sonuc["stop"] is not None:

        mesaj += (
            f"{sonuc['stop_oran']:.3f} → "
            f"{sonuc['stop']:.2f} TL\n"
        )

    else:

        mesaj += "Yok\n"

    mesaj += (
        "\n🎯 TEPE POTANSİYELİ\n"
    )

    if sonuc["tepe"] is not None:

        mesaj += (
            f"1.000 → "
            f"{sonuc['tepe']:.2f} TL  |  "
            f"{sonuc['tepe_potansiyel']:+.2f}%\n"
        )

    else:

        mesaj += "Yok\n"

    mesaj += (
        f"\n🏦 Pazar: {pazar}\n"

        f"🔊 Hacim: "
        f"{sonuc['hacim'] / 1_000_000:.1f}M"
    )

    return mesaj


# ============================================================
# AYLIK VERİ
# ============================================================

def aylik_veri_al(symbol):

    for deneme in range(
        MAX_RETRIES
    ):

        try:

            ticker = bp.Ticker(symbol)

            df = ticker.history(
                period="5y",
                interval="1mo"
            )

            if df is None or df.empty:
                raise ValueError(
                    "Boş aylık veri"
                )

            df = df.copy()

            df = numeric_temizle(
                df,
                ["Close"]
            )

            df = df.dropna(
                subset=["Close"]
            )

            if len(df) >= 40:
                return df

            raise ValueError(
                f"Yetersiz aylık veri: {len(df)}"
            )

        except Exception as e:

            print(
                f"{symbol} aylık veri hatası "
                f"({deneme + 1}/{MAX_RETRIES}): {e}"
            )

            if deneme < MAX_RETRIES - 1:
                time.sleep(1)

    return None


# ============================================================
# AYLIK MACD
# ============================================================

def aylik_macd_hesapla(df):

    close = pd.to_numeric(
        df["Close"],
        errors="coerce"
    )

    ema12 = close.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False
    ).mean()

    macd = ema12 - ema26

    signal = macd.ewm(
        span=9,
        adjust=False
    ).mean()

    return macd, signal


# ============================================================
# AYLIK MACD SİNYAL
# ============================================================

def aylik_macd_sinyal(symbol):

    try:

        df = aylik_veri_al(
            symbol
        )

        if df is None or len(df) < 40:
            return None

        df = df.copy()

        try:

            df.index = pd.to_datetime(
                df.index
            )

        except Exception:
            pass

        macd, signal = aylik_macd_hesapla(
            df
        )

        df["MACD"] = pd.to_numeric(
            macd,
            errors="coerce"
        )

        df["SIGNAL"] = pd.to_numeric(
            signal,
            errors="coerce"
        )

        df = df.dropna(
            subset=[
                "MACD",
                "SIGNAL"
            ]
        )

        if len(df) < 3:
            return None

        simdi = datetime.now(
            ISTANBUL
        )

        son_index = df.index[-1]

        son_ay_canli = False

        try:

            son_ay_canli = (
                son_index.year == simdi.year and
                son_index.month == simdi.month
            )

        except Exception:
            pass

        son = df.iloc[-1]
        onceki = df.iloc[-2]
        iki_onceki = df.iloc[-3]

        try:

            ay_etiketi = (
                f"{son_index.year:04d}-"
                f"{son_index.month:02d}"
            )

        except Exception:

            ay_etiketi = simdi.strftime(
                "%Y-%m"
            )

        sayisal = [
            son["MACD"],
            onceki["MACD"],
            iki_onceki["MACD"],
            son["SIGNAL"],
            onceki["SIGNAL"]
        ]

        if any(
            pd.isna(x)
            for x in sayisal
        ):
            return None

        son_macd = float(
            son["MACD"]
        )

        onceki_macd = float(
            onceki["MACD"]
        )

        iki_onceki_macd = float(
            iki_onceki["MACD"]
        )

        son_signal = float(
            son["SIGNAL"]
        )

        onceki_signal = float(
            onceki["SIGNAL"]
        )

        # ====================================================
        # 🟢 AYLIK
        #
        # MACD Signal'ı yukarı kesiyor
        # ====================================================

        aylik_al = (
            onceki_macd <= onceki_signal and
            son_macd > son_signal
        )

        # ====================================================
        # 🟠 AYLIK ÜSTÜNE ATTI
        # ====================================================

        aylik_ustune_atti = (
            son_macd > onceki_macd and
            onceki_macd <= iki_onceki_macd
        )

        return {
            "symbol": symbol,
            "ay": ay_etiketi,

            "aylik_al": aylik_al,

            "aylik_ustune_atti":
                aylik_ustune_atti,

            "macd": son_macd,
            "signal": son_signal,

            "onceki_macd":
                onceki_macd,

            "iki_onceki_macd":
                iki_onceki_macd,

            "canli_ay":
                son_ay_canli
        }

    except Exception as e:

        print(
            f"{symbol} aylık MACD analiz hatası: {e}"
        )

        return None


# ============================================================
# TARAMA LİSTESİ
# ============================================================

def tarama_listesi_olustur():

    bist100 = bist100_listesi()

    liste = set()

    liste.update(
        bist100
    )

    liste.update(
        ANA_PAZAR
    )

    return sorted(
        liste
    )


# ============================================================
# AYLIK MESAJ DETAY
# ============================================================

def aylik_mesaj_detay(symbol):

    return analiz_et(
        symbol,
        sadece_sinyal=True
    )


# ============================================================
# AYLIK TARAMA
# ============================================================

def aylik_macd_tarama(
    tarama_listesi
):

    print(
        f"\n📅 Aylık MACD taraması başladı. "
        f"{len(tarama_listesi)} hisse..."
    )

    kayitlar = (
        aylik_macd_kayitlari_oku()
    )

    sinyaller = []

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                aylik_macd_sinyal,
                symbol
            ): symbol

            for symbol in tarama_listesi
        }

        tamamlanan = 0
        toplam = len(futures)

        for future in as_completed(
            futures
        ):

            symbol = futures[future]

            tamamlanan += 1

            try:

                sonuc = future.result()

                if sonuc is None:
                    continue

                ay = sonuc["ay"]

                # =================================================
                # 🟢 AYLIK
                # =================================================

                if sonuc["aylik_al"]:

                    anahtar = (
                        f"AYLIK_MACD_AL|"
                        f"{symbol}|"
                        f"{ay}"
                    )

                    if anahtar not in kayitlar:

                        sinyaller.append(
                            (
                                "AYLIK",
                                symbol,
                                ay
                            )
                        )

                # =================================================
                # 🟠 AYLIK ÜSTÜNE ATTI
                # =================================================

                if sonuc["aylik_ustune_atti"]:

                    anahtar = (
                        f"AYLIK_MACD_USTUNE|"
                        f"{symbol}|"
                        f"{ay}"
                    )

                    if anahtar not in kayitlar:

                        sinyaller.append(
                            (
                                "AYLIK ÜSTÜNE ATTI",
                                symbol,
                                ay
                            )
                        )

            except Exception as e:

                print(
                    f"{symbol} aylık sonuç hatası: {e}"
                )

            if tamamlanan % 25 == 0:

                print(
                    f"Aylık tarama: "
                    f"{tamamlanan}/{toplam}"
                )

    # ============================================================
    # GÖNDER
    # ============================================================

    for (
        sinyal_tipi,
        symbol,
        ay
    ) in sinyaller:

        detay = aylik_mesaj_detay(
            symbol
        )

        if detay is None:

            print(
                f"⚠️ {symbol} aylık sinyal var "
                f"ama mesaj detayları alınamadı."
            )

            continue

        if sinyal_tipi == "AYLIK":

            baslik = "🟢 AYLIK"

        else:

            baslik = "🟠 AYLIK ÜSTÜNE ATTI"

        mesaj = mesaj_olustur(
            detay,
            baslik
        )

        print(
            f"\nAYLIK SİNYAL: "
            f"{sinyal_tipi} - {symbol}"
        )

        if telegram_gonder(mesaj):

            if sinyal_tipi == "AYLIK":

                aylik_macd_kaydet(
                    "AYLIK_MACD_AL",
                    symbol,
                    ay
                )

            else:

                aylik_macd_kaydet(
                    "AYLIK_MACD_USTUNE",
                    symbol,
                    ay
                )

            print(
                f"✅ Telegram gönderildi: "
                f"{sinyal_tipi} {symbol}"
            )

        else:

            print(
                f"❌ Telegram gönderilemedi: "
                f"{sinyal_tipi} {symbol}"
            )


# ============================================================
# ANA
# ============================================================

def main():

    simdi = datetime.now(
        ISTANBUL
    )

    print(
        "\n========================================"
    )

    print(
        "BIST TARAMA BOTU BAŞLADI"
    )

    print(
        f"Türkiye saati: "
        f"{simdi.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        "========================================"
    )

    # --------------------------------------------------------
    # PİYASA KAPALIYSA BU ÇALIŞMADA ÇIK
    # --------------------------------------------------------

    if not piyasa_acik_mi():

        print(
            "⏸ Piyasa kapalı. "
            "Bu çalışma sonlandırılıyor."
        )

        return

    # ========================================================
    # LİSTE
    # ========================================================

    tarama_listesi = (
        tarama_listesi_olustur()
    )

    print(
        f"Toplam taranacak hisse: "
        f"{len(tarama_listesi)}"
    )

    # ========================================================
    # GÜNLÜK GÖNDERİLENLER
    # ========================================================

    gonderilenler = (
        gonderilenleri_oku()
    )

    print(
        f"Bugün gönderilmiş günlük hisse: "
        f"{len(gonderilenler)}"
    )

    # ========================================================
    # GÜNLÜK TARAMA
    # ========================================================

    print(
        "\n📊 Günlük tarama başladı..."
    )

    bulunanlar = []

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                analiz_et,
                symbol
            ): symbol

            for symbol in tarama_listesi
        }

        tamamlanan = 0
        toplam = len(futures)

        for future in as_completed(
            futures
        ):

            symbol = futures[future]

            tamamlanan += 1

            try:

                sonuc = future.result()

                if sonuc is not None:

                    bulunanlar.append(
                        sonuc
                    )

                    print(
                        f"🟢 GÜNLÜK ADAY: "
                        f"{symbol}"
                    )

            except Exception as e:

                print(
                    f"{symbol} günlük sonuç hatası: "
                    f"{e}"
                )

            if tamamlanan % 25 == 0:

                print(
                    f"Günlük tarama: "
                    f"{tamamlanan}/{toplam}"
                )

    # ========================================================
    # GÜNLÜK TELEGRAM
    # ========================================================

    print(
        f"\nGünlük bulunan sinyal: "
        f"{len(bulunanlar)}"
    )

    for sonuc in bulunanlar:

        symbol = sonuc["symbol"]

        if symbol in gonderilenler:

            print(
                f"⏭ Daha önce gönderildi: "
                f"{symbol}"
            )

            continue

        mesaj = mesaj_olustur(
            sonuc,
            "🟢 YENİ"
        )

        print(
            f"\n📤 Günlük gönderiliyor: "
            f"{symbol}"
        )

        if telegram_gonder(mesaj):

            gonderilen_kaydet(
                symbol
            )

            gonderilenler.add(
                symbol
            )

            print(
                f"✅ Günlük gönderildi: "
                f"{symbol}"
            )

        else:

            print(
                f"❌ Günlük gönderilemedi: "
                f"{symbol}"
            )

    # ========================================================
    # AYLIK MACD
    # ========================================================

    aylik_macd_tarama(
        tarama_listesi
    )

    print(
        "\n========================================"
    )

    print(
        "TARAMA TAMAMLANDI"
    )

    print(
        "========================================"
    )


# ============================================================
# ÇALIŞTIR
# ============================================================

if __name__ == "__main__":
    main()
