import os
import re

# Templates to update
templates = [
    'templates/services/productList.html',
    'templates/services/productDetail.html',
    'templates/services/categoryList.html',
    'templates/services/categoryDetail.html',
    'templates/services/expenseDetail.html',
    'templates/services/expenseList.html',
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
    
    # Check if translation_filters is already loaded
    has_translation_filters = 'load translation_filters' in content
    
    # Add the load tag if missing
    if not has_translation_filters:
        # Add after other {% load %} tags
        if '{% load static %}' in content:
            content = content.replace('{% load static %}', '{% load static %}\n{% load translation_filters %}')
        elif '{% load i18n %}' in content:
            content = content.replace('{% load i18n %}', '{% load i18n %}\n{% load translation_filters %}')
        else:
            # Add at the beginning after extends
            content = re.sub(
                r"({% extends ['\"].*?['\"] %})",
                r"\1\n{% load translation_filters %}",
                content
            )
    
    # Replace product.name with product|trans_name
    # But exclude cases where it's in forms (value="{{ product.name_uz }}")
    content = re.sub(
        r'\{\{\s*product\.name(?!\w)(?!\|trans_name)',
        r'{{ product|trans_name',
        content
    )
    
    # Replace category.name with category|trans_name
    content = re.sub(
        r'\{\{\s*category\.name(?!\w)(?!\|trans_name)',
        r'{{ category|trans_name',
        content
    )
    
    # Replace product.category.name with product.category|trans_name
    content = re.sub(
        r'\{\{\s*product\.category\.name(?!\w)(?!\|trans_name)',
        r'{{ product.category|trans_name',
        content
    )
    
    # Replace order.product.name with order.product|trans_name
    content = re.sub(
        r'\{\{\s*order\.product\.name(?!\w)(?!\|trans_name)',
        r'{{ order.product|trans_name',
        content
    )
    
    # Replace expense.product.name
    content = re.sub(
        r'\{\{\s*expense\.product\.name(?!\w)(?!\|trans_name)',
        r'{{ expense.product|trans_name',
        content
    )
    
    if content != original:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated: {template_path}")
    else:
        print(f"⏭️  Unchanged: {template_path}")

print("\n✅ Template updates complete!")
print("🌍 Product and category names will now display in the selected UI language")
