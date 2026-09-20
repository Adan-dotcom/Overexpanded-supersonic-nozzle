param(
    [Parameter(Mandatory = $true)]
    [string]$SessionFile,

    [string]$OutputFile = (Join-Path (Split-Path -Parent $PSScriptRoot) 'CODEX_CONVERSATION.md')
)

$sessionPath = (Resolve-Path -LiteralPath $SessionFile).Path
$sessionName = [IO.Path]::GetFileNameWithoutExtension($sessionPath)
$sessionId = [regex]::Match(
    $sessionName,
    '[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$'
).Value
$messages = [Collections.Generic.List[string]]::new()
$utf8 = [Text.UTF8Encoding]::new($false)

$messages.Add('# Codex conversation transcript')
$messages.Add('')
$messages.Add('> Sanitized export containing only user and assistant messages. Tool calls, tool outputs,')
$messages.Add('> reasoning records, credentials, and Codex internal metadata are intentionally omitted.')
$messages.Add('> This is context for a new Codex session; it is not an importable Codex session database.')
$messages.Add('')
$messages.Add("- Original session ID: ``$sessionId``")
$messages.Add("- Exported UTC: ``$([DateTime]::UtcNow.ToString('o'))``")
$messages.Add('')

$stream = [IO.FileStream]::new(
    $sessionPath,
    [IO.FileMode]::Open,
    [IO.FileAccess]::Read,
    [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete
)
$reader = [IO.StreamReader]::new($stream, $utf8, $true)
try {
    while (($line = $reader.ReadLine()) -ne $null) {
        try {
            $record = $line | ConvertFrom-Json
        }
        catch {
            continue
        }

        if ($record.type -ne 'response_item' -or $record.payload.type -ne 'message') {
            continue
        }

        $role = [string]$record.payload.role
        if ($role -notin @('user', 'assistant')) {
            continue
        }

        $parts = foreach ($item in $record.payload.content) {
            if ($item.type -in @('input_text', 'output_text', 'text') -and $item.text) {
                [string]$item.text
            }
        }
        $body = ($parts -join "`n`n").Trim()
        if (-not $body) {
            continue
        }

        $heading = if ($role -eq 'user') { 'User' } else { 'Assistant' }
        $messages.Add("## $heading")
        $messages.Add('')
        $messages.Add($body)
        $messages.Add('')
    }
}
finally {
    $reader.Dispose()
    $stream.Dispose()
}

$outputPath = [IO.Path]::GetFullPath($OutputFile)
[IO.File]::WriteAllLines($outputPath, $messages, $utf8)

$messageCount = ($messages | Where-Object { $_ -in @('## User', '## Assistant') }).Count
$size = (Get-Item -LiteralPath $outputPath).Length
Write-Output ("Wrote {0}: {1} messages, {2:N2} MiB" -f $outputPath, $messageCount, ($size / 1MB))
