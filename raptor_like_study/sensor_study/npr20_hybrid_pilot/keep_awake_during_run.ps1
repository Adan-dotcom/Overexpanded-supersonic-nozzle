Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class AwakeState {
    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint flags);
}
"@

$ES_CONTINUOUS = [uint32]2147483648
$ES_SYSTEM_REQUIRED = [uint32]0x00000001

try {
    $flag = Join-Path $PSScriptRoot "keep_awake.flag"
    while (Test-Path -LiteralPath $flag) {
        [void][AwakeState]::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED)
        Start-Sleep -Seconds 30
    }
}
finally {
    [void][AwakeState]::SetThreadExecutionState($ES_CONTINUOUS)
}
