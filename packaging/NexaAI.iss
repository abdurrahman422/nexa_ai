#define MyAppName "Nexa AI"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "Nexa AI"

[Setup]
AppId={{9D32D0D1-4A2E-47D7-934C-70C8B4B1EE60}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\NexaAI
DefaultGroupName=Nexa AI
OutputDir=..\release\installer
OutputBaseFilename=NexaAI-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible

[Files]
Source: "..\release\NexaAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Nexa AI"; Filename: "{app}\NexaAI.exe"
Name: "{autodesktop}\Nexa AI"; Filename: "{app}\NexaAI.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\NexaAI.exe"; Description: "Launch Nexa AI"; Flags: postinstall nowait skipifsilent
