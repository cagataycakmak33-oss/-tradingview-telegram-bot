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
