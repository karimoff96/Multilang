from django.core.management.base import BaseCommand
from core.models import Region, District


class Command(BaseCommand):
    help = 'Setup Uzbekistan regions and districts'

    def handle(self, *args, **options):
        # Uzbekistan regions with their codes
        regions_data = [
            {'code': 'TAS', 'name_uz': 'Toshkent shahri', 'name_ru': 'Город Ташкент', 'name_en': 'Tashkent City'},
            {'code': 'TOS', 'name_uz': 'Toshkent viloyati', 'name_ru': 'Ташкентская область', 'name_en': 'Tashkent Region'},
            {'code': 'AND', 'name_uz': 'Andijon viloyati', 'name_ru': 'Андижанская область', 'name_en': 'Andijan Region'},
            {'code': 'BUX', 'name_uz': 'Buxoro viloyati', 'name_ru': 'Бухарская область', 'name_en': 'Bukhara Region'},
            {'code': 'FAR', 'name_uz': "Farg'ona viloyati", 'name_ru': 'Ферганская область', 'name_en': 'Fergana Region'},
            {'code': 'JIZ', 'name_uz': 'Jizzax viloyati', 'name_ru': 'Джизакская область', 'name_en': 'Jizzakh Region'},
            {'code': 'XOR', 'name_uz': 'Xorazm viloyati', 'name_ru': 'Хорезмская область', 'name_en': 'Khorezm Region'},
            {'code': 'NAM', 'name_uz': 'Namangan viloyati', 'name_ru': 'Наманганская область', 'name_en': 'Namangan Region'},
            {'code': 'NAV', 'name_uz': 'Navoiy viloyati', 'name_ru': 'Навоийская область', 'name_en': 'Navoiy Region'},
            {'code': 'QAS', 'name_uz': 'Qashqadaryo viloyati', 'name_ru': 'Кашкадарьинская область', 'name_en': 'Kashkadarya Region'},
            {'code': 'SAM', 'name_uz': 'Samarqand viloyati', 'name_ru': 'Самаркандская область', 'name_en': 'Samarkand Region'},
            {'code': 'SUR', 'name_uz': 'Surxondaryo viloyati', 'name_ru': 'Сурхандарьинская область', 'name_en': 'Surkhandarya Region'},
            {'code': 'SIR', 'name_uz': 'Sirdaryo viloyati', 'name_ru': 'Сырдарьинская область', 'name_en': 'Syrdarya Region'},
            {'code': 'QQR', 'name_uz': "Qoraqalpog'iston Respublikasi", 'name_ru': 'Республика Каракалпакстан', 'name_en': 'Republic of Karakalpakstan'},
        ]

        created_count = 0
        updated_count = 0

        for region_data in regions_data:
            region, created = Region.objects.update_or_create(
                code=region_data['code'],
                defaults={
                    'name_uz': region_data['name_uz'],
                    'name_ru': region_data['name_ru'],
                    'name_en': region_data['name_en'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created region: {region.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated region: {region.name}'))

        self.stdout.write(self.style.SUCCESS(
            f'Successfully setup regions! Created: {created_count}, Updated: {updated_count}'
        ))
        self.stdout.write(self.style.NOTICE(
            'Note: Districts can be added manually or via a separate data file.'
        ))
