"""
Compile .po files to .mo format using Python's built-in polib
No external tools required
"""
import os
import sys

# Try to import polib, install if not available
try:
    import polib
except ImportError:
    print("Installing polib...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'polib'])
    import polib

def compile_po_to_mo(po_file, mo_file):
    """Compile a .po file to .mo format"""
    try:
        po = polib.pofile(po_file)
        po.save_as_mofile(mo_file)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Compile both language files
project_dir = r'c:\Users\Doniyorbek\Desktop\Projects\Wow-dash'
os.chdir(project_dir)

languages = ['uz', 'ru', 'en']
success_count = 0

for lang in languages:
    po_path = f'locale/{lang}/LC_MESSAGES/django.po'
    mo_path = f'locale/{lang}/LC_MESSAGES/django.mo'
    
    if os.path.exists(po_path):
        print(f"Compiling {lang}...", end=' ')
        if compile_po_to_mo(po_path, mo_path):
            print(f"✓")
            success_count += 1
        else:
            print(f"✗")
    else:
        print(f"Skipping {lang} (file not found)")

print(f"\n{'='*60}")
print(f"✓ Compiled {success_count}/{len(languages)} language files successfully!")
print(f"{'='*60}")
print("\n⚠️  IMPORTANT: Restart your Django server for changes to take effect!")
print("   Run: python manage.py runserver")
