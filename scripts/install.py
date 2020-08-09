import os
import subprocess


if __name__ == "__main__":
    os.chdir("..")
    subprocess.call([
        #'python', '-m',
        'pyinstaller',
        '--onedir',
        '--hidden-import', 'pymysql',
        '--hidden-import', 'sqlalchemy.sql.default_comparator',
        '--hidden-import', 'sqlalchemy.ext.baked',
        '--add-data', 'drivers;drivers',
        '--icon', 'resources/social-network.ico',
        'src/social.py'
    ])

