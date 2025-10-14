@echo off
setlocal
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller pillow

if not exist assets mkdir assets
if exist assets\calc.png (
  if not exist assets\calc.ico (
    python - <<PY
from PIL import Image
im = Image.open('assets/calc.png').convert('RGBA')
sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
im.save('assets/calc.ico', sizes=sizes)
PY
  )
)

pyinstaller --noconsole --onefile --name MatrixDesktop --icon assets\calc.ico app.py

if exist dist\MatrixDesktop.exe (
  copy /Y dist\MatrixDesktop.exe RUN.exe >nul
  echo Built RUN.exe at project root
  rem Optional code signing: set SIGN_PFX=path\to\cert.pfx and SIGN_PWD=secret before running
  if defined SIGN_PFX (
    where signtool >nul 2>nul && (
      echo Signing RUN.exe with %SIGN_PFX%
      signtool sign /f "%SIGN_PFX%" /p "%SIGN_PWD%" /fd sha256 /tr http://timestamp.digicert.com /td sha256 "RUN.exe"
    ) || (
      echo signtool not found in PATH, skipping signing
    )
  ) else (
    echo SIGN_PFX is not set, skipping signing
  )
  rem Create desktop shortcut
  powershell -NoProfile -ExecutionPolicy Bypass -Command "
    $desktop = [Environment]::GetFolderPath('Desktop');
    $ws = New-Object -ComObject WScript.Shell;
    $lnk = Join-Path $desktop 'MatrixDesktop.lnk';
    $sc = $ws.CreateShortcut($lnk);
    $sc.TargetPath = (Join-Path $PSScriptRoot 'RUN.exe');
    $sc.WorkingDirectory = $PSScriptRoot;
    if (Test-Path (Join-Path $PSScriptRoot 'assets/calc.ico')) { $sc.IconLocation = (Join-Path $PSScriptRoot 'assets/calc.ico') };
    $sc.Save();
  "
  echo Desktop shortcut created.
) else (
  echo Build failed, dist\MatrixDesktop.exe not found
)

endlocal
