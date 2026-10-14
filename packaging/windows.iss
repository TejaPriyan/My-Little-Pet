[Setup]
AppId={{5F16A718-E375-4A11-8CD4-C521800D39D9}
AppName=My Little Pet
AppVersion=1.1.0
AppPublisher=My Little Pet
DefaultDirName={localappdata}\Programs\My Little Pet
DefaultGroupName=My Little Pet
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\my-little-pet-site\dist\downloads
OutputBaseFilename=MyLittlePet-1.1.0-Windows-Setup
SetupIconFile=pet.ico
UninstallDisplayIcon={app}\MyLittlePet.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=yes

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\release\MyLittlePet.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD-PARTY-NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\My Little Pet"; Filename: "{app}\MyLittlePet.exe"
Name: "{group}\My Little Pet - Desktop Mode"; Filename: "{app}\MyLittlePet.exe"; Parameters: "--desktop"
Name: "{autodesktop}\My Little Pet"; Filename: "{app}\MyLittlePet.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MyLittlePet.exe"; Description: "Meet your little pet"; Flags: nowait postinstall skipifsilent
