import os
import re

# Revert templates to use direct .name access (modeltranslation handles it automatically)
templates = [
    'templates/services/productList.html',
    'templates/services/productDetail.html',
    'templates/services/categoryList.html',
    'templates/services/expenseDetail.html',
    'templates/services/expenseList.html',
    'templates/services/languageList.html',
    'templates/reports/orders.html',
    'templates/reports/my_statistics.html',
    'templates/organizations/staff_detail.html',
    'templates/organizations/center_detail.html',
]

for template_path in templates:
    full_path = os.path.join(r'c:\Users\Doniyorbek\Desktop\Projects\Wow-dash', template_path)
    
    if not os.path.exists(full_path):
        print(f"⚠️  Skipped: {template_path} (not found)")
        continue
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Revert trans_name back to .name
    content = re.sub(r'\{\{\s*product\|trans_name', '{{ product.name', content)
    content = re.sub(r'\{\{\s*category\|trans_name', '{{ category.name', content)
    content = re.sub(r'\{\{\s*language\|trans_name', '{{ language.name', content)
    content = re.sub(r'\{\{\s*product\.category\|trans_name', '{{ product.category.name', content)
    content = re.sub(r'\{\{\s*order\.product\|trans_name', '{{ order.product.name', content)
    content = re.sub(r'\{\{\s*expense\.product\|trans_name', '{{ expense.product.name', content)
    
    # Fix the escaped newline issue in languageList
    if 'languageList' in template_path:
        content = content.replace('{% load i18n %}`n{% load translation_filters %}', '{% load i18n %}\n{% load translation_filters %}')
    
    if content != original:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Reverted: {template_path}")
    else:
        print(f"⏭️  Unchanged: {template_path}")

print("\n✅ Template reversion complete!")
print("🌍 Modeltranslation will now handle translations automatically")
print("   Product/Category/Language names will display in the current language")
