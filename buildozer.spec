[app]
title = BirKarta
package.name = birkarta
package.domain = kz.bolashak
source.dir = .
version = 1.0
requirements = python3,kivy==2.0.0,pyjnius

[buildozer]
log_level = 2

[android]
api = 30
minapi = 21
accept_sdk_license = True
permissions = NFC
