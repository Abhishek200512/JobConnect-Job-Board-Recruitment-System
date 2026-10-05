@echo off
title JobConnect - Job Board & Recruitment Management System
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [JobConnect] Creating virtual environment...
    python -m venv .venv
    echo [JobConnect] Installing dependencies...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)

if not exist ".env" (
    echo [JobConnect] Creating .env from .env.example
    copy .env.example .env >nul
)

echo [JobConnect] Applying migrations...
.venv\Scripts\python.exe manage.py migrate

echo [JobConnect] Starting server at http://127.0.0.1:8000
start "" http://127.0.0.1:8000
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
pause
