import os
import borsapy as bp

print("====================================")
print("BIST TARAMA SISTEMI BASLADI")
print("====================================")

# BIST 100
xu100 = bp.Index("XU100")
bist100 = set(xu100.component_symbols)

print("BIST 100:", len(bist100), "hisse")

# Şimdilik Ana Pazar listesi ayrı dosyadan okunacak.
# Dosya bir sonraki adımda oluşturulacak.
ANA_PAZAR_DOSYASI = "ana_pazar.txt"

ana_pazar = set()

if os.path.exists(ANA_PAZAR_DOSYASI):

    with open(
        ANA_PAZAR_DOSYASI,
        "r",
        encoding="utf-8"
    ) as f:

        for satir in f:

            sembol = satir.strip().upper()

            if sembol:
                ana_pazar.add(sembol)

print("Ana Pazar:", len(ana_pazar), "hisse")

# BIST 100 + Ana Pazar
tarama_listesi = sorted(
    bist100 | ana_pazar
)

print(
    "TOPLAM TARAMA:",
    len(tarama_listesi),
    "hisse"
)

print("")
print("Ilk hisseler:")

for symbol in tarama_listesi[:20]:
    print(symbol)

print("")
print("LISTE TESTI BASARILI")
