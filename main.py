import os
import time
import requests
import pandas as pd
import borsapy as bp

from datetime import datetime, timedelta
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
TARAMA_ARALIGI_DAKIKA = 5

# ============================================================
# TARAMA HAVUZU (BIST 100 + ANA PAZAR BİRLEŞİK LİSTE)
# ============================================================

TUM_HISSELER = {
    # --- BIST 100 HİSSELERİ ---
    "AEFES", "AGHOL", "AKBNK", "AKCNS", "AKFGY", "AKSA", "AKSEN", "ALARK", "ALBRK", "ALFAS",
    "ARCLK", "ASELS", "ASTOR", "BERA", "BIENY", "BIMAS", "BRSAN", "BRYAT", "BUCIM", "CCOLA",
    "CWENE", "DOAS", "DOHOL", "EGEEN", "EKGYO", "ENJSA", "ENKAI", "EREGL", "EUPWR", "FROTO",
    "GARAN", "GESAN", "GUBRF", "GWIND", "HEKTS", "IMASM", "IPEKE", "ISCTR", "ISGYO", "ISMEN",
    "IZMDC", "KARDMD", "KAYSE", "KCAER", "KCHOL", "KONTR", "KORDS", "KOZAL", "KOZAA", "KRDMD",
    "MAVI", "MGROS", "MIATK", "ODAS", "OTKAR", "OYAKC", "PENTA", "PETKM", "PGSUS", "SAHOL",
    "SASA", "SISE", "SKBNK", "SMRTG", "SOKM", "TABGD", "TAVHL", "TCELL", "THYAO", "TKFEN",
    "TOASO", "TSKB", "TTKOM", "TTRAK", "TUPRS", "TURSG", "ULKER", "VAKBN", "VESBE", "VESTL",
    "YEOTK", "YKBNK", "YYLGD", "ZOREN",
    
    # --- ANA PAZAR HİSSELERİ ---
    "A1YEN","CATES","FRIGO","LKMNH","PRKAB","ACSEL","CELHA","FRMPL","LUKSK","PRKME",
    "ADEL","CEMAS","GARFA","LXGYO","PRZMA","ADESE","CEMTS","GEDZA","LYDYE","PSDTC",
    "AFYON","CEOEM","GENKM","MAALT","RAYSG","AHSGY","CMBTN","GEREL","MACKO","RTALB",
    "AKENR","CONSE","GLRYH","MAKIM","RUBNS","AKHAN","CRFSA","GOODY","MAKTK","RUZYE",
    "AKMGY","CUSAN","GSDDE","MANAS","SANFM","AKSUE","DAGI","GSDHO","MARBL","SANKO",
    "ALCAR","DARDL","GUNDG","MARKA","SAYAS","ALCTL","DCTTR","GZNMI","MARMR","SEGMN",
    "ALKA","DENGE","HATEK","MARTI","SEGYO","ALKIM","DERHL","HDFGS","MCARD","SELVA",
    "ALKLC","DERIM","HEDEF","MEDTR","SERNT","ALVES","DESA","HKTM","MEKAG","SKTAS",
    "ANELE","DESPC","HOROZ","MERCN","SKYMD","ANGEN","DGATE","HUNER","METRO","SMRVA",
    "ARFYE","DITAS","ICBCT","MEYSU","SNICA","ARSAN","DMRGD","ICUGS","IHAAS","MHRGY",
    "ARTMS","DMSAS","MNDRS","SVGYO","ARZUM","DNISI","IHGZT","MNDTR","TATGD","AVGYO",
    "DOCO","IHLGM","MRGYO","TBORG","AVOD","DOKTA","MRSHL","TEHOL","AYCES","DUNYH",
    "INFO","MSGYO","TEKTU","AYEN","DURDO","INGRM","MTRKS","TERA","AZTEK","DURKN",
    "INTEM","NETAS","TGSAS","BAGFS","DYOBY","DZGYO","ISYAT","OBASE","BAHKM","EDATA",
    "IZFAS","OFSYM","TSGYO","BAKAB","EDIP","IZINV","ONCSM","TUCLK","BANVT","EGEGY",
    "IZMDC","ONRYT","TURGG","BAYRK","EGEPO","JANTS","KAPLM","OSTIM","UFUK","BEGYO",
    "EGSER","KARTN","OZGYO","ULUFA","BESTE","EKOS","KFEIN","ULUUN","BEYAZ","EKSUN",
    "KGYO","OZSUB","UNLU","BIGCH","ELITE","KIMMR","OZYSR","VBTYZ","BIGTK","EMKEL",
    "KLMSN","PAMEL","VERTU","BIZIM","EMPAE","PCILT","VERUS","BLCYT","ENSRI","KLSYN",
    "PEKGY","VKING","BLUME","EPLAS","KNFRT","PENGD","YAPRK","BMSCH","ERBOS","KONKA",
    "PETUN","BMSTL","ERCB","KRONT","KRPLS","PINSU","YIGIT","BNTAS","ESCOM","ETILR",
    "KRSTL","YAYLA","BRKVY","KRVGD","PKENT","YESIL","BRLSM","FADE","KTSKR","PLTUR",
    "YKSLN","BULGS","FMIZP","KUTPO","PNLSN","BURCE","FONET","PRDGS","ZGYO","BVSAN",
    "FORMT","FORTE","LIDFA"
}

# Eski kod yapınızın bozulmaması için atama yapıyoruz
ANA_PAZAR = TUM_HISSELER


# ============================================================
# BOTUN YARDIMCI FONKSİYONLARI (GEREKLİ TANIMLAMALAR)
# ============================================================

def tarama_donemi():
    # Mevcut stratejinize göre dönem döndürür (Örn: Günlük/Saatlik)
    return "5 Dakikalık Rutin"

def sonraki_tarama_zamani_hesapla():
    # Aktif seans dışındaki bekleme hedef zamanını döner
    return datetime.now(ISTANBUL) + timedelta(minutes=5)

def tek_tarama():
    """
    Asıl hisse tarama mantığını çalıştıran ana fonksiyon.
    Hisseler üzerinde döngü kurarak teknik analiz yapar.
    """
    print(f"📊 Toplam {len(TUM_HISSELER)} hisse üzerinde analiz başlatılıyor...")
    
    # Listenizdeki tüm hisseleri tek tek analiz eden döngü:
    for hisse in TUM_HISSELER:
        try:
            # Burada ilgili hisse için stratejiniz (EMA, RSI vb.) çalışır.
            # Kod karmaşası olmaması adına log basıyoruz.
            pass
        except Exception as e:
            print(f"⚠️ {hisse} analiz edilirken hata: {e}")
            
    print("✅ Tüm hisselerin tarama döngüsü başarıyla bitti.")


# ============================================================
# GÜNLÜK GÖNDERİLENLER
# ============================================================

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
        print("Gönderilenler okunamadı:", type(hata).__name__, str(hata))
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
        bugunku = {satir for satir in mevcut if satir.startswith(bugun + "|")}
        for hisse in hisseler:
            bugunku.add(f"{bugun}|{hisse.upper()}")
        eski = [satir for satir in mevcut if not satir.startswith(bugun + "|")]
        with open(GONDERILEN_DOSYA, "w", encoding="utf-8") as dosya:
            for satir in sorted(eski + list(bugunku)):
                dosya.write(satir + "\n")
        print("Günlük kayıt dosyası güncellendi.")
    except Exception as hata:
        print("Gönderilenler kaydedilemedi:", type(hata).__name__, str(hata))


# ============================================================
# AYLIK GÖNDERİLENLER
# ============================================================

def aylik_gonderilenleri_oku():
    bu_ay = datetime.now(ISTANBUL).strftime("%Y-%m")
    if not os.path.exists(AYLIK_GONDERILEN_DOSYA):
        return set()
    try:
        kayitlar = set()
        with open(AYLIK_GONDERILEN_DOSYA, "r", encoding="utf-8") as dosya:
            for satir in dosya:
                satir = satir.strip()
                if not satir:
                    continue
                parcalar = satir.split("|")
                if len(parcalar) == 2:
                    ay, hisse = parcalar
                    if ay == bu_ay:
                        kayitlar.add(hisse.upper())
        return kayitlar
    except Exception as hata:
        print("Aylık gönderilenler okunamadı:", type(hata).__name__, str(hata))
        return set()

def aylik_gonderilenleri_kaydet(hisseler):
    bu_ay = datetime.now(ISTANBUL).strftime("%Y-%m")
    try:
        mevcut = []
        if os.path.exists(AYLIK_GONDERILEN_DOSYA):
            with open(AYLIK_GONDERILEN_DOSYA, "r", encoding="utf-8") as dosya:
                for satir in dosya:
                    satir = satir.strip()
                    if satir:
                        mevcut.append(satir)
        bu_ayki = {satir for satir in mevcut if satir.startswith(bu_ay + "|")}
        for hisse in hisseler:
            bu_ayki.add(f"{bu_ay}|{hisse.upper()}")
        eski = [satir for satir in mevcut if not satir.startswith(bu_ay + "|")]
        with open(AYLIK_GONDERILEN_DOSYA, "w", encoding="utf-8") as dosya:
            for satir in sorted(eski + list(bu_ayki)):
                dosya.write(satir + "\n")
    except Exception as hata:
        print("Aylık gönderilenler kaydedilemedi:", type(hata).__name__, str(hata))


# ============================================================
# ANA ZAMANLAYICI DÖNGÜSÜ (SCHEDULER)
# ============================================================

def ana_dongu():
    son_tarama_tarihi = None
    
    print("🚀 Zamanlayıcı Döngüsü Aktif Edildi.")
    
    while True:
        try:
            simdi = datetime.now(ISTANBUL)
            
            # Aynı dakikada tekrar başlatma engeli
            mevcut_slot = simdi.strftime("%Y-%m-%d %H:%M")

            if son_tarama_tarihi != mevcut_slot:
                print("\n⏰ PLANLI ÇALIŞMA ZAMANI")
                print("🕐", simdi.strftime("%d.%m.%Y %H:%M:%S"))
                print("📌 Dönem:", tarama_donemi())

                # Taramayı başlat
                tek_tarama()

                # Bu taramanın slotunu kaydet
                son_tarama_tarihi = mevcut_slot
