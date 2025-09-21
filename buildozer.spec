[app]
title = BirKarta
package.name = birkarta
package.domain = kz.bolashak

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.1.0,pyjnius

[buildozer]
log_level = 2

[android]
api = 31
minapi = 21
ndk = 23b
accept_sdk_license = True
permissions = NFC,READ_EXTERNAL_STORAGE

[android.gradle_dependencies]

[android.manifest]
