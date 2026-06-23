$file = 'C:\Program Files (x86)\PSCAD46\fortran_compilers.xml'
$bak = 'C:\Program Files (x86)\PSCAD46\fortran_compilers.xml.before_restore_gf42_detect_keep_gf46_build.bak'
Copy-Item -LiteralPath $file -Destination $bak -Force
$text = Get-Content -LiteralPath $file -Raw
$pattern = '(?m)^\s*<compiler name="MHRC"\s+version="4\.2\.1".*?/>\s*$'
$replacement = '   <compiler name="MHRC"   version="4.2.1"       version_key="GFortran\4.2.1,VersionString"                             title_key="GFortran\#,Title"                               exe_path_key="GFortran\#,binDir"                   exe_subpath=""            exe_name="gfortran.exe" emtdc="gf46"     batch_path=""       batch_name="gf46vars.bat"  batch_args=""        runtime_env="true"  title_suffix=""          compiler_type="x86" registry="x86"  />'
$new = [regex]::Replace($text, $pattern, $replacement, 1)
if ($new -eq $text) { throw 'Could not patch gf42 compiler entry.' }
Set-Content -LiteralPath $file -Value $new -Encoding UTF8
