
import pkg_resources
from subprocess import check_call
import sys

if __name__ == '__main__':
    packages = [dist.project_name for dist in pkg_resources.working_set]
    check_call([sys.executable, '-m', 'pip', 'install', '-U'] + packages, shell=True)
