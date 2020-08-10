import os
import subprocess
import shutil


if __name__ == "__main__":
    os.chdir("..")

    target = "social.spec"
    if os.path.exists(target):
        os.remove(target)

    target = "build"
    if os.path.exists(target):
        shutil.rmtree(target, ignore_errors=True)

    target = "dist"
    if os.path.exists(target):
        shutil.rmtree(target, ignore_errors=True)

    subprocess.call([
        'pyinstaller',
        '--onedir',
        '--noconsole',
        '--hidden-import', 'pymysql',
        '--hidden-import', 'sqlalchemy.sql.default_comparator',
        '--hidden-import', 'sqlalchemy.ext.baked',
        '--add-data', 'drivers;drivers',
        '--icon', 'resources/social-network.ico',
        'src/social.py'
    ])

    shutil.rmtree("build", ignore_errors=True)
    shutil.move("dist", "build")