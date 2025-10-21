; -- VidSnare Installer Script for Inno Setup --

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (Generate a new GUID yourself using online tools or Inno Setup's wizard)
AppId=eaf79510-2373-46fb-9a99-0b54163d5ba4 
AppName=VidSnare Downloader
AppVersion=1.0 
; AppPublisher=Your Name or Company (Optional)
; AppPublisherURL=Your Website (Optional)
; AppSupportURL=Your Support URL (Optional)
; AppUpdatesURL=Your Update Info URL (Optional)
DefaultDirName={autopf}\VidSnare Downloader
; Default folder name in the Start Menu
DefaultGroupName=VidSnare Downloader
AllowNoIcons=yes
; LicenseFile=path\to\your\license.txt (Optional)
; InfoBeforeFile=path\to\your\readme.txt (Optional)
OutputBaseFilename=VidSnare_Setup_v1.0
SetupIconFile=vidsnare_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Require admin privileges for installing to Program Files
PrivilegesRequired=admin

; Define the icon used in Add/Remove Programs (Control Panel)
; Use the application exe itself, as PyInstaller embeds the icon
UninstallDisplayIcon={app}\VidSnare.exe 

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Add an option during install to create a desktop icon
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; **IMPORTANT**: This line copies the main executable from your PyInstaller dist folder
Source: "dist\VidSnare.exe"; DestDir: "{app}"; Flags: ignoreversion

; **DEPENDENCY NOTE**: If yt-dlp.exe or ffmpeg.exe are NOT bundled inside your 
; VidSnare.exe (e.g., using PyInstaller's --add-binary), you MUST copy them here too.
; Example (if they are separate files in your project dir or a subfolder):
; Source: "path\to\yt-dlp.exe"; DestDir: "{app}"; Flags: ignoreversion
; Source: "path\to\ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion
; Source: "path\to\ffprobe.exe"; DestDir: "{app}"; Flags: ignoreversion 

; If you have other necessary data files, copy them here as well.
; Source: "your_data_folder\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu Shortcut
Name: "{group}\VidSnare Downloader"; Filename: "{app}\VidSnare.exe"
; Desktop Shortcut (only if task selected)
Name: "{commondesktop}\VidSnare Downloader"; Filename: "{app}\VidSnare.exe"; Tasks: desktopicon

; Use the icon embedded within the executable for shortcuts
; No separate IconFilename needed if PyInstaller embedded it correctly.

[Run]
; Optional: Run the application after installation finishes
Filename: "{app}\VidSnare.exe"; Description: "{cm:LaunchProgram,VidSnare Downloader}"; Flags: nowait postinstall skipifsilent