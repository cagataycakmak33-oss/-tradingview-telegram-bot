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
    "BULGS", "FMIZP", "KUTPO", "PNLSN", "YUNSA",
    "BURCE", "FONET", "KZGYO", "PNSUT", "ZEDUR",
    "BVSAN", "FORMT", "PRDGS", "ZGYO",
    "FORTE", "LIDFA"
}


# =========================================================
# TARİHLİ GÖNDERİLEN KAYITLARI OKU
# =========================================================

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


# =========================================================
# GÖNDERİLENLERİ KAYDET
# =========================================================

def gonderilenleri_kaydet(hisseler):

    bugun = datetime.now(ISTANBUL).strftime("%Y-%m-%d")

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

        with open(
            GONDERILEN_DOSYA,
            "w",
            encoding="utf-8"
        ) as dosya:

            for satir in sorted(eski + list(bugunku)):
                dosya.write(satir + "\n")

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

    now = datetime.now(ISTANBUL)

    if now.weekday() >= 5:
        return False

    dakika = now.hour * 60 + now.minute

    return 9 * 60 + 40 <= dakika <= 18 * 60 + 10


# =========================================================
# BIST 100
# =========================================================

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


# =========================================================
# RSI
# =========================================================

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

    return 100 - (100 / (1 + rs))


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

    di_toplam = plus_di + minus_di

    dx = (
        100
        * (plus_di - minus_di).abs()
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

            ticker = bp.Ticker(symbol)

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


# =========================================================
# ANALİZ
# =========================================================

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

        if not gerekli.issubset(
            df.columns
        ):
            return None

        df["EMA14"] = df["Close"].ewm(
            span=EMA_PERIOD,
            adjust=False
        ).mean()

        df["RSI14"] = rsi_hesapla(
            df["Close"]
        )

        # ADX sadece bilgi amacıyla hesaplanıyor.
        # Hisse eleme filtresi DEĞİLDİR.
        df["ADX14"] = adx_hesapla(df)

        base_yuksek = df["High"].rolling(
            BASE_PERIOD
        ).max()

        base_dusuk = df["Low"].rolling(
            BASE_PERIOD
        ).min()

        df["BASE"] = (
            base_yuksek + base_dusuk
        ) / 2

        onceki = df.iloc[-2]
        son = df.iloc[-1]

        hafta_once = df.iloc[-6]

        bir_haftalik_degisim = (
            (son["Close"] / hafta_once["Close"]) - 1
        ) * 100

        gunluk_degisim = (
            (son["Close"] / onceki["Close"]) - 1
        ) * 100

        try:
            hacim = float(
                son["Volume"]
            )
        except Exception:
            hacim = 0.0

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

        ema_sinyal = (
            son["Close"]
            >= son["EMA14"] * 1.03
        )

        rsi_sinyal = (
            son["RSI14"] >= 50
        )

        # SADECE mevcut 3 filtre kullanılıyor.
        # ADX burada KESİNLİKLE filtre değil.
        if not (
            ichimoku_sinyal
            and ema_sinyal
            and rsi_sinyal
        ):
            return None

        # STOP = EMA14
        stop = float(
            son["EMA14"]
        )

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
            high + low + close
        ) / 3

        r1 = (
            2 * pivot - low
        )

        r2 = (
            pivot + high - low
        )

        r3 = (
            high + 2 * (pivot - low)
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
            "adx14": adx,
            "stop": stop,
            "k1": float(r1),
            "k2": float(r2),
            "k3": float(r3)
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

                    if symbol in gonderilenler:

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
        datetime.now(ISTANBUL)
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
    # TELEGRAM GÖNDER
    # =====================================================

    basariyla_gonderilenler = set()

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

        stop_yuzde = (
            (
                sonuc["stop"]
                - fiyat
            )
            / fiyat
        ) * 100

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
        # İSTEDİĞİMİZ TELEGRAM FORMATI
        # =================================================

        mesaj = (
            f"🟢 YENİ : {symbol}"
            f"                    "
            f"ADX {adx_isaret} "
            f"{adx_deger:.1f}\n\n"

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
            f"{sonuc['volume']:,.0f}\n\n"

            f"🛑 Stop: "
            f"{sonuc['stop']:.2f} TL "
            f"→ {stop_yuzde:+.2f}%\n"

            f"🎯 K1: "
            f"{sonuc['k1']:.2f} TL "
            f"→ {k1_yuzde:+.2f}%\n"

            f"🎯 K2: "
            f"{sonuc['k2']:.2f} TL "
            f"→ {k2_yuzde:+.2f}%\n"

            f"🎯 K3: "
            f"{sonuc['k3']:.2f} TL "
            f"→ {k3_yuzde:+.2f}%"
        )

        if telegram_gonder(
            mesaj
        ):

            basariyla_gonderilenler.add(
                symbol
            )

    # =====================================================
    # SADECE TELEGRAM'A BAŞARILI GİDENLERİ KAYDET
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
