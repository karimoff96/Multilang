#!/usr/bin/env python
"""
Simple script to compile .po files to .mo files without requiring Django settings.
This bypasses the dotenv import issue in settings.py
"""
import os
import struct
import array
from pathlib import Path

def generate_mo_file(po_file, mo_file):
    """
    Generate a .mo file from a .po file with proper charset handling
    """
    
    # Read and parse the .po file
    catalog = {}
    current_msgid = []
    current_msgstr = []
    in_msgid = False
    in_msgstr = False
    
    with open(po_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Handle msgid
            if line.startswith('msgid '):
                # Save previous entry
                if current_msgid or current_msgstr:
                    msgid_text = ''.join(current_msgid)
                    msgstr_text = ''.join(current_msgstr)
                    catalog[msgid_text] = msgstr_text
                
                # Start new entry
                text = line[7:-1] if line.endswith('"') and line[6] == '"' else ""
                current_msgid = [text]
                current_msgstr = []
                in_msgid = True
                in_msgstr = False
            
            # Handle msgstr
            elif line.startswith('msgstr '):
                text = line[8:-1] if line.endswith('"') and line[7] == '"' else ""
                current_msgstr = [text]
                in_msgid = False
                in_msgstr = True
            
            # Handle continuation lines
            elif line.startswith('"') and line.endswith('"'):
                text = line[1:-1].replace('\\n', '\n')  # Convert escaped newlines to actual newlines
                if in_msgid:
                    current_msgid.append(text)
                elif in_msgstr:
                    current_msgstr.append(text)
    
    # Add the last entry
    if current_msgid or current_msgstr:
        msgid_text = ''.join(current_msgid)
        msgstr_text = ''.join(current_msgstr)
        catalog[msgid_text] = msgstr_text
    
    # Ensure header exists with proper charset
    if '' not in catalog or 'charset=UTF-8' not in catalog.get('', ''):
        if '' in catalog:
            header = catalog['']
            if 'charset=' not in header:
                header += 'Content-Type: text/plain; charset=UTF-8\\n'
            catalog[''] = header
        else:
            catalog[''] = 'Content-Type: text/plain; charset=UTF-8\\n'
    
    # Convert to binary .mo format
    keys = sorted(catalog.keys())
    ids = [k.encode('utf-8') for k in keys]
    strs = [catalog[k].encode('utf-8') for k in keys]
    
    # Calculate offsets
    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + sum(len(k) + 1 for k in ids)
    
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
    
    # Generate the .mo file
    output = []
    
    # Magic number (little-endian)
    output.append(struct.pack('<I', 0x950412de))
    # Version
    output.append(struct.pack('<I', 0))
    # Number of entries
    output.append(struct.pack('<I', len(keys)))
    # Offset of table with original strings
    output.append(struct.pack('<I', 7 * 4))
    # Offset of table with translation strings
    output.append(struct.pack('<I', 7 * 4 + len(keys) * 8))
    # Size of hashing table
    output.append(struct.pack('<I', 0))
    # Offset of hashing table
    output.append(struct.pack('<I', 0))
    
    # Write the msgid offset table
    for length, offset in koffsets:
        output.append(struct.pack('<I', length))
        output.append(struct.pack('<I', offset))
    
    # Write the msgstr offset table
    for length, offset in voffsets:
        output.append(struct.pack('<I', length))
        output.append(struct.pack('<I', offset))
    
    # Write the msgids
    for k in ids:
        output.append(k)
        output.append(b'\x00')
    
    # Write the msgstrs
    for v in strs:
        output.append(v)
        output.append(b'\x00')
    
    # Write to file
    with open(mo_file, 'wb') as f:
        for item in output:
            f.write(item)

def compile_po_file(po_file):
    """Compile a single .po file to .mo file"""
    mo_file = po_file.with_suffix('.mo')
    print(f"Compiling {po_file.name}...")
    
    try:
        generate_mo_file(po_file, mo_file)
        print(f"✓ Successfully compiled {po_file.name}")
        return True
    except Exception as e:
        print(f"✗ Error compiling {po_file.name}: {e}")
        return False

def main():
    # Get the locale directory
    base_dir = Path(__file__).parent
    locale_dir = base_dir / 'locale'
    
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
        if compile_po_file(po_file):
            success_count += 1
        print()
    
    print(f"Compilation complete: {success_count}/{len(po_files)} files compiled successfully")

if __name__ == '__main__':
    main()
