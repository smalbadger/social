import subprocess
import os
import sys

INNO_DIR = "C:\Program Files (x86)\Inno Setup 6"
INNO_COMPILER = os.path.join(INNO_DIR, 'Compil32.exe')
INNO_SCRIPT_FILE = os.path.realpath(os.path.join(os.path.dirname(__file__), 'Social_Installer_Setup_Script.iss'))

INNO_SCRIPT_TEMPLATE = r"""
; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "Social"
#define MyAppVersion "{VERSION}"
#define MyAppPublisher "Philippe Cutillas & Sam Badger"
#define MyAppURL ""
#define MyAppExeName "social.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{78FDF148-3564-4C07-9DAA-87F3A488C38C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#SourcePath}\..\dist
OutputBaseFilename=social_installer_v{VERSION}
SetupIconFile={#SourcePath}\..\resources\social-network.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=lowest
; PrivilegesRequired=admin
; PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
;Name: "armenian"; MessagesFile: "compiler:Languages\Armenian.isl"
;Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
;Name: "catalan"; MessagesFile: "compiler:Languages\Catalan.isl"
;Name: "corsican"; MessagesFile: "compiler:Languages\Corsican.isl"
;Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"
;Name: "danish"; MessagesFile: "compiler:Languages\Danish.isl"
;Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
;Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
;Name: "french"; MessagesFile: "compiler:Languages\French.isl"
;Name: "german"; MessagesFile: "compiler:Languages\German.isl"
;Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
;Name: "icelandic"; MessagesFile: "compiler:Languages\Icelandic.isl"
;Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
;Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
;Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"
;Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
;Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
;Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
;Name: "slovak"; MessagesFile: "compiler:Languages\Slovak.isl"
;Name: "slovenian"; MessagesFile: "compiler:Languages\Slovenian.isl"
;Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
;Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
;Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourcePath}\..\build\social\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
"""
import sys, getopt

if __name__ == "__main__":

    with open('../src/version.txt') as f:
        version = f.read().strip()

    if not os.path.exists(INNO_DIR):
        print(f"INNO Setup is not installed in the correct location. Please install it at {INNO_DIR}")
        sys.exit(1)

    if os.path.exists("../venv/"):
        if "venv" not in sys.executable:
            print("=================================== ERROR ===================================")
            print("It appears you have a virtual environment set up, but have not activated it.")
            print("    Please activate your virtual environment before running this script.")
            print("=============================================================================")
            sys.exit(1)

    exit_code = subprocess.check_call("python build_exe.py", shell=True)

    if exit_code != 0:
        print("Executable not properly built. Cannot create an installer.")
        sys.exit(1)

    os.chdir("../")

    with open(INNO_SCRIPT_FILE, 'w') as isf:
        isf.write(INNO_SCRIPT_TEMPLATE.replace('{VERSION}', version))

    print("building installer...", end="", flush=True)
    exit_code = subprocess.call([INNO_COMPILER, '/cc', INNO_SCRIPT_FILE])

    if exit_code == 0:
        print("done.", flush=True)
    elif exit_code == 1:
        print("The installer command was invalid.")
    elif exit_code == 2:
        print("The installer failed to build properly.")
    else:
        print("Unknown exit code.")

    os.chdir('scripts')
    os.remove(INNO_SCRIPT_FILE)

    sys.exit(exit_code)