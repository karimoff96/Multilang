#!/usr/bin/env python
"""
Automated translation script for .po files
Translates all empty msgstr entries to Uzbek and Russian
"""

# Translation dictionaries - English to Uzbek and Russian
UZ_TRANSLATIONS = {
    # Status and action words
    "Draft": "Qoralama",
    "Scheduled": "Rejalashtirilgan",
    "Sending": "Yuborilmoqda",
    "Sent": "Yuborildi",
    "Paused": "To'xtatilgan",
    "Failed": "Muvaffaqiyatsiz",
    "Cancelled": "Bekor qilindi",
    "Pending": "Kutilmoqda",
    "Delivered": "Yetkazildi",
    "Blocked by User": "Foydalanuvchi tomonidan bloklangan",
    "Skipped (Opted Out)": "O'tkazib yuborilgan (Rad etilgan)",
    
    # Marketing content types
    "Text Only": "Faqat matn",
    "Photo with Caption": "Izoh bilan rasm",
    "Video with Caption": "Izoh bilan video",
    "Document with Caption": "Izoh bilan hujjat",
    
    # Marketing fields
    "Internal title for identification": "Identifikatsiya uchun ichki sarlavha",
    "Message Content": "Xabar tarkibi",
    "Message text (supports HTML: <b>, <i>, <a>, <code>)": "Xabar matni (HTML qo'llab-quvvatlaydi: <b>, <i>, <a>, <code>)",
    "Media File": "Media fayl",
    "Image, video, or document to send with message": "Xabar bilan birga yuborish uchun rasm, video yoki hujjat",
    "Target Scope": "Maqsadli ko'lam",
    "Target Center": "Maqsadli markaz",
    "Required for center/branch scope": "Markaz/filial ko'lami uchun talab qilinadi",
    "Target Branch": "Maqsadli filial",
    "Required for branch scope": "Filial ko'lami uchun talab qilinadi",
    "Include B2C Customers": "B2C mijozlarni qo'shish",
    "Send to individual customers": "Yakka mijozlarga yuborish",
    "Include B2B Customers": "B2B mijozlarni qo'shish",
    "Send to agency customers": "Agentlik mijozlariga yuborish",
    "Scheduled Time": "Rejalashtirilgan vaqt",
    "Leave empty to send immediately": "Darhol yuborish uchun bo'sh qoldiring",
    "Total Recipients": "Jami qabul qiluvchilar",
    "Sent Count": "Yuborilganlar soni",
    "Delivered Count": "Yetkazilganlar soni",
    "Failed Count": "Muvaffaqiyatsiz soni",
    "Created By": "Yaratgan",
    "Sent At": "Yuborilgan vaqt",
    "Completed At": "Bajarilgan vaqt",
    "Last Error": "Oxirgi xato",
    "Marketing Post": "Marketing post",
    "Marketing Posts": "Marketing postlar",
    "All Platform Users": "Barcha platforma foydalanuvchilari",
    "Recipient": "Qabul qiluvchi",
    "Telegram Message ID": "Telegram xabar ID",
    "Error Message": "Xato xabari",
    "Retry Count": "Qayta urinishlar soni",
    "Broadcast Recipient": "Eshittirish qabul qiluvchisi",
    "Broadcast Recipients": "Eshittirish qabul qiluvchilari",
    "Receive Marketing Messages": "Marketing xabarlarini qabul qilish",
    "User can opt out of marketing messages": "Foydalanuvchi marketing xabarlaridan voz kechishi mumkin",
    "Receive Promotions": "Reklama xabarlarini qabul qilish",
    "Receive Updates": "Yangilanishlarni qabul qilish",
    "Last Broadcast Received": "Oxirgi qabul qilingan eshittirish",
    "User Broadcast Preference": "Foydalanuvchi eshittirish sozlamalari",
    "User Broadcast Preferences": "Foydalanuvchi eshittirish sozlamalari",
    "Messages Per Second": "Soniyada xabarlar",
    "Max messages per second (Telegram limit: 30)": "Soniyada maksimal xabarlar (Telegram cheklovi: 30)",
    "Daily Limit Per User": "Foydalanuvchi uchun kunlik limit",
    "Max broadcasts per user per day": "Foydalanuvchi uchun kunlik maksimal eshittirishlar",
    "Batch Size": "Partiya hajmi",
    "Batch Delay (seconds)": "Partiya kechikishi (soniya)",
    "Broadcast Rate Limit": "Eshittirish tezlik limiti",
    "Broadcast Rate Limits": "Eshittirish tezlik limitlari",
    "Broadcast & Promotions": "Eshittirish va reklamalar",
    
    # Order fields
    "Pages": "Sahifalar",
    "Order file": "Buyurtma fayli",
    "Order media": "Buyurtma mediasi",
    "Received": "Qabul qilindi",
    "Cash": "Naqd",
    "Card": "Karta",
    "Document Type": "Hujjat turi",
    "Total Pages": "Jami sahifalar",
    "Translation Language": "Tarjima tili",
    "The target language selected by user from category's available languages": "Foydalanuvchi kategoriyaning mavjud tillaridan tanlagan maqsadli til",
    "Payment Type": "To'lov turi",
    "Receipt": "Kvitansiya",
    "Receipts": "Kvitansiyalar",
    "Total Price": "Jami narx",
    "Number of Copies": "Nusxalar soni",
    "Additional copies needed (0 means only original)": "Qo'shimcha nusxalar kerak (0 faqat asl nusxani anglatadi)",
    "Files": "Fayllar",
    "Assigned To": "Tayinlangan",
    "Assigned By": "Tayinlagan",
    "Assigned At": "Tayinlangan vaqt",
    "Payment Received By": "To'lovni qabul qilgan",
    "Payment Received At": "To'lov qabul qilingan vaqt",
    "Amount Received": "Qabul qilingan summa",
    "Total amount received so far": "Hozircha qabul qilingan jami summa",
    "Extra Fee": "Qo'shimcha to'lov",
    "Additional charges (rush fee, special handling, etc.)": "Qo'shimcha to'lovlar (shoshilinch to'lov, maxsus xizmat va boshqalar)",
    "Extra Fee Description": "Qo'shimcha to'lov tavsifi",
    "Reason for the extra fee": "Qo'shimcha to'lov sababi",
    "Payment Accepted Fully": "To'lov to'liq qabul qilindi",
    "Mark as True to consider payment complete regardless of received amount": "Qabul qilingan summaga qaramay to'lovni to'liq deb hisoblash uchun True deb belgilang",
    "Completed By": "Bajargan",
    "Selected language is not available for this product's category.": "Tanlangan til ushbu mahsulot kategoriyasi uchun mavjud emas.",
    "Order": "Buyurtma",
    "Orders": "Buyurtmalar",
    "Bot (User Upload)": "Bot (Foydalanuvchi yukladi)",
    "Admin Upload": "Admin yukladi",
    "Phone Confirmation": "Telefon tasdiqlash",
    "Pending Verification": "Tekshirish kutilmoqda",
    "Verified": "Tasdiqlandi",
    "Rejected": "Rad etildi",
    "Receipt File": "Kvitansiya fayli",
    "Receipt image or document": "Kvitansiya rasmi yoki hujjati",
    "Telegram File ID": "Telegram fayl ID",
    "File ID from Telegram for quick access": "Tez kirish uchun Telegram fayl ID",
    "Amount": "Summa",
    "Amount claimed in this receipt": "Ushbu kvitansiyada da'vo qilingan summa",
    "Verified Amount": "Tasdiqlangan summa",
    "Amount verified by admin": "Admin tomonidan tasdiqlangan summa",
    "Source": "Manba",
    "Comment": "Izoh",
    "Admin notes or rejection reason": "Admin izohlari yoki rad etish sababi",
    "Uploaded By (User)": "Yuklagan (Foydalanuvchi)",
    "Verified By": "Tasdiqlagan",
    "Verified At": "Tasdiqlangan vaqt",
    "Please fill in all required fields": "Barcha majburiy maydonlarni to'ldiring",
    "Order created successfully": "Buyurtma muvaffaqiyatli yaratildi",
    
    # Organization fields
    "Subdomain": "Subdomen",
    "Unique subdomain for this center (e.g., 'center1' for center1.alltranslation.uz)": "Ushbu markaz uchun noyob subdomen (masalan, center1.alltranslation.uz uchun 'center1')",
    "Owner": "Egasi",
    "Logo": "Logotip",
    "Address": "Manzil",
    "Phone": "Telefon",
    "Email": "Email",
    "Location URL": "Joylashuv URL",
    "Google Maps or Yandex Maps URL": "Google Maps yoki Yandex Maps URL",
    "Bot Token": "Bot tokeni",
    "Telegram Bot Token for this center (unique, superuser only)": "Ushbu markaz uchun Telegram Bot tokeni (noyob, faqat superuser)",
    "Company Orders Channel ID": "Kompaniya buyurtmalari kanal ID",
    "Telegram channel ID for all company orders": "Barcha kompaniya buyurtmalari uchun Telegram kanal ID",
    "Translation Centers": "Tarjima markazlari",
    "Cannot delete center with active bot token. Remove the bot token first.": "Faol bot tokeni bilan markazni o'chirib bo'lmaydi. Avval bot tokenini olib tashlang.",
    "Main Branch": "Asosiy filial",
    "B2C Orders Channel ID": "B2C buyurtmalar kanal ID",
    "Telegram channel ID for B2C (individual customer) orders": "B2C (yakka mijoz) buyurtmalari uchun Telegram kanal ID",
    "B2B Orders Channel ID": "B2B buyurtmalar kanal ID",
    "Telegram channel ID for B2B (agency/business) orders": "B2B (agentlik/biznes) buyurtmalari uchun Telegram kanal ID",
    "Show Price List": "Narxlar ro'yxatini ko'rsatish",
    "Show price list button in Telegram bot for this branch": "Ushbu filial uchun Telegram botda narxlar ro'yxati tugmasini ko'rsatish",
    "Branches": "Filiallar",
    "Display Name": "Ko'rsatiladigan nom",
    "System Role": "Tizim roli",
    "System roles cannot be deleted": "Tizim rollarini o'chirib bo'lmaydi",
}

RU_TRANSLATIONS = {
    # Status and action words
    "Draft": "Черновик",
    "Scheduled": "Запланировано",
    "Sending": "Отправка",
    "Sent": "Отправлено",
    "Paused": "Приостановлено",
    "Failed": "Не удалось",
    "Cancelled": "Отменено",
    "Pending": "Ожидание",
    "Delivered": "Доставлено",
    "Blocked by User": "Заблокировано пользователем",
    "Skipped (Opted Out)": "Пропущено (Отказался)",
    
    # Marketing content types
    "Text Only": "Только текст",
    "Photo with Caption": "Фото с подписью",
    "Video with Caption": "Видео с подписью",
    "Document with Caption": "Документ с подписью",
    
    # Marketing fields
    "Internal title for identification": "Внутренний заголовок для идентификации",
    "Message Content": "Содержание сообщения",
    "Message text (supports HTML: <b>, <i>, <a>, <code>)": "Текст сообщения (поддерживает HTML: <b>, <i>, <a>, <code>)",
    "Media File": "Медиа файл",
    "Image, video, or document to send with message": "Изображение, видео или документ для отправки с сообщением",
    "Target Scope": "Целевая область",
    "Target Center": "Целевой центр",
    "Required for center/branch scope": "Обязательно для области центра/филиала",
    "Target Branch": "Целевой филиал",
    "Required for branch scope": "Обязательно для области филиала",
    "Include B2C Customers": "Включить B2C клиентов",
    "Send to individual customers": "Отправить индивидуальным клиентам",
    "Include B2B Customers": "Включить B2B клиентов",
    "Send to agency customers": "Отправить клиентам агентства",
    "Scheduled Time": "Запланированное время",
    "Leave empty to send immediately": "Оставьте пустым для немедленной отправки",
    "Total Recipients": "Всего получателей",
    "Sent Count": "Количество отправленных",
    "Delivered Count": "Количество доставленных",
    "Failed Count": "Количество неудачных",
    "Created By": "Создано",
    "Sent At": "Отправлено в",
    "Completed At": "Завершено в",
    "Last Error": "Последняя ошибка",
    "Marketing Post": "Маркетинговый пост",
    "Marketing Posts": "Маркетинговые посты",
    "All Platform Users": "Все пользователи платформы",
    "Recipient": "Получатель",
    "Telegram Message ID": "ID сообщения Telegram",
    "Error Message": "Сообщение об ошибке",
    "Retry Count": "Количество повторов",
    "Broadcast Recipient": "Получатель рассылки",
    "Broadcast Recipients": "Получатели рассылки",
    "Receive Marketing Messages": "Получать маркетинговые сообщения",
    "User can opt out of marketing messages": "Пользователь может отказаться от маркетинговых сообщений",
    "Receive Promotions": "Получать промоакции",
    "Receive Updates": "Получать обновления",
    "Last Broadcast Received": "Последняя полученная рассылка",
    "User Broadcast Preference": "Предпочтения рассылки пользователя",
    "User Broadcast Preferences": "Предпочтения рассылки пользователя",
    "Messages Per Second": "Сообщений в секунду",
    "Max messages per second (Telegram limit: 30)": "Максимум сообщений в секунду (лимит Telegram: 30)",
    "Daily Limit Per User": "Дневной лимит на пользователя",
    "Max broadcasts per user per day": "Максимум рассылок на пользователя в день",
    "Batch Size": "Размер пакета",
    "Batch Delay (seconds)": "Задержка пакета (секунды)",
    "Broadcast Rate Limit": "Лимит скорости рассылки",
    "Broadcast Rate Limits": "Лимиты скорости рассылки",
    "Broadcast & Promotions": "Рассылки и промоакции",
    
    # Order fields
    "Pages": "Страницы",
    "Order file": "Файл заказа",
    "Order media": "Медиа заказа",
    "Received": "Получено",
    "Cash": "Наличные",
    "Card": "Карта",
    "Document Type": "Тип документа",
    "Total Pages": "Всего страниц",
    "Translation Language": "Язык перевода",
    "The target language selected by user from category's available languages": "Целевой язык, выбранный пользователем из доступных языков категории",
    "Payment Type": "Тип оплаты",
    "Receipt": "Квитанция",
    "Receipts": "Квитанции",
    "Total Price": "Общая цена",
    "Number of Copies": "Количество копий",
    "Additional copies needed (0 means only original)": "Требуется дополнительных копий (0 означает только оригинал)",
    "Files": "Файлы",
    "Assigned To": "Назначено",
    "Assigned By": "Назначил",
    "Assigned At": "Назначено в",
    "Payment Received By": "Платеж получен",
    "Payment Received At": "Платеж получен в",
    "Amount Received": "Полученная сумма",
    "Total amount received so far": "Общая сумма, полученная на данный момент",
    "Extra Fee": "Дополнительная плата",
    "Additional charges (rush fee, special handling, etc.)": "Дополнительные сборы (срочная плата, специальная обработка и т.д.)",
    "Extra Fee Description": "Описание дополнительной платы",
    "Reason for the extra fee": "Причина дополнительной платы",
    "Payment Accepted Fully": "Платеж полностью принят",
    "Mark as True to consider payment complete regardless of received amount": "Отметьте как True, чтобы считать платеж завершенным независимо от полученной суммы",
    "Completed By": "Выполнено",
    "Selected language is not available for this product's category.": "Выбранный язык недоступен для категории этого продукта.",
    "Order": "Заказ",
    "Orders": "Заказы",
    "Bot (User Upload)": "Бот (Загрузка пользователя)",
    "Admin Upload": "Загрузка администратора",
    "Phone Confirmation": "Подтверждение по телефону",
    "Pending Verification": "Ожидает проверки",
    "Verified": "Проверено",
    "Rejected": "Отклонено",
    "Receipt File": "Файл квитанции",
    "Receipt image or document": "Изображение или документ квитанции",
    "Telegram File ID": "ID файла Telegram",
    "File ID from Telegram for quick access": "ID файла из Telegram для быстрого доступа",
    "Amount": "Сумма",
    "Amount claimed in this receipt": "Сумма, указанная в этой квитанции",
    "Verified Amount": "Подтвержденная сумма",
    "Amount verified by admin": "Сумма, подтвержденная администратором",
    "Source": "Источник",
    "Comment": "Комментарий",
    "Admin notes or rejection reason": "Заметки администратора или причина отклонения",
    "Uploaded By (User)": "Загружено (Пользователь)",
    "Verified By": "Проверено",
    "Verified At": "Проверено в",
    "Please fill in all required fields": "Пожалуйста, заполните все обязательные поля",
    "Order created successfully": "Заказ успешно создан",
    
    # Organization fields
    "Subdomain": "Поддомен",
    "Unique subdomain for this center (e.g., 'center1' for center1.alltranslation.uz)": "Уникальный поддомен для этого центра (например, 'center1' для center1.alltranslation.uz)",
    "Owner": "Владелец",
    "Logo": "Логотип",
    "Address": "Адрес",
    "Phone": "Телефон",
    "Email": "Email",
    "Location URL": "URL местоположения",
    "Google Maps or Yandex Maps URL": "URL Google Maps или Yandex Maps",
    "Bot Token": "Токен бота",
    "Telegram Bot Token for this center (unique, superuser only)": "Токен Telegram бота для этого центра (уникальный, только суперпользователь)",
    "Company Orders Channel ID": "ID канала заказов компании",
    "Telegram channel ID for all company orders": "ID канала Telegram для всех заказов компании",
    "Translation Centers": "Центры перевода",
    "Cannot delete center with active bot token. Remove the bot token first.": "Невозможно удалить центр с активным токеном бота. Сначала удалите токен бота.",
    "Main Branch": "Главный филиал",
    "B2C Orders Channel ID": "ID канала заказов B2C",
    "Telegram channel ID for B2C (individual customer) orders": "ID канала Telegram для заказов B2C (индивидуальные клиенты)",
    "B2B Orders Channel ID": "ID канала заказов B2B",
    "Telegram channel ID for B2B (agency/business) orders": "ID канала Telegram для заказов B2B (агентство/бизнес)",
    "Show Price List": "Показать прайс-лист",
    "Show price list button in Telegram bot for this branch": "Показать кнопку прайс-листа в Telegram боте для этого филиала",
    "Branches": "Филиалы",
    "Display Name": "Отображаемое имя",
    "System Role": "Системная роль",
    "System roles cannot be deleted": "Системные роли нельзя удалить",
}

def translate_po_file(file_path, translations):
    """Read .po file and translate empty msgstr entries"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a msgid line
        if line.startswith('msgid "') and not line.startswith('msgid ""'):
            # Extract the English text
            msgid_text = line.split('msgid "')[1].rstrip('"\n')
            
            # Check if next line is empty msgstr
            if i + 1 < len(lines) and lines[i + 1].strip() == 'msgstr ""':
                # Check if we have a translation
                if msgid_text in translations:
                    lines[i + 1] = f'msgstr "{translations[msgid_text]}"\n'
                    modified = True
        
        i += 1
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✓ Translated {file_path}")
        return True
    else:
        print(f"○ No translations applied to {file_path}")
        return False

if __name__ == "__main__":
    import os
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uz_file = os.path.join(base_dir, "locale", "uz", "LC_MESSAGES", "django.po")
    ru_file = os.path.join(base_dir, "locale", "ru", "LC_MESSAGES", "django.po")
    
    print("Starting translation...")
    print("=" * 60)
    
    uz_modified = translate_po_file(uz_file, UZ_TRANSLATIONS)
    ru_modified = translate_po_file(ru_file, RU_TRANSLATIONS)
    
    print("=" * 60)
    if uz_modified or ru_modified:
        print("✓ Translation completed successfully!")
        print("\nNext steps:")
        print("1. Review the translations")
        print("2. Restart Django server")
        print("3. Test the translations in the UI")
    else:
        print("○ No translations were needed")
