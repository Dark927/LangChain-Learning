[Setup]
; App Information
AppName=Auto Solver Pro
AppVersion=1.0.0
AppPublisher=Auto Solver Repacks
AppPublisherURL=https://github.com/Dark927

; Default Installation Folder (Program Files)
DefaultDirName={autopf}\Auto Solver Pro
DefaultGroupName=Auto Solver Pro

; Output Installer EXE details
OutputDir=..\Output
OutputBaseFilename=AutoSolverPro_Setup_v1.0
Compression=lzma2/ultra64
SolidCompression=yes

; The "Repack Info" screen that shows before installation
InfoBeforeFile=repack_info.txt

; Modern UI Style
WizardStyle=modern
DisableWelcomePage=no

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; This tells Inno Setup to grab the PyInstaller output folder and compress it all into the EXE
Source: "..\dist\AutoSolverPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu Icon
Name: "{group}\Auto Solver Pro"; Filename: "{app}\AutoSolverPro.exe"
; Desktop Icon
Name: "{autodesktop}\Auto Solver Pro"; Filename: "{app}\AutoSolverPro.exe"; Tasks: desktopicon

[Run]
; Option to launch immediately after installation
Filename: "{app}\AutoSolverPro.exe"; Description: "{cm:LaunchProgram,Auto Solver Pro}"; Flags: nowait postinstall skipifsilent
