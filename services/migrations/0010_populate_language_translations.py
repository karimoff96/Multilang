# Generated manually to populate translation fields from existing data

from django.db import migrations


def populate_translations(apps, schema_editor):
    """
    Copy existing 'name' values to name_en (English) field.
    Preserves any manually added translations in other fields.
    """
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Copy existing name values to name_en (original data was likely English)
        # Only update where name_en is NULL to avoid overwriting manual entries
        cursor.execute("""
            UPDATE services_language 
            SET name_en = name 
            WHERE name_en IS NULL AND name IS NOT NULL AND name != ''
        """)
        
        print(f"Populated {cursor.rowcount} language name_en fields from original name field")


def reverse_translations(apps, schema_editor):
    """
    Reverse operation - clear the translation fields
    """
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute("UPDATE services_language SET name_uz = NULL, name_ru = NULL, name_en = NULL")


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0009_language_name_en_language_name_ru_language_name_uz'),
    ]

    operations = [
        migrations.RunPython(populate_translations, reverse_translations),
    ]
