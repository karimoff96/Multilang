#!/usr/bin/env python
"""
Manual compilation of .po files to .mo files without gettext tools.
This script uses Python's built-in msgfmt.py from the Tools/i18n directory.
"""
import os
import sys
from pathlib import Path

def compile_po_file(po_file):
    """Compile a single .po file to .mo file."""
    mo_file = po_file.replace('.po', '.mo')
    
    try:
        # Import msgfmt from Python's tools
        # For Python 3.x, we can use polib or write a simple compiler
        import polib
        
        po = polib.pofile(po_file)
        po.save_as_mofile(mo_file)
        print(f"✓ Compiled: {po_file} -> {mo_file}")
        return True
    except ImportError:
        print("polib not found. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'polib'])
        
        # Try again
        import polib
        po = polib.pofile(po_file)
        po.save_as_mofile(mo_file)
        print(f"✓ Compiled: {po_file} -> {mo_file}")
        return True
    except Exception as e:
        print(f"✗ Error compiling {po_file}: {e}")
        return False

def main():
    """Find and compile all .po files in the locale directory."""
    locale_dir = Path(__file__).parent / 'locale'
    
    if not locale_dir.exists():
        print(f"Locale directory not found: {locale_dir}")
        return 1
    
    po_files = list(locale_dir.glob('*/LC_MESSAGES/django.po'))
    
    if not po_files:
        print("No .po files found")
        return 1
    
    print(f"Found {len(po_files)} .po file(s) to compile:\n")
    
    success_count = 0
    for po_file in po_files:
        if compile_po_file(str(po_file)):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"Compiled {success_count}/{len(po_files)} file(s) successfully")
    print(f"{'='*50}")
    
    return 0 if success_count == len(po_files) else 1

if __name__ == '__main__':
    sys.exit(main())
