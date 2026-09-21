$StudyRoot = Split-Path -Parent $PSScriptRoot
$WslStudyRoot = (wsl.exe -d Ubuntu -- wslpath -a $StudyRoot).Trim()
$WslCeaDir = "$WslStudyRoot/tools/cea-3.3.4"
$WslInput = "$WslStudyRoot/cases/cea/baseline.inp"
wsl.exe -d Ubuntu -- bash -lc "chmod +x '$WslCeaDir/cea-linux'; cd '$WslCeaDir'; ./cea-linux '$WslInput'"
wsl.exe -d Ubuntu -- python3 "$WslStudyRoot/scripts/parse_cea_baseline.py"
