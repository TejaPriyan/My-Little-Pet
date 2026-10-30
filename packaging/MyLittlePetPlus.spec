# Free Plus release. Game and artwork only.
from pathlib import Path
ROOT = Path(SPECPATH).resolve().parent
a = Analysis([str(ROOT/'teja-pet'/'plus_main.py')], pathex=[str(ROOT/'teja-pet')], binaries=[],
    datas=[(str(ROOT/'teja-pet'/'assets'),'assets')], hiddenimports=[], hookspath=[], hooksconfig={},
    runtime_hooks=[], excludes=['numpy','matplotlib','pandas','scipy','tkinter'], noarchive=False, optimize=0)
pyz = PYZ(a.pure)
exe = EXE(pyz,a.scripts,a.binaries,a.datas,[],name='MyLittlePetPlus',debug=False,
    bootloader_ignore_signals=False,strip=False,upx=False,console=False,disable_windowed_traceback=False,
    icon=[str(ROOT/'packaging'/'pet.ico')],manifest=str(ROOT/'packaging'/'windows.manifest'),
    version=str(ROOT/'packaging'/'windows-version.txt'))
