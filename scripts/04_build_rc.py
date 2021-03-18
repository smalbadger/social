import os
import subprocess
import sys

qrc = os.path.abspath("../icons.qrc")
out = os.path.abspath("../src/gui/rc/icons_rc.py")

if __name__ == "__main__":
    print("Compiling Resource Files... ")

    d = os.path.dirname(out)
    if not os.path.exists(d):
        os.makedirs(d)

    python = sys.executable
    rcc = os.path.join(os.path.dirname(python), 'pyside2-rcc.exe')

    with open(out, 'w') as fout:
        proc = subprocess.Popen([rcc, qrc], stdout=fout)
        return_code = proc.wait()

    print("Reworking Resource Files...")
    # read in all lines from the rc file
    with open(out, 'r') as f:
        lines = f.readlines()

    # write out only the non-empty lines back to the rc file
    with open(out, 'w') as f:
        for line in lines:
            if line.strip():
                f.write(line)

    print("Done")