#ifndef PlusExecutable
  #define PlusExecutable "..\release-free\MyLittlePetPlus.exe"
#endif
[Setup]
AppId={{B7867B98-7A40-4B56-9E35-6E0107495FA0}
AppName=My Little Pet Plus
AppVersion=1.6.0
AppPublisher=Teja Priyan
DefaultDirName={localappdata}\Programs\My Little Pet Plus
DefaultGroupName=My Little Pet Plus
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\my-little-pet-site\dist\downloads
OutputBaseFilename=MyLittlePet-Plus-1.6.0-Windows-Setup
SetupIconFile=pet.ico
UninstallDisplayIcon={app}\MyLittlePetPlus.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=yes

[Tasks]
Name: desktopicon; Description: "Create a Plus shortcut"; Flags: unchecked

[Files]
Source: "{#PlusExecutable}"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD-PARTY-NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "PLUS-README.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\My Little Pet Plus"; Filename: "{app}\MyLittlePetPlus.exe"
Name: "{group}\My Little Pet Plus - Desktop"; Filename: "{app}\MyLittlePetPlus.exe"; Parameters: "--desktop"
Name: "{autodesktop}\My Little Pet Plus"; Filename: "{app}\MyLittlePetPlus.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MyLittlePetPlus.exe"; Description: "Meet your Plus pet"; Flags: nowait postinstall skipifsilent
