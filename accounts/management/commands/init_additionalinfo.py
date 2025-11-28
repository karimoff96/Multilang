from django.core.management.base import BaseCommand
from accounts.models import AdditionalInfo


class Command(BaseCommand):
    help = "Initialize or update AdditionalInfo content with default values"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset all content to default values",
        )

    def handle(self, *args, **options):
        try:
            # Get the first (and should be only) AdditionalInfo record
            additional_info = AdditionalInfo.objects.first()

            if not additional_info:
                # Only create if no record exists
                additional_info = AdditionalInfo.objects.create(
                    bank_card=None,
                    holder_name="",
                    help_text="",
                    help_text_uz="📞 Savollaringiz bo'lsa, admin bilan bog'laning\n🌐 Til o'zgartirish: /start\n📋 Buyurtma berish: Hizmatdan foydalanish",
                    help_text_ru="📞 Если у вас есть вопросы, свяжитесь с администратором\n🌐 Сменить язык: /start\n📋 Сделать заказ: Воспользоваться услугой",
                    help_text_en="📞 If you have questions, contact administrator\n🌐 Change language: /start\n📋 Place order: Use Service",
                    about_us="",
                    about_us_uz="📞 Savollaringiz bo'lsa, admin bilan bog'laning\n🌐 Kompaniyamiz haqida ko'proq ma'lumot tez kunda qo'shiladi!",
                    about_us_ru="📞 Если у вас есть вопросы, свяжитесь с администратором\n🌐 Информация о нашей компании будет добавлена в ближайшее время!",
                    about_us_en="📞 If you have questions, contact administrator\n🌐 Information about our company will be added soon!",
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        "✅ Created new AdditionalInfo record with default content"
                    )
                )
            else:
                if options["reset"]:
                    # Update existing record with default values
                    additional_info.help_text_uz = "📞 Savollaringiz bo'lsa, admin bilan bog'laning\n🌐 Til o'zgartirish: /start\n📋 Buyurtma berish: Hizmatdan foydalanish"
                    additional_info.help_text_ru = "📞 Если у вас есть вопросы, свяжитесь с администратором\n🌐 Сменить язык: /start\n📋 Сделать заказ: Воспользоваться услугой"
                    additional_info.help_text_en = "📞 If you have questions, contact administrator\n🌐 Change language: /start\n📋 Place order: Use Service"
                    additional_info.about_us_uz = "📞 Savollaringiz bo'lsa, admin bilan bog'laning\n🌐 Kompaniyamiz haqida ko'proq ma'lumot tez kunda qo'shiladi!"
                    additional_info.about_us_ru = "📞 Если у вас есть вопросы, свяжитесь с администратором\n🌐 Информация о нашей компании будет добавлена в ближайшее время!"
                    additional_info.about_us_en = "📞 If you have questions, contact administrator\n🌐 Information about our company will be added soon!"
                    additional_info.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            "✅ Reset existing AdditionalInfo content to default values"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✅ AdditionalInfo record already exists")
                    )

            # Show current content
            self.stdout.write("\n📋 Current AdditionalInfo content:")
            self.stdout.write(
                f"   🇺🇿 Uzbek (Help): {additional_info.help_text_uz[:50]}..."
                if additional_info.help_text_uz
                else "   🇺🇿 Uzbek (Help): [Empty]"
            )
            self.stdout.write(
                f"   🇷🇺 Russian (Help): {additional_info.help_text_ru[:50]}..."
                if additional_info.help_text_ru
                else "   🇷🇺 Russian (Help): [Empty]"
            )
            self.stdout.write(
                f"   🇬🇧 English (Help): {additional_info.help_text_en[:50]}..."
                if additional_info.help_text_en
                else "   🇬🇧 English (Help): [Empty]"
            )
            self.stdout.write(
                f"   🇺🇿 Uzbek (About): {additional_info.about_us_uz[:50]}..."
                if additional_info.about_us_uz
                else "   🇺🇿 Uzbek (About): [Empty]"
            )
            self.stdout.write(
                f"   🇷🇺 Russian (About): {additional_info.about_us_ru[:50]}..."
                if additional_info.about_us_ru
                else "   🇷🇺 Russian (About): [Empty]"
            )
            self.stdout.write(
                f"   🇬🇧 English (About): {additional_info.about_us_en[:50]}..."
                if additional_info.about_us_en
                else "   🇬🇧 English (About): [Empty]"
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "\n🎯 You can edit this content in Django Admin: /admin/users/additionalinfo/"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to initialize AdditionalInfo: {e}")
            )
