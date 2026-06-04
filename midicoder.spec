# -*- mode: python ; coding: utf-8 -*-
r"""
PyInstaller spec file for Midicoder CE standalone binary.

Runtime bundled:
  - Python 3.12.x (exact version from .venv)
  - FastAPI + uvicorn + all Python dependencies
  - tree_sitter + tree_sitter_languages (native .pyd/.so included)
  - midicoder/ package (pipeline, api, packs, storage)
  - Angular SPA dist (midicoder/frontend/)
  - Datasette (SQLite web viewer, port 8080)
  - SQLite (built-in Python stdlib)

NOT bundled:
  - Node.js (only needed at build time for Angular compilation)

Build:
    .venv\Scripts\pyinstaller midicoder.spec   (Windows)
    .venv/bin/pyinstaller midicoder.spec        (Linux/macOS)

Output:
    dist/midicoder (single file, ~150-250MB)
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

block_cipher = None

# PyInstaller 6.x collect_all() returns tuple (datas, binaries, hiddenimports)
#   - datas: list of (abspath, destpath) tuples — for Analysis.datas
#   - binaries: list of (abspath, destpath) tuples — for Analysis.binaries
#   - hiddenimports: list of module name strings — for Analysis.hiddenimports

fastapi_datas, fastapi_bins, fastapi_imports = collect_all('fastapi')
uvicorn_datas, uvicorn_bins, uvicorn_imports = collect_all('uvicorn')
pydantic_datas, pydantic_bins, pydantic_imports = collect_all('pydantic')
datasette_datas, datasette_bins, datasette_imports = collect_all('datasette')
ps_datas, ps_bins, ps_imports = collect_all('pydantic_settings')
starlette_datas, starlette_bins, starlette_imports = collect_all('starlette')
anyio_datas, anyio_bins, anyio_imports = collect_all('anyio')
h11_datas, h11_bins, h11_imports = collect_all('h11')
sniffio_datas, sniffio_bins, sniffio_imports = collect_all('sniffio')
# typing_extensions: single-module (not a package) — collect_all() warns.
# PyInstaller resolves it automatically; no extra collection needed.
te_datas, te_bins, te_imports = [], [], []
click_datas, click_bins, click_imports = collect_all('click')
pystray_datas, pystray_bins, pystray_imports = collect_all('pystray')

# Pillow: native .pyd/.so collected by the built-in PIL hook.
# It's a single-module (not a package) so collect_data_files() also warns.
# Let PyInstaller's hook handle everything.
pillow_datas, pillow_bins, pillow_imports = [], [], []

# Merge all from dependencies
dep_datas = (fastapi_datas + uvicorn_datas + pydantic_datas + datasette_datas +
             ps_datas + starlette_datas + anyio_datas + h11_datas + sniffio_datas + te_datas + click_datas +
             pystray_datas + pillow_datas)
dep_bins = (fastapi_bins + uvicorn_bins + pydantic_bins + datasette_bins +
            ps_bins + starlette_bins + anyio_bins + h11_bins + sniffio_bins + te_bins + click_bins +
            pystray_bins + pillow_bins)
dep_imports = (fastapi_imports + uvicorn_imports + pydantic_imports + datasette_imports +
               ps_imports + starlette_imports + anyio_imports + h11_imports + sniffio_imports + te_imports + click_imports +
               pystray_imports + pillow_imports)

# Collect all midicoder submodules
midicoder_modules = collect_submodules('midicoder')

all_hidden = [
    'midicoder',
    'midicoder.__main__',
    'midicoder.launcher',
    'midicoder.spa_serve',
    'midicoder.api',
    'midicoder.api.main',
    'midicoder.api.config',
    'midicoder.api.i18n',
    'midicoder.api.models',
    'midicoder.api.pipeline_bridge',
    'midicoder.api.artifact',
    'midicoder.api.routers',
    'midicoder.api.routers.health',
    'midicoder.api.routers.init',
    'midicoder.api.routers.projects',
    'midicoder.api.routers.config',
    'midicoder.api.routers.index',
    'midicoder.api.routers.version',
    'midicoder.api.routers.brief',
    'midicoder.api.routers.contract',
    'midicoder.api.routers.ir',
    'midicoder.api.routers.code',
    'midicoder.api.routers.runtime',
    'midicoder.api.routers.websocket',
    'midicoder.api.routers.pipeline',
    'midicoder.api.routers.patches',
    'midicoder.pipeline',
    'midicoder.pipeline.commands',
    'midicoder.pipeline.commands.init',
    'midicoder.pipeline.commands.brief',
    'midicoder.pipeline.commands.contract',
    'midicoder.pipeline.commands.ir',
    'midicoder.pipeline.commands.code',
    'midicoder.pipeline.commands.version',
    'midicoder.pipeline.commands.index',
    'midicoder.pipeline.commands.preview',
    'midicoder.pipeline.commands.util',
    'midicoder.storage',
    'midicoder.storage.projects',
    'midicoder.storage.sqlite',
    'midicoder.errors',
    # Tree-sitter (native extensions — .pyd/.so files)
    'tree_sitter',
    'tree_sitter_languages',
    # YAML
    'ruamel.yaml',
    'ruamel.yaml.constructor',
    'ruamel.yaml.emitter',
    # Others
    'openai',
    'tiktoken',
    'code_review_graph',
    'yaml',
    'pysqlite3',
    'sqlite3',
    'ssl',
    '_sqlite3',
] + midicoder_modules + dep_imports

# Data files: entire midicoder package (includes frontend/, packs/, prompts/)
# Plus data files from collect_all for critical dependencies.
datas = collect_data_files('midicoder', include_py_files=True)
datas.extend(dep_datas)

# Bundle logo.png for tray icon + desktop shortcut
_spec_dir = os.getcwd()
_logo_src = os.path.join(_spec_dir, 'webgui', 'public', 'logo.png')
if os.path.isfile(_logo_src):
    datas.append((_logo_src, 'midicoder/logo.png'))

# Bundle Angular SPA dist as midicoder/frontend/
_frontend_src = os.path.join(_spec_dir, 'webgui', 'dist', 'webgui', 'browser')
if os.path.isdir(_frontend_src):
    datas.append((_frontend_src, 'midicoder/frontend'))
del _logo_src, _frontend_src, _spec_dir

# Additional Datasette data files (static CSS/JS + Jinja2 templates)
# Manual fallback in case collect_all missed them.
_ds_path = None
try:
    import importlib, os
    _ds = importlib.import_module('datasette')
    _ds_root = _ds.__path__[0] if hasattr(_ds, '__path__') else os.path.dirname(_ds.__file__)
    _ds_path = _ds_root
except Exception:
    pass

if _ds_path and os.path.isdir(_ds_path):
    for _subdir in ('static', 'templates'):
        _src_dir = os.path.join(_ds_path, _subdir)
        if os.path.isdir(_src_dir):
            datas.append((_src_dir, 'datasette/' + _subdir))
del _ds_path

# Binaries from collect_all (native extensions, shared libraries)
extra_bins = dep_bins

a = Analysis(
    ['midicoder/__main__.py'],
    pathex=[],
    binaries=extra_bins,
    datas=datas,
    noarchive=False,
    hiddenimports=all_hidden,
    hookspath=['scripts/hooks'],
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'pytest',
        'setuptools',
        'wheel',
        'pip',
        'docutils',
        # SQLAlchemy optional DB drivers — not installed, cause "not found" warnings
        'pysqlite2',
        'MySQLdb',
        'psycopg2',
    ],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Convert logo.png → logo.ico at build time for EXE icon
_logo_path = None
try:
    import os as _os
    from PIL import Image as _PILImage
    _spec_dir = _os.getcwd()
    _logo_src = _os.path.join(_spec_dir, 'webgui', 'public', 'logo.png')
    if _os.path.isfile(_logo_src):
        _img = _PILImage.open(_logo_src).convert('RGBA')
        _ico_path = _os.path.join(_spec_dir, 'build', 'midicoder-icon.ico')
        _os.makedirs(_os.path.dirname(_ico_path), exist_ok=True)
        _img.save(_ico_path, format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
        _logo_path = _ico_path
        print(f"Generated icon: {_ico_path}")
except Exception as _e:
    print(f"Icon generation failed: {_e}")

# UPX exclude: native extensions must NOT be compressed or they crash at import time
upx_exclude = ['*.pyd', '*.so', '*.dll']

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='midicoder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=upx_exclude,
    console=False,  # PyInstaller 6.x: console=False = no console window (windowed mode)
    icon=_logo_path if _logo_path else None,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    [],
    name='midicoder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=upx_exclude,
    runtime_tmpdir=None,
    no_archive=False,
)
