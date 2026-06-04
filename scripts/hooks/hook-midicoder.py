# PyInstaller hook for Midicoder CE
# Ensures all Midicoder modules and data files are included in the bundle.

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect ALL midicoder submodules (covers midicoder.api.*, midicoder.pipeline.*, etc.)
hiddenimports = collect_submodules('midicoder')

# Collect all data files (frontend/, packs/, prompts/, .yml, .jinja2)
datas = collect_data_files('midicoder', include_py_files=True)
