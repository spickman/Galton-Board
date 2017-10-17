# -*- mode: python -*-

block_cipher = None


a = Analysis(['GaltonBoard.py'],
             pathex=['E:\\GaltonBoard\\GaltonBoard'],
             binaries=[],
             datas=[('preset1config.ini', '.'), ('preset2config.ini', '.'), ('preset3config.ini', '.'), ('Button.py', '.'), ('TextBox.py', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='GaltonBoard',
          debug=True,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='GaltonBoard')
