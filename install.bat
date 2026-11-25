@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Instalasi Sistem Nota
echo ============================================
echo.
echo [1/3] Membuat virtual environment (.venv) dengan Python 3.9 ...
py -3.9 -m venv .venv
if errorlevel 1 (
  echo     Perintah "py -3.9" tidak tersedia, mencoba "python" ...
  python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
  echo.
  echo GAGAL membuat .venv.
  echo Pastikan Python 3.9 sudah terpasang ^(python.org/downloads/release/python-3913^).
  echo.
  pause
  exit /b 1
)
echo [2/3] Memperbarui pip ...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
echo [3/3] Memasang dependensi (Flask, waitress) ...
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo GAGAL memasang dependensi. Periksa koneksi internet lalu ulangi.
  pause
  exit /b 1
)
echo.
echo ============================================
echo   Selesai. Jalankan start.bat untuk membuka aplikasi.
echo ============================================
pause
