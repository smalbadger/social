import sys
import os
import setuptools
from cx_Freeze import setup, Executable

sys.path.append(os.path.abspath("./src/"))
sys.path.append(os.path.abspath("./src/gui/rc/"))

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = {
    "packages": [
        # Facile sub-packages
        "src.common",
        "src.database",
        "src.emails",
        "src.gui",
        "src.site_controllers"
    ],

    "includes": [
        "pymysql",
        "PySide2.QtWidgets"
    ],

    "include_files": [
    ],

    "excludes": [
        "scipy.spatial.cKDTree",
        "matplotlib.tests",
        "numpy.random._examples",
        "mpl_toolkits",
    ]
}

base = None

# Uncomment for GUI applications to NOT show cmd window while running.
# if sys.platform =='win32':
#     base = 'Win32GUI'

executables = [
    Executable(script = 'src/social.py', base=base, targetName = 'social.exe', icon = 'resources/social-network.ico')
]

setup(name='Social',
      version = '1.0',
      description = 'A tool for automating social media activity.',
      options = {
          "build_exe": buildOptions,
      },
      executables = executables)