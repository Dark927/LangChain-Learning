@echo off
cd ..
echo ==============================================
echo      AUTO SOLVER PRO - REPACK BUILDER
echo ==============================================
echo.

echo [1/3] Installing/Verifying Python Dependencies...
python -m pip install pyinstaller customtkinter pillow pyautogui pytesseract pyperclip

echo.
echo [2/3] Compiling Python Code to Standalone Binaries...
echo (This may take a minute or two...)
python -m PyInstaller --noconfirm --onedir --windowed --add-data "themes;themes" --name "AutoSolverPro" src\main.py

echo.
echo [Fix] Copying missing python3.dll (PyInstaller workaround)...
for /f "delims=" %%I in ('python -c "import sys, os; print(os.path.join(sys.base_exec_prefix, 'python3.dll'))"') do set "PYTHON3_DLL=%%I"
if exist "%PYTHON3_DLL%" (
    copy "%PYTHON3_DLL%" "dist\AutoSolverPro\_internal\" >nul
    echo Successfully patched missing Python DLL!
)

move AutoSolverPro.spec repack\ >nul 2>&1

echo.
echo [3/3] Building Repack Installer...
:: Check if Inno Setup is installed in common directories
set "INNO_PATH="
if exist "C:\Program Files (x86)\Inno Setup 7\ISCC.exe" set "INNO_PATH=C:\Program Files (x86)\Inno Setup 7\ISCC.exe"
if exist "C:\Program Files\Inno Setup 7\ISCC.exe" set "INNO_PATH=C:\Program Files\Inno Setup 7\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" set "INNO_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 5\ISCC.exe" set "INNO_PATH=C:\Program Files\Inno Setup 5\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" set "INNO_PATH=%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "INNO_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 5\ISCC.exe" set "INNO_PATH=%LOCALAPPDATA%\Programs\Inno Setup 5\ISCC.exe"

if defined INNO_PATH (
    echo Compiling Setup.exe with Inno Setup...
    "%INNO_PATH%" repack\installer.iss
    echo.
    echo ==============================================
    echo SUCCESS: You can find your final Repack Installer in the "Output" folder!
    echo ==============================================
    explorer "Output"
) else (
    echo.
    echo ==============================================
    echo ALMOST DONE! 
    echo PyInstaller finished freezing your code into the "dist\AutoSolverPro" folder.
    echo.
    echo To create the final "Setup.exe" Installer Wizard:
    echo 1. Download and install Inno Setup (https://jrsoftware.org/isdl.php)
    echo 2. Right-click the "installer.iss" file in the "repack" folder.
    echo 3. Click "Compile".
    echo.
    echo Your professional repack installer will be outputted to the "Output" folder!
    echo ==============================================
    explorer "dist\AutoSolverPro"
)

pause
