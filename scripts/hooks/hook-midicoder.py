# PyInstaller hook for Midicoder
# This file ensures all Midicoder modules are included in the bundled executable

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all submodules
hiddenimports = collect_submodules('midicoder')

# Additional explicit imports that might be missed
hiddenimports += [
    'midicoder',
    'midicoder.cli',
    'midicoder.__main__',
    'midicoder.commands',
    'midicoder.commands.init',
    'midicoder.commands.brief',
    'midicoder.commands.contract',
    'midicoder.commands.ir',
    'midicoder.commands.code',
    'midicoder.commands.version',
    'midicoder.commands.config',
    'midicoder.commands.index',
    'midicoder.commands.runtime',
    'midicoder.config',
    'midicoder.context',
    'midicoder.contract',
    'midicoder.dsl',
    'midicoder.io',
    'midicoder.ir',
    'midicoder.llm',
    'midicoder.brief',
    'midicoder.runtime',
]

# Collect data files if any
datas = collect_data_files('midicoder')