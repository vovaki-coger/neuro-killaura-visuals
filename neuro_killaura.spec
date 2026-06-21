# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec для Neuro KillAura Launcher

import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('configs', 'configs'),
        ('models', 'models'),
        ('launcher', 'launcher'),
        ('neuro_killaura', 'neuro_killaura'),
        ('visuals', 'visuals'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'torch',
        'torch.nn',
        'numpy',
        'pygame',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'psutil',
        'requests',
        'ctypes',
        'ctypes.windll',
        'tkinter',
        'tkinter.colorchooser',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas', 'IPython', 'jupyter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NeuroKillAura',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NeuroKillAura',
)
