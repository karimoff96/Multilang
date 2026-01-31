#!/usr/bin/env python
"""
Translation Utilities
=====================

Consolidated script for translation-related tasks.

Commands:
    compile         Compile all .po files to .mo files
    translate       Auto-translate missing translations (requires API key)
    check           Check for missing translations

Usage:
    python scripts/translation_utils.py [command]
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOCALE_DIR = BASE_DIR / 'locale'


def compile_messages():
    """Compile all .po files to .mo files"""
    print("📦 Compiling translation messages...")
    
    languages = ['ru', 'uz', 'en']
    
    for lang in languages:
        po_file = LOCALE_DIR / lang / 'LC_MESSAGES' / 'django.po'
        
        if po_file.exists():
            print(f"  ✓ Compiling {lang}...")
            result = subprocess.run(
                ['django-admin', 'compilemessages', '-l', lang],
                cwd=BASE_DIR,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"    ✅ {lang} compiled successfully")
            else:
                print(f"    ❌ Error compiling {lang}: {result.stderr}")
        else:
            print(f"  ⚠️  {lang} .po file not found")
    
    print("\n✅ Compilation complete!")


def check_translations():
    """Check for missing translations"""
    print("🔍 Checking for missing translations...")
    
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WowDash.settings')
    django.setup()
    
    from django.utils.translation import gettext_lazy as _
    
    # This would need to be implemented based on your specific needs
    print("  ℹ️  Manual check required - review .po files for 'fuzzy' or empty msgstr")


def main():
    """Main command handler"""
    commands = {
        'compile': compile_messages,
        'check': check_translations,
    }
    
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nAvailable commands:")
        for cmd in commands.keys():
            print(f"  - {cmd}")
        return 1
    
    command = sys.argv[1]
    
    if command not in commands:
        print(f"❌ Unknown command: {command}")
        return 1
    
    try:
        commands[command]()
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
