# __main__.spec
# PyInstaller spec file for Conlang Assistant
from PyInstaller.utils.hooks import collect_data_files

# Collect all data files from mlconjug3, goddamnthis sucked
mlconjug3_datas = collect_data_files('mlconjug3')

block_cipher = None

a = Analysis(
    ['__main__.py'],
    pathex=[],
    binaries=[],
    datas=mlconjug3_datas,
    hiddenimports=[
        'yaml',
        'mlconjug3',
        'sklearn',
        'sklearn.utils._cython_blas',
        'sklearn.utils._weight_vector',
        'sklearn.neighbors._typedefs',
        'sklearn.neighbors._quad_tree',
        'sklearn.tree._utils',
        'sklearn.linear_model._logistic',
        'sklearn.linear_model._sag_fast',
        'sklearn.linear_model._cd_fast',
        'sklearn.utils._cython_blas',
        'sklearn.utils._weight_vector',
        'sklearn.neighbors._typedefs',
        'sklearn.neighbors._quad_tree',
        'sklearn.tree._utils',
        'scipy.special._cdflib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ConlangAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,   # set to False if you want no console window
)
