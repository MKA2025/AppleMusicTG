@echo off

REM Create virtual environment
python -m venv venv
call venv\Scripts\activate

REM Install requirements
pip install -r requirements.txt

REM Create necessary directories
mkdir downloads 2>nul
mkdir temp 2>nul
mkdir config 2>nul

REM Copy example config if not exists
if not exist config\config.json (
    copy config\config.example.json config\config.json
    echo Please edit config\config.json with your settings
)
