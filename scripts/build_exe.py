import os
import subprocess
import shutil
from semantic_version import Version

version = Version("1.2.3")

version_file = """
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=({major}, {minor}, {patch}, 0),
    prodvers=({major}, {minor}, {patch}, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Philippe Cutillas & Sam Badger'),
        StringStruct(u'FileDescription', u'Social'),
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'Social'),
        StringStruct(u'LegalCopyright', u'Copyright Philippe Cutillas & Sam Badger, 2020. All rights reserved.'),
        StringStruct(u'OriginalFilename', u'SOCIAL.EXE'),
        StringStruct(u'ProductName', u'Social Network Automation Tool'),
        StringStruct(u'ProductVersion', u'{major}.{minor}.{patch}.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""


if __name__ == "__main__":

    with open('../src/version.txt') as vf:
        v = Version(vf.read().strip())

    with open('../src/file_version_info.txt', 'w') as fvi:
        fvi.write(version_file.format(major=v.major, minor=v.minor, patch=v.patch, version=str(v)).encode('utf-8').decode('utf-8'))

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

    exit_code = subprocess.call([
        'pyinstaller',
        '--onedir',
        '--noconsole',
        '--hidden-import', 'pymysql',
        '--hidden-import', 'sqlalchemy.sql.default_comparator',
        '--hidden-import', 'sqlalchemy.ext.baked',
        '--add-data', 'drivers;drivers',
        '--add-data', 'src/version.txt;.',
        '--icon', 'resources/social-network.ico',
        '--version-file', os.path.abspath(os.path.join('src', 'file_version_info.txt')),
        'src/social.py'
    ])

    if exit_code:
        print("Did not build correctly")
        exit(exit_code)

    os.remove('src/file_version_info.txt')

    shutil.rmtree("build", ignore_errors=True)
    shutil.move("dist", "build")