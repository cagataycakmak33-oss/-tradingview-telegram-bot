
                # Aynı dakikada tekrar başlatma
                # engeli
                mevcut_slot = (
                    simdi.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                )

                if (
                    son_tarama_tarihi
                    !=
                    mevcut_slot
                ):

                    print(
                        "\n⏰ PLANLI ÇALIŞMA ZAMANI"
                    )

                    print(
                        "🕐",
                        simdi.strftime(
                            "%d.%m.%Y %H:%M:%S"
                        )
                    )

                    print(
                        "📌 Dönem:",
                        tarama_donemi()
                    )

                    # Taramayı başlat
                    tek_tarama()

                    # Bu taramanın slotunu kaydet
                    son_tarama_tarihi = mevcut_slot

                    print(
                        "\n⏳ Bir sonraki planlı tarama bekleniyor..."
                    )

                # ------------------------------------------------
                # Bir sonraki 5 dakikalık saat dilimine hizalan.
                # Tarama süresi uzarsa ikinci tarama üst üste başlamaz.
                # ------------------------------------------------
                simdi_son = datetime.now(ISTANBUL)
                dakika_sonraki = (
                    (simdi_son.minute // TARAMA_ARALIGI_DAKIKA) + 1
                ) * TARAMA_ARALIGI_DAKIKA
                if dakika_sonraki >= 60:
                    sonraki_slot = simdi_son.replace(
                        minute=0, second=0, microsecond=0
                    ) + timedelta(hours=1)
                else:
                    sonraki_slot = simdi_son.replace(
                        minute=dakika_sonraki, second=0, microsecond=0
                    )
                bekleme = max(
                    1,
                    int((sonraki_slot - datetime.now(ISTANBUL)).total_seconds())
                )
                print(
                    f"⏱️ Sonraki tarama slotu: {sonraki_slot.strftime('%H:%M:%S')} "
                    f"({bekleme} sn bekleme)"
                )
                time.sleep(bekleme)

                continue

            # ------------------------------------------------
            # AKTİF ÇALIŞMA DIŞI
            # ------------------------------------------------

            sonraki = (
                sonraki_tarama_zamani_hesapla()
            )

            print(
                "\r"
                f"💤 Beklemede | "
                f"Saat: {now.strftime('%H:%M:%S')} | "
                f"Sonraki tarama: "
                f"{sonraki.strftime('%d.%m %H:%M')}",
                end="",
                flush=True
            )

            # 30 saniyede bir kontrol
            time.sleep(30)

        except KeyboardInterrupt:

            print(
                "\n\n🛑 Bot kullanıcı tarafından durduruldu."
            )

            break

        except Exception as hata:

            print(
                "\n\n🚨 SCHEDULER HATASI:",
                type(hata).__name__,
                str(hata)
            )

            print(
                "⏳ 60 saniye sonra tekrar denenecek..."
            )

            time.sleep(60)


# ============================================================
# ÇALIŞTIR
# ============================================================

if __name__ == "__main__":
