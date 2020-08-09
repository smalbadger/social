import sys
import os
import setuptools
from cx_Freeze import setup, Executable

sys.path.append(os.path.abspath("./src/"))
sys.path.append(os.path.abspath("./src/gui/rc/"))
sys.path.append(os.path.abspath("C:/Users/smalb/anaconda3/Lib/site-packages"))

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
        "PySide2.QtWidgets",
        "matplotlib.animation",
    ] + [f"matplotlib.{os.path.splitext(module)[0]}" for module in os.listdir("C:/Users/smalb/anaconda3/Lib/site-packages/matplotlib") if module.endswith(".py") and "__init__" not in module],

    "include_files": [
        "drivers/",
        "C:/Users/smalb/anaconda3/Library/plugins",
        "C:/Users/smalb/anaconda3/Lib/site-packages/mpl_toolkits",
    ] + [os.path.join(r"C:\Users\smalb\anaconda3\Library\bin", file) for file in os.listdir(r"C:\Users\smalb\anaconda3\Library\bin") if file.endswith(".dll")]
    + [os.path.join(r"C:\Users\smalb\anaconda3\envs\social\Library\bin", file) for file in os.listdir(r"C:\Users\smalb\anaconda3\envs\social\Library\bin") if file.endswith(".dll")],

    "excludes": [
        "scipy.spatial.cKDTree",
        "matplotlib.tests",
        "numpy.random._examples",
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

# TODO:
#  1. Include the mkl_intel_threads.dll file
#  2. Add __init__.py file to mpl_toolkits if it doesn't exist