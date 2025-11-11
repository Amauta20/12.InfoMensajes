@echo off

:: Build the executable with PyInstaller
echo Building executable...
call pyinstaller main.spec

:: Build the installer with Inno Setup
echo Building installer...
call "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "installer.iss"

echo Build complete!
