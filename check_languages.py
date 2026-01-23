from services.models import Language

print("All Language records:")
print("-" * 80)
for lang in Language.objects.all():
    print(f"ID: {lang.id}")
    print(f"  Short: {lang.short_name}")
    print(f"  name_uz: {lang.name_uz}")
    print(f"  name_ru: {lang.name_ru}")
    print(f"  name_en: {lang.name_en}")
    print()
