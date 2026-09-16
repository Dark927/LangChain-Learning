@echo off
cd ..
echo ==============================================
echo      AUTO SOLVER PRO - REPACK BUILDER
echo ==============================================
echo.

echo [1/4] Installing/Verifying Python Dependencies...
python -m pip install pyinstaller customtkinter pillow pyautogui pytesseract pyperclip cairosvg pix2text gpt4all

echo.
echo [2/4] Generating favicon.ico from logo.svg...
python repack\svg_to_ico.py logo.svg favicon.ico

echo.
echo [3/4] Compiling Python Code to Standalone Binaries...
echo (This may take a minute or two...)
python -m PyInstaller --noconfirm --onedir --windowed --icon="favicon.ico" --add-data "favicon.ico;." --add-data "themes;themes" --name "AutoSolverPro" src\main.py

echo.
echo [Fix] Copying missing python3.dll (PyInstaller workaround)...
for /f "delims=" %%I in ('python -c "import sys, os; print(os.path.join(sys.base_exec_prefix, 'python3.dll'))"') do set "PYTHON3_DLL=%%I"
if exist "%PYTHON3_DLL%" (
    copy "%PYTHON3_DLL%" "dist\AutoSolverPro\_internal\" >nul
    echo Successfully patched missing Python DLL!
)

echo.
echo [3.5/4] Bundling Tesseract OCR into Repack...
if exist "C:\Program Files\Tesseract-OCR" (
    xcopy "C:\Program Files\Tesseract-OCR" "dist\AutoSolverPro\Tesseract-OCR" /E /I /H /Y >nul
    echo Successfully bundled local Tesseract-OCR into the Repack!
) else (
    echo WARNING: Tesseract-OCR not found in C:\Program Files\Tesseract-OCR.
    echo The repack will not include Tesseract. Users will need to install it manually.
)

move AutoSolverPro.spec repack\ >nul 2>&1

echo.
echo [4/4] Building Repack Installer...
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
