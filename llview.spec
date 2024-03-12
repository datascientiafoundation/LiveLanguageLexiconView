# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['livelanguagelexiconview/src/llview.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
a.datas+=[
    ('que.xml',
    'livelanguagelexiconview/src/que.xml', 
    'DATA'),
    ('mon.xml',
    'livelanguagelexiconview/src/mon.xml', 
    'DATA'),
    ]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='llview',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
