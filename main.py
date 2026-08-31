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
    "BAYRK","EGEPO","JANTS","OSMEN","UFUK","BEGYO","EGSER","KAPLM","OSTIM","ULUFA",
    "BESTE","EKOS","KARTN","OZGYO","ULUUN","BEYAZ","EKSUN","KFEIN","OZGYO","ULUSE",
    "BIGCH","ELITE","KGYO","OZSUB","UNLU","BIGTK","EMKEL","KIMMR","OZYSR","VBTYZ",
    "BIZIM","EMPAE","KLMSN","PAMEL","VERTU","BLCYT","ENSRI","KLSYN","PCILT","VERUS",
    "BLUME","EPLAS","KNFRT","PEKGY","VKING","BMSCH","ERBOS","KONKA","PENGD","VRGYO",
    "BMSTL","ERCB","KRONT","KRPLS","PETUN","YAPRK","BNTAS","ESCOM","KRPLS","PETUN",
    "YIGIT","BORSK","ETILR","KRSTL","PINSU","YAYLA","BRKVY","EYGYO","KRVGD","PKENT",
    "YESIL","BRLSM","FADE","KTSKR","PLTUR","YKSLN","BULGS","FMIZP","KUTPO","PNLSN",
    "BURCE","FONET","PRDGS","ZGYO","BVSAN","FORMT","PRDGS","ZGYO","FORTE","LIDFA"
}


def gonderilenleri_oku():
    bugun = datetime.now(ISTANBUL).strftime("%Y-%m-%d")

    if not os.path.exists(GONDERILEN_DOSYA):
        return set()

    try:
        kayitlar = set()

        with open(GONDERILEN_DOSYA, "r", encoding="utf-8") as dosya:
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
    bugun = datetime.now(ISTANBUL).strftime("%Y-%m-%d")

    try:
        mevcut = []

        if os.path.exists(GONDERILEN_DOSYA):
            with open(GONDERILEN_DOSYA, "r", encoding="utf-8") as dosya:
                for satir in dosya:
                    satir = satir.strip()

                    if satir:
                        mevcut.append(satir)

        bugunku = {
            satir
            for satir in mevcut
            if satir.startswith(bugun + "|")
        }

        for hisse in hisseler:
            bugunku.add(
                f"{bugun}|{hisse.upper()}"
            )

        eski = [
            satir
            for satir in mevcut
            if not satir.startswith(bugun + "|")
        ]

        with open(GONDERILEN_DOSYA, "w", encoding="utf-8") as dosya:
            for satir in sorted(eski + list(bugunku)):
                dosya.write(satir + "\n")

        print("Kayıt dosyası güncellendi.")

    except Exception as hata:
        print(
            "Gönderilenler kaydedilemedi:",
            type(hata)._name_,
            str(hata)
        )


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

        print("Telegram:", response.status_code)

        return response.ok

    except Exception as hata:
        print(
            "Telegram HATA:",
            type(hata)._name_,
            str(hata)
        )

        return False


def piyasa_acik_mi():
    now = datetime.now(ISTANBUL)

    if now.weekday() >= 5:
        return False

    dakika = now.hour * 60 + now.minute

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

    kazanc = delta.clip(lower=0)
    kayip = -delta.clip(upper=0)

    ort_kazanc = kazanc.ewm(
        alpha=1 / RSI_PERIOD,
        adjust=False
    ).mean()

    ort_kayip = kayip.ewm(
        alpha=1 / RSI_PERIOD,
        adjust=False
    ).mean()

    rs = ort_kazanc / ort_kayip

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
        (yukari_hareket > asagi_hareket)
        & (yukari_hareket > 0),
        0.0
    )

    minus_dm = asagi_hareket.where(
        (asagi_hareket > yukari_hareket)
        & (asagi_hareket > 0),
        0.0
    )

    tr1 = high - low
    tr2 = (high - onceki_close).abs()
    tr3 = (low - onceki_close).abs()

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

    di_toplam = plus_di + minus_di

    dx = (
        100
        * (plus_di - minus_di).abs()
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
    for deneme in range(1, MAX_RETRIES + 1):

        try:
            ticker = bp.Ticker(symbol)

            df = ticker.history(
                period="6mo"
            )

            if df is None or len(df) < 120:
                return None

            return df.copy()

        except Exception as hata:

            hata_metni = str(hata)

            if (
                "429" in hata_metni
                or "Too Many Requests" in hata_metni
            ):
                bekleme = 2 ** deneme

                print(
                    f"{symbol}: 429 - "
                    f"{bekleme} sn bekleniyor"
                )

                time.sleep(bekleme)

                continue

            print(
                symbol,
                "VERİ HATASI:",
                type(hata)._name_,
                str(hata)
            )

            return None

    return None


def fibonacci_seviyeleri(df):

    if len(df) < FIB_LOOKBACK:
        return None

    son_df = df.tail(FIB_LOOKBACK)

    high_series = son_df["High"]
    low_series = son_df["Low"]

    fhigh = float(high_series.max())
    flow = float(low_series.min())

    if fhigh <= flow:
        return None

    high_pos = high_series.values.argmax()
    low_pos = low_series.values.argmin()

    high_bars_back = (
        FIB_LOOKBACK - 1 - high_pos
    )

    low_bars_back = (
        FIB_LOOKBACK - 1 - low_pos
    )

    revfibs = low_bars_back > high_bars_back

    aralik = fhigh - flow

    def fib_x(n):

        if revfibs:
            return aralik * n + flow

        return fhigh - aralik * n

    seviyeler = {
        oran: float(fib_x(deger))
        for oran, deger in {
            "0.000": 0.000,
            "0.236": 0.236,
            "0.382": 0.382,
            "0.500": 0.500,
            "0.618": 0.618,
            "0.786": 0.786,
            "1.000": 1.000
        }.items()
    }

    return {
        "high": fhigh,
        "low": flow,
        "high_bars_back": high_bars_back,
        "low_bars_back": low_bars_back,
        "revfibs": revfibs,
        "yon": (
            "yukselis"
            if revfibs
            else "dus"
        ),
        "seviyeler": seviyeler
    }


def fib_destek_direnc_bul(df, fiyat):

    fib = fibonacci_seviyeleri(df)

    if fib is None:
        return None

    seviyeler = fib["seviyeler"]

    destekler = [
        (float(v), o)
        for o, v in seviyeler.items()
        if float(v) < fiyat
    ]

    direncler = [
        (float(v), o)
        for o, v in seviyeler.items()
        if float(v) > fiyat
    ]

    destekler.sort(
        key=lambda x: x[0],
        reverse=True
    )

    direncler.sort(
        key=lambda x: x[0]
    )

    hedefler = [
        direncler[i]
        if len(direncler) > i
        else None
        for i in range(6)
    ]

    return {
        "s1": (
            destekler[0]
            if destekler
            else None
        ),
        **{
            f"k{i+1}": hedefler[i]
            for i in range(6)
        },
        "fib": fib
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
            hacim / ortalama_hacim
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


def yuzde_mesafe(seviye, fiyat):

    if seviye is None:
        return None

    return (
        (seviye - fiyat)
        / fiyat
    ) * 100


def analiz_et(symbol):

    try:

        print(
            "Taranıyor:",
            symbol
        )

        df = veri_al(symbol)

        if df is None:
            return None

        gerekli = {
            "High",
            "Low",
            "Close",
            "Volume"
        }

        if not gerekli.issubset(df.columns):
            return None

        df["EMA14"] = (
            df["Close"].ewm(
                span=EMA_PERIOD,
                adjust=False
            ).mean()
        )

        df["RSI14"] = rsi_hesapla(
            df["Close"]
        )

        df["ADX14"] = adx_hesapla(
            df
        )

        df["BASE"] = (
            df["High"]
            .rolling(BASE_PERIOD)
            .max()
            +
            df["Low"]
            .rolling(BASE_PERIOD)
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
            (son["Close"] / hafta_once["Close"])
            - 1
        ) * 100

        gunluk_degisim = (
            (son["Close"] / onceki["Close"])
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

        ichimoku_sinyal = (
            onceki["BASE"] >= onceki["Close"]
            and
            son["BASE"] < son["Close"]
        )

        fiyat_ema_sinyal = (
            son["Close"]
            >=
            son["EMA14"]
            * (1 + EMA_MIN_DISTANCE)
        )

        ema_yukseliyor = (
            son["EMA14"]
            >
            onceki["EMA14"]
        )

        rsi_50_cross = (
            onceki["RSI14"] <= 50
            and
            son["RSI14"] > 50
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

        s1, s1_fib = s1_bilgi

        stop = s1 * 0.995

        sonuc = {
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
                (fiyat / ema14) - 1
            ) * 100,
            "rsi14": rsi14,
            "adx14": adx,
            "s1": s1,
            "s1_fib": s1_fib,
            "stop": stop
        }

        for i in range(1, 7):

            bilgi = (
                fib_sonuclari[
                    f"k{i}"
                ]
            )

            sonuc[f"k{i}"] = (
                bilgi[0]
                if bilgi
                else None
            )

            sonuc[f"k{i}_fib"] = (
                bilgi[1]
                if bilgi
                else None
            )

        sonuc["fib_high"] = (
            fib_sonuclari["fib"]["high"]
        )

        sonuc["fib_low"] = (
            fib_sonuclari["fib"]["low"]
        )

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

    bist100 = bist100_listesi()

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
        datetime.now(ISTANBUL)
    )

    print(
        "\n⚡ Hızlı tarama başlıyor..."
    )

    print(
        f"⚡ Aynı anda {MAX_WORKERS} hisse taranacak."
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
        "📐 Fibonacci: TradingView 100 mum"
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
        datetime.now(ISTANBUL)
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

        symbol = sonuc["symbol"]

        pazar_adi = (
            "BIST 100"
            if symbol in bist100
            else (
                "Ana Pazar"
                if symbol in ANA_PAZAR
                else "Bilinmiyor"
            )
        )

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

        adx_deger = sonuc["adx14"]

        adx_isaret = adx_gosterge(
            adx_deger
        )

        fiyat = sonuc["price"]
        stop = sonuc["stop"]

        s1 = sonuc["s1"]

        stop_yuzde = yuzde_mesafe(
            stop,
            fiyat
        )

        k_yuzdeleri = {}

        for isim in [
            "k1",
            "k2",
            "k3",
            "k4",
            "k5",
            "k6"
        ]:

            seviye = sonuc[isim]

            k_yuzdeleri[isim] = (
                yuzde_mesafe(
                    seviye,
                    fiyat
                )
                if seviye is not None
                else None
            )

        hacim_orani = (
            sonuc["volume"]
            /
            sonuc["avg_volume_20"]
            if sonuc["avg_volume_20"] > 0
            else 0
        )

        mesaj = (

            f"🟢 YENİ : {symbol} "
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

            f"🔊 Hacim: "
            f"{sonuc['volume']:,.0f}\n"

            f"📊 20G Ort. Hacim: "
            f"{sonuc['avg_volume_20']:,.0f}\n"

            f"📈 Hacim/Ort.: "
            f"{hacim_orani:.2f}x\n\n"

            f"🛑 DESTEKLER\n"

            f"S1: "
            f"{s1:.2f} TL — "
            f"Fib {sonuc['s1_fib']} "
            f"→ "
            f"{yuzde_mesafe(s1, fiyat):+.2f}%\n\n"

            f"🛑 STOP\n"

            f"{stop:.2f} TL "
            f"→ "
            f"{stop_yuzde:+.2f}%\n\n"

            f"🎯 HEDEFLER\n"

            f"K1: "
            f"{sonuc['k1']:.2f} TL — "
            f"Fib {sonuc['k1_fib']} "
            f"→ "
            f"{k_yuzdeleri['k1']:+.2f}%\n"
        )

        for i in range(2, 7):

            k = sonuc[f"k{i}"]

            if k is not None:

                mesaj += (
                    f"K{i}: "
                    f"{k:.2f} TL — "
                    f"Fib "
                    f"{sonuc[f'k{i}_fib']} "
                    f"→ "
                    f"{k_yuzdeleri[f'k{i}']:+.2f}%\n"
                )

        mesaj += (
            f"\n📐 100G FIB ARALIĞI\n"
            f"🔻 Dip: "
            f"{sonuc['fib_low']:.2f} TL\n"
            f"🔺 Tepe: "
            f"{sonuc['fib_high']:.2f} TL"
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
