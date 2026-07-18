Unicode True

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"

!ifndef APP_VERSION
  !define APP_VERSION "0.0.0"
!endif

!ifndef APP_VERSION_NUM
  !define APP_VERSION_NUM "0.0.0.0"
!endif

!define APP_NAME "QuantumScribe"
!define APP_PUBLISHER "Natan Melquiades"
!define APP_URL "https://github.com/Natanmelquiades/QuantumScribe"
!define APP_EXE "QuantumScribe.exe"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\QuantumScribe"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "..\dist\QuantumScribe-Setup-${APP_VERSION}-Windows-x64.exe"
InstallDir "$LOCALAPPDATA\Programs\${APP_NAME}"
RequestExecutionLevel user
SetCompressor /SOLID lzma
CRCCheck on
ManifestDPIAware true
BrandingText "${APP_NAME} — instalação por usuário"
Icon "..\build\QuantumScribe.ico"
UninstallIcon "..\build\QuantumScribe.ico"

VIProductVersion "${APP_VERSION_NUM}"
VIAddVersionKey /LANG=1046 "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey /LANG=1046 "FileDescription" "Instalador do ${APP_NAME}"
VIAddVersionKey /LANG=1046 "FileVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1046 "LegalCopyright" "Copyright (c) 2026 ${APP_PUBLISHER}"
VIAddVersionKey /LANG=1046 "ProductName" "${APP_NAME}"
VIAddVersionKey /LANG=1046 "ProductVersion" "${APP_VERSION}"

!define MUI_ABORTWARNING
!define MUI_ICON "..\build\QuantumScribe.ico"
!define MUI_UNICON "..\build\QuantumScribe.ico"
!define MUI_WELCOMEPAGE_TEXT "Este assistente instala somente o Core leve do ${APP_NAME} para o usuário atual.$\r$\n$\r$\nModelos e aceleração NVIDIA só serão baixados depois de uma confirmação explícita no aplicativo."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Abrir o ${APP_NAME}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "PortugueseBR"

Section "${APP_NAME} (obrigatório)" SecMain
  SectionIn RO
  SetShellVarContext current
  SetOutPath "$INSTDIR"

  ; Remove apenas os arquivos conhecidos do bundle anterior. Arquivos que não
  ; pertencem ao Quantum Scribe são preservados mesmo dentro da pasta fixa.
  !include "generated_uninstall_files.nsh"
  File /r "..\dist\QuantumScribe\*.*"

  FileOpen $0 "$INSTDIR\.quantumscribe-install" w
  FileWrite $0 "${APP_NAME} ${APP_VERSION}$\r$\n"
  FileClose $0

  WriteUninstaller "$INSTDIR\Desinstalar.exe"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0

  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "URLInfoAbout" "${APP_URL}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '$\"$INSTDIR\Desinstalar.exe$\"'
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section /o "Atalho na área de trabalho" SecDesktop
  SetShellVarContext current
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} "Instala o aplicativo, o desinstalador e o atalho do menu Iniciar."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Cria também um atalho opcional na área de trabalho."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Function CheckAppRunning
  System::Call 'kernel32::OpenMutexW(i 0x00100000, i 0, w "LocalWhisper.SingleInstance") p.r0'
  ${If} $0 != 0
    System::Call 'kernel32::CloseHandle(p r0)'
    MessageBox MB_ICONEXCLAMATION|MB_OK "O ${APP_NAME} está aberto. Encerre-o pelo ícone da bandeja antes de instalar ou atualizar." /SD IDOK
    Abort
  ${EndIf}
FunctionEnd

Function .onInit
  SetShellVarContext current
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP|MB_OK "Esta versão do ${APP_NAME} requer Windows de 64 bits." /SD IDOK
    Abort
  ${EndIf}
  Call CheckAppRunning
FunctionEnd

Section "Uninstall"
  SetShellVarContext current
  ${If} $INSTDIR != "$LOCALAPPDATA\Programs\${APP_NAME}"
    MessageBox MB_ICONSTOP|MB_OK "Local de instalação inválido. A desinstalação foi cancelada para proteger seus arquivos." /SD IDOK
    Abort
  ${EndIf}
  IfFileExists "$INSTDIR\.quantumscribe-install" +3 0
    MessageBox MB_ICONSTOP|MB_OK "Marcador de instalação ausente. Nenhum arquivo foi removido." /SD IDOK
    Abort

  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}.lnk"
  DeleteRegKey HKCU "${UNINSTALL_KEY}"

  ; Dados em %LOCALAPPDATA%\QuantumScribe ficam preservados intencionalmente.
  !include "generated_uninstall_files.nsh"
  Delete "$INSTDIR\.quantumscribe-install"
  Delete "$INSTDIR\Desinstalar.exe"
  RMDir "$INSTDIR"
SectionEnd

Function un.CheckAppRunning
  System::Call 'kernel32::OpenMutexW(i 0x00100000, i 0, w "LocalWhisper.SingleInstance") p.r0'
  ${If} $0 != 0
    System::Call 'kernel32::CloseHandle(p r0)'
    MessageBox MB_ICONEXCLAMATION|MB_OK "O ${APP_NAME} está aberto. Encerre-o pelo ícone da bandeja antes de desinstalar." /SD IDOK
    Abort
  ${EndIf}
FunctionEnd

Function un.onInit
  SetShellVarContext current
  Call un.CheckAppRunning
FunctionEnd
