import borsapy as bp

print("BIST VERI TESTI BASLADI")

try:
    stocks = bp.stocks()

    print("Hisse sayisi:", len(stocks))
    print(stocks.head())

    print("BIST VERI TESTI BASARILI")

except Exception as e:
    print("HATA:")
    print(type(e)._name_)
    print(str(e))
