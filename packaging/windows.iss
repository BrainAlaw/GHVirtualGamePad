#define AppVersion "0.2.0-rc.2"

[Setup]
AppId={{99F54A90-5902-444F-A543-4377252E83D1}
AppName=GHVirtualGamePad
AppVersion={#AppVersion}
AppPublisher=BrainAlaw
AppPublisherURL=https://github.com/BrainAlaw/GHVirtualGamePad
DefaultDirName={autopf}\GHVirtualGamePad
DefaultGroupName=GHVirtualGamePad
OutputDir=..\artifacts
OutputBaseFilename=GHVirtualGamePad-{#AppVersion}-windows-x64-setup
SetupIconFile=..\artifacts\ghvirtualgamepad.ico
UninstallDisplayIcon={app}\GHVirtualGamePad.exe
LicenseFile=..\LICENSE
InfoBeforeFile=windows-drivers.txt
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
PrivilegesRequired=admin
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
SetupLogging=yes

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked
Name: vigem; Description: "Install missing ViGEmBus 1.22.0 (virtual Xbox controllers)"; Check: MissingViGEm
Name: interception; Description: "Install missing Interception 1.0.1 (keyboard filter; non-commercial use; reboot required)"; Check: MissingInterception

[Files]
Source: "..\artifacts\windows\GHVirtualGamePad\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\artifacts\windows-dependencies\ViGEmBus.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Tasks: vigem
Source: "..\artifacts\windows-dependencies\install-interception.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Tasks: interception

[Icons]
Name: "{group}\GHVirtualGamePad"; Filename: "{app}\GHVirtualGamePad.exe"
Name: "{group}\Uninstall GHVirtualGamePad"; Filename: "{uninstallexe}"
Name: "{autodesktop}\GHVirtualGamePad"; Filename: "{app}\GHVirtualGamePad.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GHVirtualGamePad.exe"; Description: "Open GHVirtualGamePad"; Flags: nowait postinstall skipifsilent runasoriginaluser; Check: NoDriverChanges

[Code]
var
  DriverChanges: Boolean;

function MissingViGEm: Boolean;
begin
  Result := not RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\ViGEmBus');
end;

function MissingInterception: Boolean;
begin
  Result := not (RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\keyboard') and
    RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\mouse'));
end;

function NoDriverChanges: Boolean;
begin
  Result := not DriverChanges;
end;

procedure InstallDriver(FileName, Parameters: String);
var
  Code: Integer;
begin
  if not Exec(ExpandConstant('{tmp}\') + FileName, Parameters, '', SW_HIDE, ewWaitUntilTerminated, Code) then
    RaiseException('Cannot start driver installer. Re-run setup to retry.');
  if (Code <> 0) and (Code <> 3010) and (Code <> 1641) then
    RaiseException('Driver installation failed (code ' + IntToStr(Code) + '). Do not disable Windows security protections.');
  DriverChanges := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    if WizardIsTaskSelected('vigem') and MissingViGEm then
      InstallDriver('ViGEmBus.exe', '/passive /norestart');
    if WizardIsTaskSelected('interception') and MissingInterception then
      InstallDriver('install-interception.exe', '/install');
  end;
end;

function NeedRestart: Boolean;
begin
  Result := DriverChanges;
end;
