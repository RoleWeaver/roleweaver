#define MyAppName "Role Weaver"
#ifndef MyAppVersion
#define MyAppVersion "1.3.2"
#endif
#define MyAppPublisher "RoleWeaver"
#define MyAppURL "https://github.com/RoleWeaver/roleweaver"
#define MyAppExeName "RoleWeaver.exe"

[Setup]
AppId={{D80C3B71-07A8-47D7-9F5B-7CE0A27EAB92}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Programs\Role Weaver
DefaultGroupName=Role Weaver
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\release
OutputBaseFilename=RoleWeaver-Setup-v{#MyAppVersion}
SetupIconFile=..\assets\RoleWeaver.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\RoleWeaver\*"; DestDir: "{app}"; Excludes: "Characters\*,Campaigns\*,Lore\*,RoleplayRules\*"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\RoleWeaver\Characters\*"; DestDir: "{app}\Characters"; Flags: onlyifdoesntexist uninsneveruninstall recursesubdirs createallsubdirs
Source: "..\dist\RoleWeaver\Campaigns\*"; DestDir: "{app}\Campaigns"; Flags: onlyifdoesntexist uninsneveruninstall recursesubdirs createallsubdirs
Source: "..\dist\RoleWeaver\Lore\*"; DestDir: "{app}\Lore"; Flags: onlyifdoesntexist uninsneveruninstall recursesubdirs createallsubdirs
Source: "..\dist\RoleWeaver\RoleplayRules\*"; DestDir: "{app}\RoleplayRules"; Flags: onlyifdoesntexist uninsneveruninstall recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Role Weaver"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Role Weaver"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Role Weaver"; Flags: nowait postinstall skipifsilent
