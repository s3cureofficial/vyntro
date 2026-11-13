; Inno-Setup-Skript für den Windows-Installer von Vyntro.
; Wird vom GitHub-Workflow aufgerufen:  ISCC /DVersion=1.0.0 windows\vyntro.iss

#ifndef Version
  #define Version "1.0.0"
#endif

[Setup]
AppId={{6B0E8B3C-5D7A-4C1E-9E62-7A1F2C9D4B11}
AppName=Vyntro
AppVersion={#Version}
AppVerName=Vyntro {#Version}
AppPublisher=Vyntro
DefaultDirName={autopf}\Vyntro
DefaultGroupName=Vyntro
DisableProgramGroupPage=yes
; ohne Administratorrechte installierbar (landet dann im Benutzerordner)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\installer
OutputBaseFilename=Vyntro-Setup-{#Version}
SetupIconFile=..\branding\vyntro.ico
UninstallDisplayIcon={app}\Vyntro.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "Verknüpfung auf dem Desktop anlegen"; GroupDescription: "Zusätzlich:"

[Files]
Source: "..\dist\Vyntro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Vyntro"; Filename: "{app}\Vyntro.exe"
Name: "{group}\Vyntro deinstallieren"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Vyntro"; Filename: "{app}\Vyntro.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Vyntro.exe"; Description: "Vyntro jetzt starten"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Autostart-Eintrag entfernen, falls er in den Einstellungen eingeschaltet wurde
Filename: "reg.exe"; Parameters: "delete HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v Vyntro /f"; Flags: runhidden; RunOnceId: "AutostartEntfernen"
