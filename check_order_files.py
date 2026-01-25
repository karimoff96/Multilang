"""
Diagnostic script to check order files
Run with: python manage.py shell < check_order_files.py
Or in Django shell: exec(open('check_order_files.py').read())
"""

from orders.models import Order, OrderMedia
from django.core.files.storage import default_storage
import os

order_id = 1083

print(f"\n{'='*80}")
print(f"Checking Order #{order_id}")
print(f"{'='*80}\n")

try:
    order = Order.objects.get(id=order_id)
    print(f"Order Status: {order.status}")
    print(f"Total Pages: {order.total_pages}")
    print(f"Created: {order.created_at}")
    print(f"\n{'='*80}")
    print(f"FILES ATTACHED TO THIS ORDER:")
    print(f"{'='*80}\n")
    
    files = order.files.all()
    print(f"Total files: {files.count()}\n")
    
    for idx, file_obj in enumerate(files, 1):
        print(f"\n--- File #{idx} (OrderMedia ID: {file_obj.id}) ---")
        print(f"Pages: {file_obj.pages}")
        print(f"Created: {file_obj.created_at}")
        print(f"Telegram File ID: {file_obj.telegram_file_id}")
        
        # Raw file field value
        raw_path = str(file_obj.file) if file_obj.file else "EMPTY"
        print(f"\nRAW file field value:")
        print(f"  '{raw_path}'")
        print(f"  Length: {len(raw_path)} characters")
        
        # Check for corruption patterns
        has_agac = 'AgAC' in raw_path
        has_baac = 'BAAC' in raw_path
        print(f"\nCorruption check:")
        print(f"  Contains 'AgAC': {has_agac}")
        print(f"  Contains 'BAAC': {has_baac}")
        print(f"  Is corrupted: {has_agac or has_baac}")
        
        # Try to get file.name
        try:
            file_name = file_obj.file.name if file_obj.file else "N/A"
            print(f"\nfile.name: {file_name}")
        except Exception as e:
            print(f"\nERROR getting file.name: {e}")
        
        # Check if file exists on disk
        if file_obj.file and raw_path and raw_path != 'EMPTY':
            exists = default_storage.exists(raw_path)
            print(f"\nFile exists on disk: {exists}")
            
            if exists:
                size = default_storage.size(raw_path)
                print(f"File size: {size} bytes ({size/1024:.2f} KB)")
        
        # Try to get URL
        try:
            url = file_obj.file.url if file_obj.file else None
            print(f"\nfile.url: {url}")
        except Exception as e:
            print(f"\nERROR getting file.url: {e}")
        
        print(f"\n{'-'*80}")
    
    print(f"\n{'='*80}")
    print("DIAGNOSIS COMPLETE")
    print(f"{'='*80}\n")
    
except Order.DoesNotExist:
    print(f"ERROR: Order #{order_id} does not exist!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
