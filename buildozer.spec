[app]
title = BirKarta
package.name = birkarta
package.domain = kz.bolashak
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,json
requirements = python3,kivy,pyjnius

android.permissions = NFC
android.features = android.hardware.nfc
android.api = 33
android.minapi = 24
android.enable_androidx = True
