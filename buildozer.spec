[app]
title = БірКарта
package.name = birkarta
package.domain = kz.bolashak

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0
requirements = python3,kivy,pyjnius

[buildozer]
log_level = 2

[android]
api = 33
minapi = 24
ndk = 23b
sdk = 33

# NFC разрешения
permissions = NFC,READ_EXTERNAL_STORAGE,INTERNET

# Настройки для NFC
android.add_src = 

# Интент фильтры для NFC
android.add_xml = res/xml/nfc_tech_filter.xml

# Активности в манифесте
android.add_activities = 

# Манифест настройки
android.manifest.intent_filters = res/raw/intent_filters.xml

# Иконка (опционально)
# icon.filename = icon.png

[android.manifest]
# Добавляем NFC фичи в манифест
android.uses_feature = android.hardware.nfc

[android.gradle_dependencies]
# Если нужны дополнительные зависимости