import borsapy as bp
import pandas as pd

print("====================================")
print("BIST HISSE TARAMA BASLADI")
print("====================================")


# -------------------------------------------------
# AYARLAR
# -------------------------------------------------

EMA_PERIYOT = 14
RSI_PERIYOT = 14

ICHIMOKU_TENKAN = 9
ICHIMOKU_KIJUN = 26
ICHIMOKU_SENKOU = 52


# -------------------------------------------------
# RSI
# -------------------------------------------------

def hesapla_rsi(df, periyot=14):

    delta = df["Close"].diff()

    kazanc = delta.clip(lower=0)
    kayip = -delta.clip(upper=0)

    ort_kazanc = kazanc.ewm(
        alpha=1 / periyot,
        adjust=False
    ).mean()

    ort_kayip = kayip.ewm(
        alpha=1 / periyot,
        adjust=False
    ).mean()

    rs = ort_kazanc / ort_kayip

    return 100 - (100 / (1 + rs))


# -------------------------------------------------
# ICHIMOKU BASE LINE
# -------------------------------------------------

def hesapla_base_line(df):

    en_yuksek = df["High"].rolling(
        ICHIMOKU_KIJUN
    ).max()

    en_dusuk = df["Low"].rolling(
        ICHIMOKU_KIJUN
    ).min()

    return (en_yuksek + en_dusuk) / 2


# -------------------------------------------------
# HISSE ANALIZI
# -------------------------------------------------

def hisse_analiz(symbol):

    try:

        ticker = bp.Ticker(symbol)

        df = ticker.history(period="6mo")

        if df is None or len(df) < 60:
            return None

        df = df.copy()

        # EMA 14
        df["EMA14"] = df["Close"].ewm(
            span=EMA_PERIYOT,
            adjust=False
        ).mean()

        # RSI 14
        df["RSI14"] = hesapla_rsi(
            df,
            RSI_PERIYOT
        )

        # Ichimoku Base Line
        df["BASE"] = hesapla_base_line(df)

        onceki = df.iloc[-2]
        son = df.iloc[-1]

        fiyat = float(son["Close"])

        # -----------------------------------------
        # 1 - BASE LINE FIYATI ASAGI KESIYOR
        # -----------------------------------------

        ichimoku_sart = (
            onceki["Close"] >= onceki["BASE"]
            and
            son["Close"] < son["BASE"]
        )

        # -----------------------------------------
        # 2 - FIYAT EMA14'UN EN AZ %3 UZERINDE
        # -----------------------------------------

        ema_sart = (
            fiyat >= float(son["EMA14"]) * 1.03
        )

        # -----------------------------------------
        # 3 - RSI > 50
        # -----------------------------------------

        rsi_sart = (
            float(son["RSI14"]) > 50
        )

        if ichimoku_sart and ema_sart and rsi_sart:

            return {
                "symbol": symbol,
                "price": fiyat,
                "ema14": float(son["EMA14"]),
                "rsi": float(son["RSI14"]),
                "base": float(son["BASE"])
            }

        return None

    except Exception as e:

        print(
            f"{symbol} HATA: "
            f"{type(e)._name_}: {e}"
        )

        return None


# -------------------------------------------------
# BIST 100
# -------------------------------------------------

print("BIST 100 listesi aliniyor...")

xu100 = bp.Index("XU100")

bist100 = xu100.component_symbols

print(
    "BIST 100 hisse sayisi:",
    len(bist100)
)


# -------------------------------------------------
# TARAMA
# -------------------------------------------------

sonuclar = []

for symbol in bist100:

    print(
        "Taranıyor:",
        symbol
    )

    sonuc = hisse_analiz(symbol)

    if sonuc:

        sonuclar.append(sonuc)

        print(
            "🚨 SARTLARI SAGLADI:",
            symbol
        )


# -------------------------------------------------
# SONUCLAR
# -------------------------------------------------

print("")
print("====================================")
print("TARAMA TAMAMLANDI")
print("====================================")

print(
    "Bulunan hisse sayisi:",
    len(sonuclar)
)

for sonuc in sonuclar:

    print(
        sonuc["symbol"],
        "| Fiyat:",
        round(sonuc["price"], 2),
        "| EMA14:",
        round(sonuc["ema14"], 2),
        "| RSI:",
        round(sonuc["rsi"], 2),
        "| Base:",
        round(sonuc["base"], 2)
    )
