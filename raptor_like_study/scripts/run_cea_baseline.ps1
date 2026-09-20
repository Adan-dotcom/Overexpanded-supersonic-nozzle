$StudyRoot = Split-Path -Parent $PSScriptRoot
$CeaDir = Join-Path $StudyRoot 'tools\cea-3.3.4'
$Input = Join-Path $StudyRoot 'cases\cea\baseline.inp'
$WslCeaDir = '/mnt/d/PRUEBA SU2_2026/raptor_like_study/tools/cea-3.3.4'
$WslInput = '/mnt/d/PRUEBA SU2_2026/raptor_like_study/cases/cea/baseline.inp'
wsl.exe -d Ubuntu -- bash -lc "chmod +x '$WslCeaDir/cea-linux'; cd '$WslCeaDir'; ./cea-linux '$WslInput'"
wsl.exe -d Ubuntu -- python3 '/mnt/d/PRUEBA SU2_2026/raptor_like_study/scripts/parse_cea_baseline.py'
