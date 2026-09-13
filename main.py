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
AYLIK_GONDERILEN_DOSYA = "gonderilen_aylik_hisseler.txt"

# 5 günlük performans takip dosyası
PERFORMANS_DOSYA = "5_gunluk_performans.txt"

EMA_PERIOD = 14
RSI_PERIOD = 14
BASE_PERIOD = 26
ADX_PERIOD = 14

EMA_MIN_DISTANCE = 0.02

FIB_LOOKBACK = 100

# ============================================================
# AYLIK MACD
# ============================================================

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

AYLIK_VERI_PERIYODU = "5y"

# ============================================================
# GENEL AYARLAR
# ============================================================

MAX_WORKERS = 4
MAX_RETRIES = 3

ISTANBUL = ZoneInfo("Europe/Istanbul")


# ============================================================
# ANA PAZAR
# ============================================================

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
    "BLUME","EPLAS","KNFRT","PENGD","PETUN","YAPRK","BMSCH","ERBOS","KONKA","PETUN",
    "BMSTL","ERCB","KRONT","KRPLS","PINSU","YIGIT","BNTAS","ESCOM","ETILR","KRSTL",
    "YAYLA","BRKVY","KRVGD","PKENT","YESIL","BRLSM","FADE","KTSKR","PLTUR",
    "YKSLN","BULGS","FMIZP","KUTPO","PNLSN","BURCE","FONET","PRDGS","ZGYO","BVSAN",
    "FORMT","FORTE","LIDFA"
}


# ============================================================
# GÜNLÜK GÖNDERİLENLER
# ============================================================

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
                        kayitlar.add(
                            hisse.upper()
                        )

        return kayitlar

    except Exception as hata:

        print(
            "Gönderilenler okunamadı:",
            type(hata).__name__,
            str(hata)
        )

        return set()


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
            "Günlük kayıt dosyası güncellendi."
        )

    except Exception as hata:

        print(
            "Gönderilenler kaydedilemedi:",
            type(hata).__name__,
            str(hata)
        )


# ============================================================
# AYLIK GÖNDERİLENLER
# ============================================================

def aylik_gonderilenleri_oku():

    bu_ay = datetime.now(
        ISTANBUL
    ).strftime("%Y-%m")

    if not os.path.exists(
        AYLIK_GONDERILEN_DOSYA
    ):
        return set()

    try:

        kayitlar = set()

        with open(
            AYLIK_GONDERILEN_DOSYA,
            "r",
            encoding="utf-8"
        ) as dosya:

            for satir in dosya:

                satir = satir.strip()

                if not satir:
                    continue

                parcalar = satir.split("|")

                if len(parcalar) == 2:

                    ay, hisse = parcalar

                    if ay == bu_ay:

                        kayitlar.add(
                            hisse.upper()
                        )

        return kayitlar

    except Exception as hata:

        print(
            "Aylık gönderilenler okunamadı:",
            type(hata).__name__,
            str(hata)
        )

        return set()


def aylik_gonderilenleri_kaydet(hisseler):

    bu_ay = datetime.now(
        ISTANBUL
    ).strftime("%Y-%m")

    try:

        mevcut = []

        if os.path.exists(
            AYLIK_GONDERILEN_DOSYA
        ):

            with open(
                AYLIK_GONDERILEN_DOSYA,
                "r",
                encoding="utf-8"
            ) as dosya:

                for satir in dosya:

                    satir = satir.strip()

                    if satir:
                        mevcut.append(satir)

        bu_ayki = {
            satir
            for satir in mevcut
            if satir.startswith(
                bu_ay + "|"
            )
        }

        for hisse in hisseler:

            bu_ayki.add(
                f"{bu_ay}|{hisse.upper()}"
            )

        eski = [
            satir
            for satir in mevcut
            if not satir.startswith(
                bu_ay + "|"
            )
        ]

        with open(
            AYLIK_GONDERILEN_DOSYA,
            "w",
            encoding="utf-8"
        ) as dosya:

            for satir in sorted(
                eski + list(bu_ayki)
            ):

                dosya.write(
                    satir + "\n"
                )

        print(
            "Aylık kayıt dosyası güncellendi."
        )

    except Exception as hata:

        print(
            "Aylık kayıtlar kaydedilemedi:",
            type(hata).__name__,
            str(hata)
        )


# ============================================================
# 5 GÜNLÜK PERFORMANS TAKİP
#
# DOSYA FORMATI:
#
# tarih|hisse|fiyat|tip
#
# Örnek:
#
# 2026-09-14|ASELS|215.00|GUNLUK
# 2026-09-14|THYAO|310.50|AYLIK
#
# ============================================================

def performans_kayitlarini_oku():

    if not os.path.exists(
        PERFORMANS_DOSYA
    ):
        return []

    kayitlar = []

    try:

        with open(
            PERFORMANS_DOSYA,
            "r",
            encoding="utf-8"
        ) as dosya:

            for satir in dosya:

                satir = satir.strip()

                if not satir:
                    continue

                parcalar = satir.split("|")

                if len(parcalar) != 4:
                    continue

                tarih, hisse, fiyat, tip = parcalar

                try:

                    fiyat = float(fiyat)

                except Exception:

                    continue

                kayitlar.append({
                    "tarih": tarih,
                    "symbol": hisse.upper(),
                    "fiyat": fiyat,
                    "tip": tip.upper()
                })

        return kayitlar

    except Exception as hata:

        print(
            "Performans kayıtları okunamadı:",
            type(hata).__name__,
            str(hata)
        )

        return []


def performans_kaydi_ekle(
    symbol,
    fiyat,
    tip
):

    try:

        tarih = datetime.now(
            ISTANBUL
        ).strftime("%Y-%m-%d")

        kayit = (
            f"{tarih}|"
            f"{symbol.upper()}|"
            f"{float(fiyat):.8f}|"
            f"{tip.upper()}"
        )

        mevcut = []

        if os.path.exists(
            PERFORMANS_DOSYA
        ):

            with open(
                PERFORMANS_DOSYA,
                "r",
                encoding="utf-8"
            ) as dosya:

                for satir in dosya:

                    satir = satir.strip()

                    if satir:
                        mevcut.append(satir)

        # Aynı tarih + hisse + tip tekrar kaydedilmesin

        kontrol = (
            f"{tarih}|"
            f"{symbol.upper()}|"
        )

        for satir in mevcut:

            if (
                satir.startswith(kontrol)
                and
                satir.endswith(
                    "|" + tip.upper()
                )
            ):

                return

        with open(
            PERFORMANS_DOSYA,
            "a",
            encoding="utf-8"
        ) as dosya:

            dosya.write(
                kayit + "\n"
            )

        print(
            f"📌 5 günlük takip kaydedildi: "
            f"{symbol} | {tip} | "
            f"{fiyat:.2f} TL"
        )

    except Exception as hata:

        print(
            "Performans kaydı eklenemedi:",
            type(hata).__name__,
            str(hata)
        )


def performans_kaydi_sil(
    kayit
):

    try:

        mevcut = []

        if os.path.exists(
            PERFORMANS_DOSYA
        ):

            with open(
                PERFORMANS_DOSYA,
                "r",
                encoding="utf-8"
            ) as dosya:

                mevcut = [
                    satir.strip()
                    for satir in dosya
                    if satir.strip()
                ]

        hedef = (
            f"{kayit['tarih']}|"
            f"{kayit['symbol']}|"
            f"{kayit['fiyat']:.8f}|"
            f"{kayit['tip']}"
        )

        yeni = []

        silindi = False

        for satir in mevcut:

            parcalar = satir.split("|")

            if len(parcalar) != 4:

                yeni.append(satir)
                continue

            try:

                ayni = (
                    parcalar[0] == kayit["tarih"]
                    and
                    parcalar[1].upper()
                    == kayit["symbol"].upper()
                    and
                    abs(
                        float(parcalar[2])
                        - kayit["fiyat"]
                    ) < 0.000001
                    and
                    parcalar[3].upper()
                    == kayit["tip"].upper()
                )

            except Exception:

                ayni = False

            if ayni and not silindi:

                silindi = True
                continue

            yeni.append(satir)

        with open(
            PERFORMANS_DOSYA,
            "w",
            encoding="utf-8"
        ) as dosya:

            for satir in yeni:
                dosya.write(
                    satir + "\n"
                )

    except Exception as hata:

        print(
            "Performans kaydı silinemedi:",
            type(hata).__name__,
            str(hata)
        )


# ============================================================
# PERFORMANS İÇİN 5. İŞLEM GÜNÜNÜ BUL
#
# Burada takvim günü değil, borsapy'den gelen gerçek
# işlem günleri kullanılıyor.
# ============================================================

def besinci_islem_gunu_bul(
    df,
    sinyal_tarihi
):

    try:

        if df is None:
            return None

        if "Close" not in df.columns:
            return None

        if len(df) == 0:
            return None

        veri = df.copy()

        if not isinstance(
            veri.index,
            pd.DatetimeIndex
        ):

            veri.index = pd.to_datetime(
                veri.index
            )

        # Saat bilgisini kaldır
        tarihler = pd.DatetimeIndex(
            veri.index
        ).normalize()

        sinyal_gunu = pd.Timestamp(
            sinyal_tarihi
        ).normalize()

        # Sinyal gününden sonraki gerçek işlem günleri
        sonraki = []

        for i in range(
            len(veri)
        ):

            tarih = tarihler[i]

            if tarih > sinyal_gunu:

                try:

                    fiyat = float(
                        veri.iloc[i]["Close"]
                    )

                except Exception:

                    continue

                if pd.isna(fiyat):
                    continue

                sonraki.append({
                    "tarih": tarih,
                    "fiyat": fiyat
                })

        # En az 5 işlem günü gerekiyor
        if len(sonraki) < 5:
            return None

        return sonraki[4]

    except Exception as hata:

        print(
            "5. işlem günü hesaplama HATA:",
            type(hata).__name__,
            str(hata)
        )

        return None


# ============================================================
# 5 GÜNLÜK PERFORMANS MESAJI
# ============================================================

def performans_mesaji_hazirla(
    kayit,
    sonuc_tarihi,
    sonuc_fiyati,
    performans
):

    symbol = kayit["symbol"]

    tip = kayit["tip"]

    if performans >= 0:

        emoji = "🟢"
        durum = "POZİTİF"

    else:

        emoji = "🔴"
        durum = "NEGATİF"

    if tip == "AYLIK":

        sinyal_tipi = "🔴 AYLIK"

    else:

        sinyal_tipi = "🟢 GÜNLÜK"

    mesaj = (

        f"📊 5 GÜNLÜK PERFORMANS\n\n"

        f"{emoji} {symbol}\n\n"

        f"📌 Sinyal: {sinyal_tipi}\n"

        f"📅 Sinyal tarihi: "
        f"{kayit['tarih']}\n"

        f"💰 Sinyal fiyatı: "
        f"{kayit['fiyat']:.2f} TL\n\n"

        f"📅 5. işlem günü: "
        f"{sonuc_tarihi.strftime('%d.%m.%Y')}\n"

        f"💰 5. gün fiyatı: "
        f"{sonuc_fiyati:.2f} TL\n\n"

        f"{emoji} Performans: "
        f"{performans:+.2f}%\n\n"

        f"{'✅' if performans >= 0 else '❌'} "
        f"5 GÜNLÜK SONUÇ: {durum}"
    )

    return mesaj


# ============================================================
# 5 GÜNLÜK PERFORMANS KONTROLÜ
#
# SADECE VADESİ GELMİŞ KAYITLARIN VERİSİ ÇEKİLİR.
#
# Bu fonksiyon bütün hisseleri tekrar taramaz.
# ============================================================

def bes_gunluk_performans_kontrol():

    print("\n====================================")
    print("📊 5 GÜNLÜK PERFORMANS KONTROLÜ")
    print("====================================")

    kayitlar = performans_kayitlarini_oku()

    if not kayitlar:

        print(
            "📭 Bekleyen 5 günlük performans kaydı yok."
        )

        return

    print(
        "Toplam takip edilen kayıt:",
        len(kayitlar)
    )

    bugun = datetime.now(
        ISTANBUL
    ).date()

    kontrol_edilecek = []

    # --------------------------------------------------------
    # Önce sadece gerçekten 5 işlem günü geçmiş olabilecek
    # kayıtları seçiyoruz.
    #
    # En erken kontrol için 7 takvim günü yeterli bir tampon.
    # Hafta sonu nedeniyle erken kontrol yapılması sorun değil;
    # gerçek işlem günü yine veri üzerinden belirlenecek.
    # --------------------------------------------------------

    for kayit in kayitlar:

        try:

            sinyal_tarihi = datetime.strptime(
                kayit["tarih"],
                "%Y-%m-%d"
            ).date()

        except Exception:

            continue

        gun_farki = (
            bugun - sinyal_tarihi
        ).days

        if gun_farki >= 5:

            kontrol_edilecek.append(
                kayit
            )

    if not kontrol_edilecek:

        print(
            "⏳ Henüz 5 işlem günü dolan kayıt yok."
        )

        return

    print(
        "⏱️ Kontrol edilecek kayıt:",
        len(kontrol_edilecek)
    )

    tamamlanan = 0

    # --------------------------------------------------------
    # SADECE VADESİ GELEN KAYITLAR
    # --------------------------------------------------------

    for kayit in kontrol_edilecek:

        symbol = kayit["symbol"]

        try:

            print(
                f"📊 Performans kontrolü: "
                f"{symbol} | "
                f"{kayit['tip']}"
            )

            # ------------------------------------------------
            # Burada sadece vadesi gelen hissenin verisi alınır.
            # Tüm tarama listesi tekrar taranmaz.
            # ------------------------------------------------

            df = veri_al(
                symbol,
                "6mo"
            )

            if df is None:

                print(
                    f"⚠️ {symbol}: "
                    "Performans verisi alınamadı."
                )

                continue

            hedef = besinci_islem_gunu_bul(
                df,
                kayit["tarih"]
            )

            # Henüz 5. işlem günü oluşmadıysa
            # kayıt silinmez, sonraki taramada tekrar kontrol edilir.

            if hedef is None:

                print(
                    f"⏳ {symbol}: "
                    "5. işlem günü henüz oluşmamış."
                )

                continue

            sonuc_fiyati = float(
                hedef["fiyat"]
            )

            giris_fiyati = float(
                kayit["fiyat"]
            )

            if giris_fiyati <= 0:

                print(
                    f"⚠️ {symbol}: "
                    "Geçersiz giriş fiyatı."
                )

                continue

            performans = (
                (
                    sonuc_fiyati
                    /
                    giris_fiyati
                )
                - 1
            ) * 100

            mesaj = performans_mesaji_hazirla(
                kayit,
                hedef["tarih"],
                sonuc_fiyati,
                performans
            )

            if telegram_gonder(mesaj):

                # ------------------------------------------------
                # Telegram başarıyla gönderildiyse kaydı siliyoruz.
                # Böylece aynı performans tekrar gönderilmez.
                # ------------------------------------------------

                performans_kaydi_sil(
                    kayit
                )

                print(
                    f"✅ {symbol}: "
                    f"5 günlük performans gönderildi "
                    f"({performans:+.2f}%)"
                )

            else:

                print(
                    f"⚠️ {symbol}: "
                    "Telegram gönderilemedi. "
                    "Kayıt korunuyor."
                )

            tamamlanan += 1

        except Exception as hata:

            print(
                symbol,
                "5 GÜNLÜK PERFORMANS HATASI:",
                type(hata).__name__,
                str(hata)
            )

    print(
        "📊 Performans kontrolü tamamlandı."
    )

    print(
        "Kontrol edilen:",
        tamamlanan
    )


# ============================================================
# TELEGRAM
# ============================================================

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

        if not response.ok:

            print(
                "Telegram cevap:",
                response.text[:500]
            )

        return response.ok

    except Exception as hata:

        print(
            "Telegram HATA:",
            type(hata).__name__,
            str(hata)
        )

        return False


# ============================================================
# PİYASA
# ============================================================

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


# ============================================================
# BIST 100
# ============================================================

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
            type(hata).__name__,
            str(hata)
        )

        return set()


# ============================================================
# RSI
# ============================================================

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
        /
        ort_kayip
    )

    return 100 - (
        100 / (1 + rs)
    )


# ============================================================
# ADX
# ============================================================

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
            >
            asagi_hareket
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
            >
            yukari_hareket
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
        -
        onceki_close
    ).abs()

    tr3 = (
        low
        -
        onceki_close
    ).abs()

    true_range = (
        tr1
        .combine(
            tr2,
            max
        )
        .combine(
            tr3,
            max
        )
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
        /
        atr
    )

    minus_di = (
        100
        *
        minus_dm.ewm(
            alpha=1 / ADX_PERIOD,
            adjust=False
        ).mean()
        /
        atr
    )

    di_toplam = (
        plus_di
        +
        minus_di
    )

    dx = (
        100
        *
        (
            plus_di
            -
            minus_di
        ).abs()
        /
        di_toplam
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


# ============================================================
# VERİ AL
# ============================================================

def veri_al(
    symbol,
    period="6mo"
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
                period=period
            )

            if df is None:
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
                type(hata).__name__,
                str(hata)
            )

            return None

    return None


# ============================================================
# FIBONACCI
# ============================================================

def fibonacci_seviyeleri(df):

    if len(df) < FIB_LOOKBACK:
        return None

    son_df = df.tail(
        FIB_LOOKBACK
    ).copy()

    high_series = son_df["High"]
    low_series = son_df["Low"]

    fib_high = float(
        high_series.max()
    )

    fib_low = float(
        low_series.min()
    )

    if fib_high <= fib_low:
        return None

    high_index = (
        high_series.idxmax()
    )

    low_index = (
        low_series.idxmin()
    )

    yukselis = (
        low_index < high_index
    )

    aralik = (
        fib_high
        -
        fib_low
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


def fib_analiz(
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

    ust = []

    for oran, seviye in seviyeler.items():

        if seviye > fiyat:

            kar_yuzdesi = (
                (
                    seviye
                    -
                    fiyat
                )
                /
                fiyat
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

    yakin_ust = (
        ust[0]
        if ust
        else None
    )

    fib100 = seviyeler[
        "1.000"
    ]

    tepe_potansiyel = (
        (
            fib100
            -
            fiyat
        )
        /
        fiyat
    ) * 100

    fiyat_seviyesi = None

    en_yakin_mesafe = None

    for oran, seviye in seviyeler.items():

        mesafe = abs(
            fiyat
            -
            seviye
        )

        if (
            en_yakin_mesafe is None
            or
            mesafe < en_yakin_mesafe
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


# ============================================================
# SİNYAL GÜCÜ
# ============================================================

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
        max(
            0,
            puan
        )
    )


# ============================================================
# ORTAK HİSSE DETAYLARI
# ============================================================

def hisse_detaylarini_hazirla(
    symbol,
    df
):

    try:

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

        if len(df) < 120:
            return None

        df = df.copy()

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
            adx_hesapla(df)
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

        fiyat = float(
            son["Close"]
        )

        ema14 = float(
            son["EMA14"]
        )

        rsi14 = float(
            son["RSI14"]
        )

        fib_sonuc = fib_analiz(
            df,
            fiyat
        )

        if fib_sonuc is None:
            return None

        stop_bilgi = fib_sonuc[
            "stop"
        ]

        if stop_bilgi is None:
            return None

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

            "stop": stop_bilgi[0],

            "stop_fib": stop_bilgi[1],

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
            "DETAY HATASI:",
            type(hata).__name__,
            str(hata)
        )

        return None


# ============================================================
# GÜNLÜK ANALİZ
# ============================================================

def analiz_et(symbol):

    try:

        print(
            "Taranıyor:",
            symbol
        )

        df = veri_al(
            symbol,
            "6mo"
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

        if len(df) < 120:
            return None

        df = df.copy()

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
            adx_hesapla(df)
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

        onceki = df.iloc[-2]

        son = df.iloc[-1]

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

        return hisse_detaylarini_hazirla(
            symbol,
            df
        )

    except Exception as hata:

        print(
            symbol,
            "GÜNLÜK HATA:",
            type(hata).__name__,
            str(hata)
        )

        return None


# ============================================================
# AYLIK MACD HESAPLA
# ============================================================

def aylik_macd_hesapla(df):

    try:

        if df is None:
            return None

        if "Close" not in df.columns:
            return None

        if len(df) < 100:
            return None

        aylik = df.copy()

        if not isinstance(
            aylik.index,
            pd.DatetimeIndex
        ):

            try:

                aylik.index = pd.to_datetime(
                    aylik.index
                )

            except Exception:

                return None

        aylik = aylik.sort_index()

        aylik_close = (
            aylik["Close"]
            .resample("ME")
            .last()
            .dropna()
        )

        if len(aylik_close) < 35:
            return None

        macd_fast = (
            aylik_close
            .ewm(
                span=MACD_FAST,
                adjust=False
            )
            .mean()
        )

        macd_slow = (
            aylik_close
            .ewm(
                span=MACD_SLOW,
                adjust=False
            )
            .mean()
        )

        macd_level = (
            macd_fast
            -
            macd_slow
        )

        signal = (
            macd_level
            .ewm(
                span=MACD_SIGNAL,
                adjust=False
            )
            .mean()
        )

        aylik_macd = pd.DataFrame({
            "Close": aylik_close,
            "MACD": macd_level,
            "Signal": signal
        })

        if len(aylik_macd) < 2:
            return None

        onceki = aylik_macd.iloc[-2]

        son = aylik_macd.iloc[-1]

        yukari_kesisim = (
            onceki["MACD"]
            <=
            onceki["Signal"]
            and
            son["MACD"]
            >
            son["Signal"]
        )

        return {

            "sinyal": bool(
                yukari_kesisim
            ),

            "macd": float(
                son["MACD"]
            ),

            "signal": float(
                son["Signal"]
            ),

            "onceki_macd": float(
                onceki["MACD"]
            ),

            "onceki_signal": float(
                onceki["Signal"]
            )
        }

    except Exception as hata:

        print(
            "Aylık MACD hesaplama HATA:",
            type(hata).__name__,
            str(hata)
        )

        return None


# ============================================================
# AYLIK MACD ANALİZ
# ============================================================

def aylik_macd_analiz_et(symbol):

    try:

        print(
            "🔴 Aylık MACD taranıyor:",
            symbol
        )

        df_uzun = veri_al(
            symbol,
            AYLIK_VERI_PERIYODU
        )

        if df_uzun is None:
            return None

        macd_sonuc = (
            aylik_macd_hesapla(
                df_uzun
            )
        )

        if macd_sonuc is None:
            return None

        if not macd_sonuc["sinyal"]:
            return None

        df_gunluk = veri_al(
            symbol,
            "6mo"
        )

        if df_gunluk is None:
            return None

        detay = hisse_detaylarini_hazirla(
            symbol,
            df_gunluk
        )

        if detay is None:
            return None

        detay["aylik_macd"] = (
            macd_sonuc["macd"]
        )

        detay["aylik_signal"] = (
            macd_sonuc["signal"]
        )

        detay["aylik_onceki_macd"] = (
            macd_sonuc[
                "onceki_macd"
            ]
        )

        detay["aylik_onceki_signal"] = (
            macd_sonuc[
                "onceki_signal"
            ]
        )

        return detay

    except Exception as hata:

        print(
            symbol,
            "AYLIK MACD HATA:",
            type(hata).__name__,
            str(hata)
        )

        return None


# ============================================================
# FIB SATIRI
# ============================================================

def fib_satiri(
    oran,
    seviye,
    fiyat,
    fiyat_fib
):

    if oran == fiyat_fib:

        potansiyel = (
            (
                seviye
                -
                fiyat
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

    if seviye > fiyat:

        potansiyel = (
            (
                seviye
                -
                fiyat
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


# ============================================================
# TELEGRAM MESAJI
# ============================================================

def mesaj_hazirla(
    sonuc,
    baslik
):

    symbol = sonuc[
        "symbol"
    ]

    adx_deger = sonuc[
        "adx14"
    ]

    adx_isaret = adx_gosterge(
        adx_deger
    )

    fiyat = sonuc[
        "price"
    ]

    stop = sonuc[
        "stop"
    ]

    stop_fib = sonuc[
        "stop_fib"
    ]

    fibler = sonuc[
        "fib_levels"
    ]

    fiyat_fib = sonuc[
        "fiyat_fib"
    ]

    mesaj = (

        f"{baslik} : {symbol}"
        f"                   ADX "
        f"{adx_isaret} "
        f"{adx_deger:.1f}\n"

        f"⭐ Sinyal Gücü: "
        f"{sonuc['sinyal_gucu']}/100\n\n"

        f"💰 Giriş: "
        f"{fiyat:.2f} TL\n"

        f"{'🟢' if sonuc['daily_change'] >= 0 else '🔴'} "
        f"Günlük: "
        f"{sonuc['daily_change']:+.2f}%\n"

        f"{'🟢' if sonuc['weekly_change'] >= 0 else '🔴'} "
        f"1 Hafta: "
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
        f"{'BIST 100' if symbol in BIST100_GLOBAL else 'Ana Pazar'}\n"

        f"🔊 Hacim: "
        f"{sonuc['volume'] / 1_000_000:.1f}M"
    )

    return mesaj


# ============================================================
# GÜNLÜK TARAMA
# ============================================================

BIST100_GLOBAL = set()


def gunluk_tarama(
    tarama_listesi
):

    print("\n====================================")
    print("🟢 GÜNLÜK TARAMA")
    print("====================================")

    gonderilenler = (
        gonderilenleri_oku()
    )

    print(
        "Bugün daha önce gönderilen:",
        len(gonderilenler)
    )

    bulunan = []

    tamamlanan = 0

    baslangic_zamani = datetime.now(
        ISTANBUL
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
                    type(hata).__name__,
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
        -
        baslangic_zamani
    ).total_seconds()

    print(
        f"\n⏱️ Günlük tarama süresi: "
        f"{int(sure // 60)} dakika "
        f"{int(sure % 60)} saniye"
    )

    print(
        "Yeni bulunan günlük hisse:",
        len(bulunan)
    )

    basariyla_gonderilenler = set()

    for sonuc in bulunan:

        symbol = sonuc[
            "symbol"
        ]

        mesaj = mesaj_hazirla(
            sonuc,
            "🟢 YENİ"
        )

        if telegram_gonder(
            mesaj
        ):

            basariyla_gonderilenler.add(
                symbol
            )

            # =================================================
            # SADECE TELEGRAM BAŞARILIYSA 5 GÜNLÜK TAKİBE AL
            # =================================================

            performans_kaydi_ekle(
                symbol,
                sonuc["price"],
                "GUNLUK"
            )

    if basariyla_gonderilenler:

        gonderilenleri_kaydet(
            basariyla_gonderilenler
        )

        print(
            "Günlük gönderilen hisse:",
            ", ".join(
                sorted(
                    basariyla_gonderilenler
                )
            )
        )

    else:

        print(
            "Yeni gönderilen günlük hisse yok."
        )


# ============================================================
# AYLIK MACD TARAMA
# ============================================================

def aylik_macd_tarama(
    tarama_listesi
):

    print("\n====================================")
    print("🔴 AYLIK MACD TARAMASI")
    print("====================================")

    print(
        "📊 MACD: 12 / 26"
    )

    print(
        "📈 Signal: 9"
    )

    print(
        "🔴 ŞART: MACD Level aşağıdan yukarı Signal kesişimi"
    )

    print(
        "⏱️ Ay sonu beklenmeyecek."
    )

    print(
        "📅 İçinde bulunulan aylık mum kullanılacak."
    )

    aylik_gonderilenler = (
        aylik_gonderilenleri_oku()
    )

    print(
        "Bu ay daha önce gönderilen aylık hisse:",
        len(aylik_gonderilenler)
    )

    aylik_bulunan = []

    aylik_tamamlanan = 0

    aylik_baslangic = datetime.now(
        ISTANBUL
    )

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        aylik_gelecekler = {

            executor.submit(
                aylik_macd_analiz_et,
                symbol
            ): symbol

            for symbol in tarama_listesi
        }

        for gelecek in as_completed(
            aylik_gelecekler
        ):

            symbol = aylik_gelecekler[
                gelecek
            ]

            try:

                sonuc = gelecek.result()

                aylik_tamamlanan += 1

                if sonuc:

                    if symbol in aylik_gonderilenler:

                        print(
                            f"⏭️ {symbol} "
                            "bu ay zaten AYLIK gönderildi."
                        )

                    else:

                        print(
                            f"🔴 AYLIK MACD KESİŞİMİ: "
                            f"{symbol}"
                        )

                        aylik_bulunan.append(
                            sonuc
                        )

                        aylik_gonderilenler.add(
                            symbol
                        )

            except Exception as hata:

                aylik_tamamlanan += 1

                print(
                    symbol,
                    "AYLIK PARALEL HATA:",
                    type(hata).__name__,
                    str(hata)
                )

            if aylik_tamamlanan % 25 == 0:

                print(
                    f"📊 Aylık ilerleme: "
                    f"{aylik_tamamlanan}/"
                    f"{len(tarama_listesi)}"
                )

    aylik_sure = (
        datetime.now(
            ISTANBUL
        )
        -
        aylik_baslangic
    ).total_seconds()

    print(
        f"\n⏱️ Aylık MACD tarama süresi: "
        f"{int(aylik_sure // 60)} dakika "
        f"{int(aylik_sure % 60)} saniye"
    )

    print(
        "Yeni aylık MACD hissesi:",
        len(aylik_bulunan)
    )

    aylik_basariyla_gonderilenler = set()

    for sonuc in aylik_bulunan:

        symbol = sonuc[
            "symbol"
        ]

        mesaj = mesaj_hazirla(
            sonuc,
            "🔴 AYLIK"
        )

        if telegram_gonder(
            mesaj
        ):

            aylik_basariyla_gonderilenler.add(
                symbol
            )

            # =================================================
            # SADECE TELEGRAM BAŞARILIYSA 5 GÜNLÜK TAKİBE AL
            # =================================================

            performans_kaydi_ekle(
                symbol,
                sonuc["price"],
                "AYLIK"
            )

    if aylik_basariyla_gonderilenler:

        aylik_gonderilenleri_kaydet(
            aylik_basariyla_gonderilenler
        )

        print(
            "Aylık gönderilen hisse:",
            ", ".join(
                sorted(
                    aylik_basariyla_gonderilenler
                )
            )
        )

    else:

        print(
            "Yeni gönderilen aylık hisse yok."
        )


# ============================================================
# TEK TARAMA
# ============================================================
#
# ÖNEMLİ:
#
# 5 günlük performans kontrolü burada ilk olarak çalışır.
#
# Ancak:
#
# - bütün hisseler tekrar taranmaz
# - sadece vadesi gelen kayıtlar kontrol edilir
#
# Ana günlük tarama mantığı aynıdır.
#
# ============================================================

def tek_tarama(
    aylik_yap=False
):

    global BIST100_GLOBAL

    print("\n\n################################################")
    print("🚀 PLANLI TARAMA BAŞLADI")

    print(
        "🕐 Saat:",
        datetime.now(
            ISTANBUL
        ).strftime(
            "%d.%m.%Y %H:%M:%S"
        )
    )

    print(
        "📌 Aylık MACD:",
        "EVET"
        if aylik_yap
        else "HAYIR"
    )

    print("################################################")

    # ========================================================
    # 5 GÜNLÜK PERFORMANS
    #
    # Bu bölüm sadece vadesi gelen kayıtları kontrol eder.
    # ========================================================

    bes_gunluk_performans_kontrol()

    # ========================================================
    # PİYASA
    # ========================================================

    if not piyasa_acik_mi():

        print(
            "Piyasa saati dışında."
        )

        return

    # ========================================================
    # BIST LİSTELERİ
    # ========================================================

    print(
        "BIST 100 listesi alınıyor..."
    )

    bist100 = bist100_listesi()

    if not bist100:

        print(
            "BIST 100 listesi alınamadı."
        )

        return

    BIST100_GLOBAL = bist100

    tarama_listesi = sorted(
        bist100
        |
        ANA_PAZAR
    )

    print(
        "BIST 100 hisse sayısı:",
        len(bist100)
    )

    print(
        "Ana Pazar hisse sayısı:",
        len(ANA_PAZAR)
    )

    print(
        "Toplam benzersiz taranacak hisse:",
        len(tarama_listesi)
    )

    # ========================================================
    # GÜNLÜK
    # ========================================================

    gunluk_tarama(
        tarama_listesi
    )

    # ========================================================
    # AYLIK MACD
    #
    # SADECE:
    # 09:50 ilk çalışma
    # 14:00 ilk çalışma
    # ========================================================

    if aylik_yap:

        print(
            "\n🔴 Bu çalışma AYLIK MACD içeriyor."
        )

        aylik_macd_tarama(
            tarama_listesi
        )

    else:

        print(
            "\n⏭️ Bu çalışmada aylık MACD atlandı."
        )

    print("\n====================================")
    print("✅ BU PLANLI TARAMA TAMAMLANDI")
    print("====================================")


# ============================================================
# PROGRAMI ÇALIŞTIR
# ============================================================
#
# GitHub Actions:
#
# AYLIK_TARAMA=true python main.py
#
# veya
#
# AYLIK_TARAMA=false python main.py
#
# ============================================================

if __name__ == "__main__":

    aylik_yap = (
        os.environ.get(
            "AYLIK_TARAMA",
            "false"
        ).lower()
        == "true"
    )

    print(
        "\n🤖 BIST BOTU BAŞLATILDI"
    )

    print(
        "🕐 Türkiye saati:",
        datetime.now(
            ISTANBUL
        ).strftime(
            "%d.%m.%Y %H:%M:%S"
        )
    )

    print(
        "🔴 Aylık MACD:",
        "AKTİF"
        if aylik_yap
        else "PASİF"
    )

    print(
        "📊 5 Günlük Performans:",
        "AKTİF"
    )

    tek_tarama(
        aylik_yap=aylik_yap
    )

    print(
        "\n🏁 main.py tamamlandı."
    )
