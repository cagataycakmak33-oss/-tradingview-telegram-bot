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
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

GONDERILEN_DOSYA = "gonderilen_hisseler.txt"
AYLIK_GONDERILEN_DOSYA = "gonderilen_aylik_hisseler.txt"
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
        print("Aylık kayıt dosyası güncellendi.")
    except Exception as hata:
        print("Aylık gönderilenler kaydedilemedi:", type(hata).__name__, str(hata))

# ============================================================
# TELEGRAM BİLDİRİM FONKSİYONU
# ============================================================
def telegram_mesaj_gonder(mesaj):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram token veya Chat ID eksik!")
        return
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Telegram hatası: {response.text}")
    except Exception as e:
        print(f"Telegram bağlantı hatası: {str(e)}")

# ============================================================
# ANA ÇALIŞMA MANTIĞI (ÖRNEK TARAMA)
# ============================================================
def hisse_tarama_yap():
    print("Piyasa taraması başlatılıyor...")
    # Burada borsapy (bp) kütüphanenizle tarama yaptığınızı varsayıyoruz.
    # Örnek olarak test amaçlı simüle edilmiştir.
    bulunan_hisseler = []
    
    # Gerçek tarama mantığınızı buraya entegre edebilirsiniz.
    # Örnek:
    # for hisse in ANA_PAZAR:
    #     if hisse_sinyal_verdi_mi(hisse):
    #         bulunan_hisseler.append(hisse)
    
    return bulunan_hisseler

if __name__ == "__main__":
    # Güvenli saat aralığı kontrolü (09:50 - 18:00)
    simdi = datetime.now(ISTANBUL)
    mevcut_saat_dk = simdi.hour * 60 + simdi.minute
    
    # Cumartesi (5) veya Pazar (6) ise çalışma
    if simdi.weekday() >= 5:
        print("Bugün hafta sonu. Tarama yapılmıyor.")
    # 09:50 (590 dk) ile 18:00 (1080 dk) arasındaysa çalıştır
    elif 590 <= mevcut_saat_dk <= 1080:
        bulunanlar = hisse_tarama_yap()
        
        if bulunanlar:
            gonderilenler = gonderilenleri_oku()
            yeni_hisseler = [h for h in bulunanlar if h not in gonderilenler]
            
            if yeni_hisseler:
                mesaj = f"🔔 *Yeni Sinyal Veren Hisseler:*\n" + "\n".join([f"📈 #{h}" for h in yeni_hisseler])
                telegram_mesaj_gonder(mesaj)
                gonderilenleri_kaydet(yeni_hisseler)
                aylik_gonderilenleri_kaydet(yeni_hisseler)
            else:
                print("Bulunan hisseler bugün zaten bildirilmiş.")
        else:
            print("Tarama sonucunda kriterlere uyan yeni hisse bulunamadı.")
    else:
        print(f"Şu an seans saatleri dışındayız ({simdi.strftime('%H:%M')}). İşlem yapılmadı.")
