[app]
title = BirKarta
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
permissions = NFC,READ_EXTERNAL_STORAGE
accept_sdk_license = True

[android.gradle_dependencies]

[android.manifest]
