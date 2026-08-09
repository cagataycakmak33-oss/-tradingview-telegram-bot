import os
import requests
import borsapy as bp
import pandas as pd
from io import BytesIO
from pypdf import PdfReader
from datetime import datetime
from zoneinfo import ZoneInfo


PDF_URL = "https://www.borsaistanbul.com/files/duyuru-48375-TR.pdf"

print("====================================")
print("BIST 100 + ANA PAZAR TESTI")
print("====================================")


# -------------------------------------------------
# BIST 100
# -------------------------------------------------

xu100 = bp.Index("XU100")

bist100 = set(
    symbol.upper()
    for symbol in xu100.component_symbols
)

print("BIST 100:", len(bist100))


# -------------------------------------------------
# RESMI BORSA ISTANBUL PDF
# -------------------------------------------------

print("Borsa Istanbul resmi liste indiriliyor...")

response = requests.get(
    PDF_URL,
    timeout=30
)

response.raise_for_status()

reader = PdfReader(
    BytesIO(response.content)
)

# Ana Pazar listesini PDF'den çıkar
ana_pazar = set()

for page in reader.pages:

    text = page.extract_text() or ""

    # PDF'nin Ana Pazar bölümündeki sembolleri
    # daha sonra güvenli şekilde ayrıştıracağız.
    lines = text.splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Sadece BIST sembol formatına benzeyen
        # kelimeleri al
        kelimeler = line.split()

        for kelime in kelimeler:

            kelime = kelime.upper().strip()

            if (
                3 <= len(kelime) <= 6
                and kelime.isalnum()
            ):
                ana_pazar.add(kelime)


print(
    "PDF'den bulunan sembol sayisi:",
    len(ana_pazar)
)


# -------------------------------------------------
# ONEMLI:
# BIST 100 + ANA PAZAR
# -------------------------------------------------

tarama_listesi = sorted(
    bist100 | ana_pazar
)


print(
    "Toplam aday sembol:",
    len(tarama_listesi)
)

print("")
print("Ilk 30 sembol:")

for symbol in tarama_listesi[:30]:
    print(symbol)


print("")
print("====================================")
print("TEST TAMAMLANDI")
print("====================================")
