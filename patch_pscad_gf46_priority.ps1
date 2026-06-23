$file = 'C:\Program Files (x86)\PSCAD46\fortran_compilers.xml'
$bak = 'C:\Program Files (x86)\PSCAD46\fortran_compilers.xml.before_gf46_priority.bak'
Copy-Item -LiteralPath $file -Destination $bak -Force
$text = Get-Content -LiteralPath $file -Raw
$gf42 = [regex]::Match($text, '(?m)^\s*<compiler name="MHRC"\s+version="4\.2\.1".*?/>\s*$').Value
$gf46 = [regex]::Match($text, '(?m)^\s*<compiler name="MHRC"\s+version="4\.6\.2".*?/>\s*$').Value
if (-not $gf42 -or -not $gf46) { throw 'Could not find gf42/gf46 compiler lines.' }
$text = $text.Replace($gf42, '__GF42_PLACEHOLDER__').Replace($gf46, $gf46 + "`r`n" + $gf42).Replace('__GF42_PLACEHOLDER__', '').Replace("`r`n`r`n   <compiler name=`"INTEL`"", "`r`n   <compiler name=`"INTEL`"")
Set-Content -LiteralPath $file -Value $text -Encoding UTF8
