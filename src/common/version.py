import os
from semantic_version import Version

from pygit2 import Repository, Signature, GIT_SORT_TIME, Commit

versionFile = os.path.abspath('version.txt')
changeLogFile = os.path.abspath('changelog.txt')

def getCurrentVersion():
    with open(versionFile) as vf:
        return Version(vf.read().strip())

def setVersion(v: Version):
    with open(versionFile, 'w') as vf:
        vf.write(str(v))

def getChangeLog():
    with open(changeLogFile) as clf:
        return clf.read()

def setChangeLog(log):
    with open(changeLogFile, 'w') as clf:
        clf.write(log)

def getCommitMessagesSince(repoDir, v: Version):
    repo = Repository(repoDir)
    start = repo.revparse_single(repo.head.name)
    release_tag = repo.revparse_single(f'refs/tags/v{v}')

    walker = repo.walk(start.id, GIT_SORT_TIME)
    walker.hide(release_tag.id)

    return [commit.message for commit in walker if "Merge" not in commit.message]

def addVersionTagToLastCommit(repoDir, v: Version, message):
    repo = Repository(repoDir)
    tagger = Signature('Sam Badger', 'smalbadger@email.arizona.edu')
    lastCommit = repo.revparse_single('HEAD')
    repo.create_tag(f"v{v}", lastCommit.id, 1, tagger, message)
