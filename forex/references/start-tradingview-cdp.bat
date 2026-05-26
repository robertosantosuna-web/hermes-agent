@echo off
setlocal

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "(Get-AppxPackage *TradingView*).InstallLocation"`) do set "TVDIR=%%I"

if not defined TVDIR (
  echo Nao foi possivel localizar o TradingView.
  exit /b 1
)

start "" "%TVDIR%\TradingView.exe" --remote-debugging-port=9222
echo TradingView iniciado com debug port 9222.
endlocal
