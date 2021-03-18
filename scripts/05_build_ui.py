# No need to update this script unless there is a bug.
import os
import subprocess
import sys

ui_folder = os.path.abspath("../src/gui/ui/")

if __name__ == "__main__":
    python = sys.executable
    uic = os.path.join(os.path.dirname(python), 'pyside2-uic.exe')

    print("Removing existing compiled UI files...")
    for file in os.listdir(ui_folder):
        if file.startswith("ui_") and file.endswith(".py"):
            print("\t" + file)
            os.remove(os.path.join(ui_folder, file))

    print("Compiling UI files... ")
    for file in os.listdir(ui_folder):
        if file.endswith(".ui"):
            srcFile = os.path.join(ui_folder, file)
            dstFile = os.path.join(ui_folder, "ui_{}.py".format(file[:-3]))
            print("\t" + file)

            with open(dstFile, 'w') as fout:
                if python:
                    args = [python, uic, srcFile]
                else:
                    args = [uic, srcFile]
                proc = subprocess.Popen(args, stdout=fout)
                return_code = proc.wait()

            with open(dstFile, 'r') as fin:
                contents = fin.read()

            with open(dstFile, 'w') as fout:
                fout.write(contents.replace("import icons_rc", "import gui.rc.icons_rc as icons_rc"))

    print("Done")