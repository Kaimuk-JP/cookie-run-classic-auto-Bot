; Script generated for Inno Setup 6
; CookieRun Classic Bot Pro - Windows Installer Script

#ifndef MyAppVersion
#define MyAppVersion "2.0.0"
#endif
#define MyAppName "CookieRun Classic Bot Pro"
#define MyAppPublisher "CookieRun Bot Team"
#define MyAppExeName "CookieRunBot.exe"

[Setup]
AppId={{D4167B2A-941E-479A-A3E5-88B1CA9F6751}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\CookieRunBot
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist_installer
OutputBaseFilename=CookieRunBot_Setup_v{#MyAppVersion}
SetupIconFile=src\bot_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog commandline
CloseApplications=yes
RestartApplications=yes

[InstallDelete]
Type: files; Name: "{app}\python3*.dll"
Type: files; Name: "{app}\*.pyd"
Type: files; Name: "{app}\libcrypto-*.dll"
Type: files; Name: "{app}\libssl-*.dll"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\CookieRun_Bot\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.log,*.tmp,screenshots\*,src\screenshots\*,logs\*,src\logs\*,settings\*.json,history\*.json,logs_error\*"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall
