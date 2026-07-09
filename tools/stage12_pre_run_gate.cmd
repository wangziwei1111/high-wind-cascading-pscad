@echo off
setlocal
cd /d "%~dp0\.."
python analysis\pscad_tools\audit_stage12_pre_run_gate.py
pause
