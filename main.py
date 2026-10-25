        )

        fiyat = (
            sonuc["price"]
        )

        stop = (
            sonuc["stop"]
        )

        stop_fib = (
            sonuc["stop_fib"]
        )

        fibler = (
            sonuc["fib_levels"]
        )

        fiyat_fib = (
            sonuc["fiyat_fib"]
        )

        # =================================================
        # TELEGRAM MESAJI
        # =================================================

        mesaj = (

            f"🟢 YENİ : {symbol}"
            f"                   ADX "
            f"{adx_isaret} "
            f"{adx_deger:.1f}\n"

            f"⭐ Sinyal Gücü: "
            f"{sonuc['sinyal_gucu']}/100\n\n"

            f"💰 Giriş: "
            f"{fiyat:.2f} TL\n"

            f"{gunluk_isaret} Günlük: "
            f"{sonuc['daily_change']:+.2f}%\n"

            f"{hafta_isaret} 1 Hafta: "
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
            f"{pazar_adi}\n"

            f"🔊 Hacim: "
            f"{sonuc['volume'] / 1_000_000:.1f}M"
        )

        if telegram_gonder(mesaj):
            basariyla_gonderilenler.add(symbol)
            # Her başarılı mesajdan hemen sonra yerel kaydı güncelle.
            # İş akışı adımı tamamlandığında YAML bu dosyayı GitHub'a aktarır.
            gonderilenleri_kaydet({symbol})
        else:
            print(
                f"{symbol}: Telegram gönderimi başarısız; hisse gönderildi olarak kaydedilmedi."
            )

    if not basariyla_gonderilenler:
        print("Yeni gönderilen hisse yok.")


if __name__ == "__main__":

    main()
