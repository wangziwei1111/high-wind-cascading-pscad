$shim = 'C:\Program Files (x86)\GFortran\4.2.1\bin\gf46vars.bat'
$target = 'C:\Program Files (x86)\GFortran\4.6\bin\gf46vars.bat'
if (!(Test-Path -LiteralPath $target)) { throw "Target gf46vars.bat not found: $target" }
$content = @"
@echo off
call "$target"
"@
Set-Content -LiteralPath $shim -Value $content -Encoding ASCII
