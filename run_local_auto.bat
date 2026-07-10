@echo off
REM ── Kiwoom Daily Gainers — auto-run (Windows Task Scheduler, weekdays 15:40) ──
REM Requires: Kiwoom OpenAPI+ auto-login ON + PC powered on (logged-in session).
REM EDIT the two paths below to match your machine, then point Task Scheduler here.

set REPO_DIR=C:\path\to\kiwoom-daily-gainers
set CONDA_ACTIVATE=C:\Users\<you>\miniconda3\Scripts\activate.bat

cd /d "%REPO_DIR%"
if not exist logs mkdir logs
echo ================ %date% %time% ================ >> "logs\local_auto.log"
call "%CONDA_ACTIVATE%" py38_32
python market_briefing.py >> "logs\local_auto.log" 2>&1
echo [exit %errorlevel%] >> "logs\local_auto.log"
