import os
from ftplib import FTP
from subprocess import Popen, PIPE
from semantic_version import Version
from pygit2 import Repository, Signature, GIT_SORT_TIME

import database.general
from database.credentials import file_host, file_port, file_password, file_username
from gui.updateversiondialog import UpdateVersionDialog

versionFile = os.path.abspath('version.txt')
changeLogFile = os.path.abspath('changelog.txt')

def getCurrentVersion():
    """Get the currently running version of Social"""
    with open(versionFile) as vf:
        return Version(vf.read().strip())

def setVersion(v: Version):
    """
    Set the contents of the version file

    .. note::
        ONLY RUN FROM THE RELEASE TOOL!!
    """
    with open(versionFile, 'w') as vf:
        vf.write(str(v))

def getCommitMessagesSince(repoDir, v: Version):
    """
    Get all of the commit messages since a particular release

    .. note::
        ONLY RUN FROM THE RELEASE TOOL!!
    """
    repo = Repository(repoDir)
    start = repo.revparse_single(repo.head.name)
    release_tag = repo.revparse_single(f'refs/tags/v{v}')

    walker = repo.walk(start.id, GIT_SORT_TIME)
    walker.hide(release_tag.id)

    return [commit.message for commit in walker if "Merge" not in commit.message]

def addVersionTagToLastCommit(repoDir, v: Version, message):
    """
    Tag the last commit with a particular version.

    .. note::
        ONLY RUN FROM THE RELEASE TOOL!!
    """
    repo = Repository(repoDir)
    tagger = Signature('Sam Badger', 'smalbadger@email.arizona.edu')
    lastCommit = repo.revparse_single('HEAD')
    repo.create_tag(f"v{v}", lastCommit.id, 1, tagger, message)

def getActiveVersion():
    """Get the active version from the database"""
    return database.general.Session.query(Version).filter(Version.active == True).one_or_none()

def updateAvailable():
    """If an update is available, return True, else False"""
    with open('version.txt') as vf:
        version = vf.read().strip()

    return getActiveVersion().semantic_id != version

def uploadInstaller(v: Version):
    """
    Upload an installer to the server

    .. note::
        ONLY RUN FROM THE RELEASE TOOL!!
    """
    ftp = FTP()
    ftp.connect(host=file_host, port=file_port)
    ftp.login(user=file_username, passwd=file_password)

    localFile = f'../dist/social_installer_v{str(v)}.exe'
    remoteFile = f'installers/social_v{str(v)}.exe'
    with open(localFile, 'rb') as f:
        ftp.storbinary(f'STOR {remoteFile}', f)
    ftp.quit()


updateLock = False
def update():
    """Update to the active version of Social. Return True if update occurred and False otherwise."""
    global updateLock

    if updateLock:
        return False

    updateLock = True

    if not updateAvailable():
        updateLock = False
        return False

    activeVersion = getActiveVersion()

    ftp = FTP()
    ftp.connect(host=file_host, port=file_port)
    ftp.login(user=file_username, passwd=file_password)

    # download new installer from server
    def write_and_alert(contents):
        installerFile = f'social_installer_v{activeVersion.semantic_id}.exe'
        with open(installerFile, 'wb') as fp:
            fp.write(contents)

        UpdateVersionDialog(activeVersion).exec_()
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        Popen([installerFile], stdin=PIPE, stdout=PIPE, stderr=PIPE, creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        exit(100)

    ftp.retrbinary(f'RETR installers/social_installer_v{activeVersion.semantic_id}.exe', callback=write_and_alert)