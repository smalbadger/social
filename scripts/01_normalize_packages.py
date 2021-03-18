import os
import sys
import pygit2
from subprocess import check_output, check_call
from os.path import join, dirname

temp_req_file = join(dirname(__file__), "temp_requirements.txt")
perm_pip_req_file = join(dirname(__file__), '..', "requirements.txt")

# Mapping of dependencies to download and install from Facade Technologies github
# These are generally repositories that needed to be forked and modified to work with Facile.
requirements_from_source = {
    "qtmodern": ("https://github.com/facade-technologies-inc/qtmodern.git", "master"),
}


if __name__ == "__main__":

    # -- Get current list of installed packages. -----------------------------------------------------------------------
    frz = check_output([sys.executable, '-m', 'pip', 'freeze'])
    with open(temp_req_file, 'w') as f:
        f.write(frz.decode('UTF-8'))

    with open(temp_req_file) as f:
        cur_reqs = set(f.readlines())
    os.remove(temp_req_file)

    # -- Get list of necessary requirements ----------------------------------------------------------------------------
    with open(perm_pip_req_file) as f:
        needed_reqs = set(f.readlines())

    # -- Determine which requirements we have, need to get rid of, or need to install. ---------------------------------
    # TODO: Find way to filter unnecessary packages from pip freeze
    unnecessary_packages = [p for p in cur_reqs - needed_reqs if p not in requirements_from_source]
    have_packages = cur_reqs.intersection(needed_reqs)
    needed_packages = list(needed_reqs - cur_reqs)

    # -- Uninstall unnecessary packages --------------------------------------------------------------------------------
    for package in unnecessary_packages:
        if package := package.strip():
            print(f"Uninstalling {package}...", end=' ')
            check_call([sys.executable, '-m', 'pip', 'uninstall', package, '-y'])
            print('Done.')
    print()

    # -- Install necessary packages ------------------------------------------------------------------------------------
    for package in needed_packages:
        if package := package.strip():
            print(f'Installing {package}...', end=' ')
            check_call([sys.executable, '-m', 'pip', 'install', package])
            print('Done.')
    print()

    # -- Clone/Pull any dependencies which are not hosted on PyPi) -----------------------------------------------------
    for package, repo in requirements_from_source.items():
        url, branchName = repo
        repo_path = os.path.normpath(join(dirname(__file__), "../../", package))

        # if the repo already exists, switch to the target branch and pull
        if os.path.exists(repo_path):
            print(f"Pulling: {package} @ branch: {branchName}")
            repoObj = pygit2.Repository(join(repo_path, ".git"))
            branch = repoObj.lookup_branch(branchName)
            ref = repoObj.lookup_reference(branch.name)
            repoObj.checkout(ref)

            freeze_loc = os.getcwd()
            os.chdir(repo_path)
            output = check_output(["git", "pull"])
            os.chdir(freeze_loc)

        else:
            print(f"Cloning: {package} @ branch: {branchName}")
            pygit2.clone_repository(url, repo_path, checkout_branch=branchName)

        print(f"Installing from source: {package}")
        check_call([sys.executable, '-m', 'pip', 'install', '--no-deps', repo_path])
        print('')

    # -- Print a report of what was done -------------------------------------------------------------------------------
    report = {
        "These are extra (we uninstalled them for you)": unnecessary_packages,
        "You have these required packages already (no action)": have_packages,
        "You need these packages (we installed them for you)": needed_packages,
        "We also pulled the following packages from github": requirements_from_source.keys()
    }

    for x, l in report.items():
        l = '\t'.join(l).rstrip() if l else None
        print("\n{x}:\n\t{l}".format(x=x, l=l))

    print()  # extra whitespace to look good
