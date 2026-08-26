
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
