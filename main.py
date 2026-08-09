import borsapy as bp

print("BIST VERI TESTI BASLADI")

try:
    hisse = bp.Ticker("THYAO")

    print("THYAO bilgisi alindi")

    veri = hisse.history(period="1mo")

    print("Veri satir sayisi:", len(veri))
    print(veri.tail())

    print("BIST VERI TESTI BASARILI")

except Exception as e:
    print("HATA TIPI:", type(e)._name_)
    print("HATA:", str(e))
