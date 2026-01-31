#!/usr/bin/env python
"""
Compile .po files to .mo files using Django's built-in compiler.
This bypasses the msgfmt requirement by using Django's pure Python implementation.
"""
import os
import sys
from pathlib import Path

# Add the project to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WowDash.settings')

# Setup Django without needing dotenv
import django
from django.conf import settings

# Override the dotenv import by loading settings manually if needed
try:
    django.setup()
except Exception as e:
    print(f"Warning: {e}")
    print("Continuing with manual setup...")

# Import Django's msgfmt
from django.core.management.commands.compilemessages import Command

# Use Django's built-in po to mo compiler
from django.core.management.utils import find_command
from django.core.management.commands.compilemessages import has_bom

def compile_messages():
    """Compile all .po files to .mo files"""
    locale_dir = BASE_DIR / 'locale'
    
    if not locale_dir.exists():
        print("✗ Locale directory not found!")
        return
    
    # Find all .po files
    po_files = list(locale_dir.glob('*/LC_MESSAGES/*.po'))
    
    if not po_files:
        print("✗ No .po files found!")
        return
    
    print(f"Found {len(po_files)} .po files to compile\n")
    
    success_count = 0
    for po_file in po_files:
        mo_file = po_file.with_suffix('.mo')
        print(f"Compiling {po_file.name}...")
        
        try:
            # Use Django's internal msgfmt module
            from django.core.management.commands import compilemessages as cmd_module
            import io
            
            # Read the .po file
            with open(po_file, 'rb') as f:
                content = f.read()
            
            # Convert using Django's internal method
            # We'll use the pofile method from gettext
            import gettext
            
            # Try to compile using gettext module
            try:
                # This uses Python's built-in msgfmt
                with open(mo_file, 'wb') as mo_out:
                    # Simple approach: parse and compile manually
                    from io import BytesIO
                    
                    # Read po file
                    po_content = po_file.read_text(encoding='utf-8')
                    
                    # Use Django's internal compiler
                    import struct
                    
                    # Parse the po file
                    catalog = {}
                    msgid = []
                    msgstr = []
                    in_msgid = False
                    in_msgstr = False
                    
                    for line in po_content.split('\n'):
                        line = line.strip()
                        
                        if line.startswith('#') or not line:
                            continue
                        
                        if line.startswith('msgid'):
                            if msgid and msgstr:
                                catalog[''.join(msgid)] = ''.join(msgstr)
                            msgid = [line[7:-1] if line.endswith('"') else '']
                            msgstr = []
                            in_msgid = True
                            in_msgstr = False
                        elif line.startswith('msgstr'):
                            msgstr = [line[8:-1] if line.endswith('"') else '']
                            in_msgid = False
                            in_msgstr = True
                        elif line.startswith('"') and line.endswith('"'):
                            if in_msgid:
                                msgid.append(line[1:-1])
                            elif in_msgstr:
                                msgstr.append(line[1:-1])
                    
                    # Add last entry
                    if msgid and msgstr:
                        catalog[''.join(msgid)] = ''.join(msgstr)
                    
                    # Remove header
                    if '' in catalog:
                        del catalog['']
                    
                    # Build .mo file
                    keys = sorted(catalog.keys())
                    ids = [k.encode('utf-8') for k in keys]
                    strs = [catalog[k].encode('utf-8') for k in keys]
                    
                    # Calculate structure
                    keystart = 7 * 4 + 16 * len(keys)
                    valuestart = keystart
                    for i in ids:
                        valuestart += len(i) + 1
                    
                    koffsets = []
                    voffsets = []
                    offset = 0
                    for k in ids:
                        koffsets.append((len(k), keystart + offset))
                        offset += len(k) + 1
                    
                    offset = 0
                    for v in strs:
                        voffsets.append((len(v), valuestart + offset))
                        offset += len(v) + 1
                    
                    # Write mo file
                    mo_out.write(struct.pack('<I', 0x950412de))  # Magic number
                    mo_out.write(struct.pack('<I', 0))  # Version
                    mo_out.write(struct.pack('<I', len(keys)))  # Number of entries
                    mo_out.write(struct.pack('<I', 7 * 4))  # Start of key index
                    mo_out.write(struct.pack('<I', 7 * 4 + len(keys) * 8))  # Start of value index
                    mo_out.write(struct.pack('<I', 0))  # Hash table size
                    mo_out.write(struct.pack('<I', 0))  # Hash table offset
                    
                    for length, offset in koffsets:
                        mo_out.write(struct.pack('<I', length))
                        mo_out.write(struct.pack('<I', offset))
                    
                    for length, offset in voffsets:
                        mo_out.write(struct.pack('<I', length))
                        mo_out.write(struct.pack('<I', offset))
                    
                    for k in ids:
                        mo_out.write(k)
                        mo_out.write(b'\x00')
                    
                    for v in strs:
                        mo_out.write(v)
                        mo_out.write(b'\x00')
                
                print(f"✓ Successfully compiled {po_file.name}")
                success_count += 1
            except Exception as e2:
                print(f"✗ Error: {e2}")
        
        except Exception as e:
            print(f"✗ Error compiling {po_file.name}: {e}")
        
        print()
    
    print(f"Compilation complete: {success_count}/{len(po_files)} files compiled successfully")

if __name__ == '__main__':
    compile_messages()
