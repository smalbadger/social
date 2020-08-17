import os
from ftplib import FTP
from subprocess import Popen, PIPE
from semantic_version import Version
from pygit2 import Repository, Signature, GIT_SORT_TIME

import database.general
from database.credentials import file_host, file_port, file_password, file_username
from gui.updateversiondialog import UpdateVersionDialog

updateInProgress = False

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
    return database.general.Session.query(database.general.Version).filter(database.general.Version.active == True).one_or_none()

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
def downloadInstaller():
    """Download"""

    if not updateAvailable():
        return False

    global uploadInProgress
    updateInProgress = True

    activeVersion = getActiveVersion()

    ftp = FTP()
    ftp.connect(host=file_host, port=file_port)
    ftp.login(user=file_username, passwd=file_password)

    # download new installer from server
    installerFile = f'social_v{activeVersion.semantic_id}.exe'
    with open(installerFile, 'wb') as fp:
        ftp.retrbinary(f'RETR installers/social_v{activeVersion.semantic_id}.exe', callback=fp.write)

def triggerUpdate():
    """Display the update dialog """
    activeVersion = getActiveVersion()
    installerFile = f'social_v{activeVersion.semantic_id}.exe'
    UpdateVersionDialog(activeVersion).exec_()

    CREATE_NEW_PROCESS_GROUP = 0x00000200
    DETACHED_PROCESS = 0x00000008
    Popen([installerFile], stdin=PIPE, stdout=PIPE, stderr=PIPE, creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)

    exit(100)

