from win32com.client import Dispatch
from zipfile import ZipFile, BadZipFile
import requests
import os, time


def getVersion(filename):
    parser = Dispatch("Scripting.FileSystemObject")
    try:
        version = parser.GetFileVersion(filename)
    except Exception:
        return None
    return version


def getChromeDriver():

    # The possible chrome paths
    paths = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]

    version = list(filter(None, [getVersion(p) for p in paths]))[0]

    # Sometimes there isn't a driver for a specific version, so this loop ensures we find at least one
    while True:
        # All chrome driver urls have this form
        url = 'https://chromedriver.storage.googleapis.com/' + version + '/chromedriver_win32.zip'

        # Download the file
        r = requests.get(url, allow_redirects=True)

        # Have to save it because ZipFile doesn't allow directly passing file
        with open('tmp.zip', 'wb') as f:
            f.write(r.content)

        try:
            with ZipFile('tmp.zip', 'r') as zipObj:
                zipObj.extractall(saveDir)

            break

        except BadZipFile:
            os.remove('tmp.zip')

            # Get standard driver for the general version
            genVsn = version[:2]

            if int(genVsn) is 84:
                version = '84.0.4147.30'
            elif int(genVsn) is 83:
                version = '83.0.4103.39'
            elif int(genVsn) is 81:
                version = '81.0.4044.138'
            elif int(genVsn) is 80:
                version = '80.0.3987.106'
            elif int(genVsn) is 79:
                version = '79.0.3945.36'
            elif int(genVsn) is 78:
                version = '78.0.3904.105'
            elif int(genVsn) is 77:
                version = '77.0.3865.40'
            elif int(genVsn) is 76:
                version = '76.0.3809.126'
            elif int(genVsn) is 75:
                version = '75.0.3770.140'
            elif int(genVsn) is 74:
                version = '74.0.3729.6'
            elif int(genVsn) is 73:
                version = '73.0.3683.68'
            else:
                version = '2.46'

    os.remove('tmp.zip')


if __name__ == "__main__":

    saveDir = os.path.join('..', 'drivers', 'windows')
    driverNames = ['chromedriver.exe']

    # First check if the drivers already exist. Delete them if they do
    for driver in driverNames:
        driverPath = os.path.join(saveDir, driver)
        if os.path.exists(driverPath):
            os.remove(driverPath)

    getChromeDriver()
