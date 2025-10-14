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
) else (
  echo Build failed, dist\MatrixDesktop.exe not found
)

endlocal
