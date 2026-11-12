param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9.-]+$')][string]$RemoteHost,
    [Parameter(Mandatory=$true)][ValidateRange(1,65535)][int]$SshPort,
    [Parameter(Mandatory=$true)][string]$IdentityFile,
    [Parameter(Mandatory=$true)][ValidatePattern('^/workspace/aegis/evidence/multicam/p2-smoke-\d{8}T\d{6}Z-[0-9a-f]{8}$')][string]$RemoteRunPath,
    [Parameter(Mandatory=$true)][string]$EvidenceRoot,
    [Parameter(Mandatory=$true)][string]$StatusPath,
    [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$RemoteUser = 'root'
)

if (-not (Test-Path -LiteralPath $IdentityFile -PathType Leaf)) { throw 'SSH identity file is missing.' }
if (Test-Path -LiteralPath $StatusPath) { throw 'Refusing to overwrite a status record.' }
$runName = ($RemoteRunPath -split '/')[-1]
$localRun = Join-Path $EvidenceRoot $runName
if (Test-Path -LiteralPath $localRun) { throw 'Run already exists locally; refusing to overwrite evidence.' }
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetFullPath($EvidenceRoot)) | Out-Null
$startedAt = [DateTime]::UtcNow.ToString('o')
@{ phase='waiting_for_authentication'; started_at_utc=$startedAt; local_run=$localRun } |
    ConvertTo-Json | Set-Content -LiteralPath $StatusPath -Encoding UTF8
Write-Host 'AEGIS: enter your SSH key passphrase to download the completed run.'
$scpExitCode = 255
try {
    $source = $RemoteUser + '@' + $RemoteHost + ':' + $RemoteRunPath
    & scp -r -P $SshPort -o StrictHostKeyChecking=yes -o UpdateHostKeys=no -o ConnectTimeout=10 `
        -i $IdentityFile $source $EvidenceRoot
    $scpExitCode = $LASTEXITCODE
} finally {
    @{ phase='finished'; started_at_utc=$startedAt; finished_at_utc=[DateTime]::UtcNow.ToString('o');
       exit_code=$scpExitCode; local_run=$localRun } |
        ConvertTo-Json | Set-Content -LiteralPath $StatusPath -Encoding UTF8
}
Write-Host ('Download exit code: ' + $scpExitCode + '. Codex can inspect the local files.')
