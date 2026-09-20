param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$patterns = @(
    '*.vtk', '*.vtu', '*.dat', '*.su2', '*.msh', '*.stl', '*.cgns',
    '*.exe', '*.dll', '*.lib', 'cea-linux',
    'restart*.csv', 'seed_*.csv', 'history*.csv', 'wall_npr*.csv',
    'wall.csv',
    'wall_smoke*.csv', 'wall_continue*.csv', 'wall_relax*.csv',
    'wall_safe*.csv', 'wall_urans*.csv'
)

$rootPath = (Resolve-Path -LiteralPath $Root).Path
$rows = foreach ($file in Get-ChildItem -LiteralPath $rootPath -File -Recurse) {
    $matched = $false
    foreach ($pattern in $patterns) {
        if ($file.Name -like $pattern) {
            $matched = $true
            break
        }
    }
    if ($matched) {
        [pscustomobject]@{
            relative_path = $file.FullName.Substring($rootPath.Length + 1)
            size_bytes = $file.Length
            modified_utc = $file.LastWriteTimeUtc.ToString('o')
            disposition = 'local_regenerable_not_in_git'
        }
    }
}

$output = Join-Path $rootPath 'LOCAL_ARTIFACTS_MANIFEST.csv'
$rows | Sort-Object relative_path | Export-Csv -LiteralPath $output -NoTypeInformation -Encoding utf8
$bytes = ($rows | Measure-Object size_bytes -Sum).Sum
Write-Output ("Wrote {0}: {1} artifacts, {2:N2} GiB" -f $output, $rows.Count, ($bytes / 1GB))
