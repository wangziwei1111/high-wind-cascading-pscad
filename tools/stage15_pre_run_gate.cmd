@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python analysis\pscad_tools\audit_stage15_pre_run_gate.py
pause
