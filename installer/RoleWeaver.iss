#define MyAppName "Role Weaver"
#define MyAppVersion "1.0.0"
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
Source: "..\dist\RoleWeaver\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Role Weaver"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Role Weaver"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Role Weaver"; Flags: nowait postinstall skipifsilent
