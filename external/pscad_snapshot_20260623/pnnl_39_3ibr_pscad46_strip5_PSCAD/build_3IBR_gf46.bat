@echo off
setlocal
cd /d "%~dp03IBR.gf46"
call "C:\Program Files (x86)\GFortran\4.6\bin\gf46vars.bat"
make -f 3IBR.mak
endlocal
