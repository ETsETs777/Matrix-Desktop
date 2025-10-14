@echo off
setlocal
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconsole --onefile --name MatrixDesktop app.py
echo Done. Check dist\MatrixDesktop.exe
endlocal
