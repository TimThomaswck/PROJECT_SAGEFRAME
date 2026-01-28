; SageFrame Windows Installer Script
; Inno Setup v6.2+
; 
; Implements Story 6.1 AC1, AC2, AC4: Windows installer with OS integration
;
; Build command:
;   iscc installer.iss
;
; Output:
;   dist/SageFrame-Setup.exe - Windows installer

[Setup]
; Application information
AppName=SageFrame
AppVersion=1.0.0
AppPublisher=SageFrame Project
AppPublisherURL=https://github.com/sageframe/sageframe
AppSupportURL=https://github.com/sageframe/sageframe/issues
AppUpdatesURL=https://github.com/sageframe/sageframe/releases
AppCopyright=Copyright 2026 SageFrame Contributors

; Installation directories
DefaultDirName={autopf}\SageFrame
DefaultGroupName=SageFrame

; Installer output
OutputDir=dist
OutputBaseFilename=SageFrame-Setup
Compression=lzma
SolidCompression=yes

; Installer UI
SetupIconFile=app\resources\icon.ico
SetupLogging=yes
ShowLanguageDialog=no
VersionInfoVersion=1.0.0.0
VersionInfoCompany=SageFrame
VersionInfoProductName=SageFrame
VersionInfoProductVersion=1.0.0

; Windows integration (AC2)
UninstallDisplayIcon={app}\SageFrame.exe
CreateUninstallRegEntry=yes
RegisterUninstallKey=yes

; Requires Windows 7 SP1 or later
MinVersion=6.1sp1

; Allow installation to Program Files without elevation prompts
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Files]
; Main executable
Source: "dist\SageFrame.exe"; DestDir: "{app}"; Flags: ignoreversion

; Resources
Source: "app\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts (AC2)
Name: "{group}\SageFrame"; Filename: "{app}\SageFrame.exe"; WorkingDir: "{app}"; Comment: "Personal productivity and organization application"; IconIndex: 0

; Desktop shortcut
Name: "{commondesktop}\SageFrame"; Filename: "{app}\SageFrame.exe"; WorkingDir: "{app}"; Comment: "Personal productivity and organization application"

; Uninstall shortcut
Name: "{group}\Uninstall SageFrame"; Filename: "{uninstallexe}"; WorkingDir: "{app}"

[Run]
; Launch application after installation (AC2)
Filename: "{app}\SageFrame.exe"; Description: "Launch SageFrame"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up application data on uninstall (optional, keeps user data)
Type: filesandordirs; Name: "{localappdata}\SageFrame\cache"
Type: files; Name: "{app}\*.exe"
Type: files; Name: "{app}\*.dll"
Type: filesandordirs; Name: "{app}\resources"

[Registry]
; Register application in Windows (AC2)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "SageFrame"; ValueType: string; ValueData: "{app}\SageFrame.exe"; Flags: uninsdeletevalue

; Application association (optional, for future protocol support)
Root: HKCU; Subkey: "Software\Classes\sageframe"; ValueType: string; ValueData: "URL:SageFrame Protocol"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\sageframe"; ValueName: "URL Protocol"; ValueType: string; ValueData: ""
Root: HKCU; Subkey: "Software\Classes\sageframe\DefaultIcon"; ValueType: string; ValueData: "{app}\SageFrame.exe,0"
Root: HKCU; Subkey: "Software\Classes\sageframe\shell\open\command"; ValueType: string; ValueData: """{app}\SageFrame.exe"" ""%1"""

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Welcome to SageFrame Setup
WelcomeLabel2=This will install [name/ver] on your computer.%n%nBefore continuing, close any other applications.
FinishedHeadingText=Completing SageFrame Setup
FinishedLabelFile=SageFrame has been installed successfully.
FinishedLabel=Setup has completed. You may now launch SageFrame from the Start Menu or Desktop.
