param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9.-]+$')][string]$RemoteHost,
    [Parameter(Mandatory=$true)][ValidateRange(1,65535)][int]$SshPort,
    [Parameter(Mandatory=$true)][string]$IdentityFile,
    [Parameter(Mandatory=$true)][string]$RunnerPath,
    [Parameter(Mandatory=$true)][string]$LogPath,
    [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$RemoteUser = 'root',
    [ValidateSet('Capture','SumoSetup','StaticMap','LiveFeed','Cosim')][string]$TaskKind = 'Capture'
)

# The private key stays in OpenSSH. This script never reads or records its contents.
if (-not (Test-Path -LiteralPath $IdentityFile -PathType Leaf)) { throw 'SSH identity file is missing.' }
if (-not (Test-Path -LiteralPath $RunnerPath -PathType Leaf)) { throw 'Capture runner is missing.' }
if (Test-Path -LiteralPath $LogPath) { throw 'Refusing to overwrite an existing log.' }
$statusPath = $LogPath + '.status.json'
if (Test-Path -LiteralPath $statusPath) { throw 'Refusing to overwrite an existing status record.' }
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($LogPath))) | Out-Null
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$startedAt = [DateTime]::UtcNow.ToString('o')
@{ phase='waiting_for_authentication'; started_at_utc=$startedAt; log=$LogPath } |
    ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding UTF8
Write-Host 'AEGIS: enter your SSH key passphrase in this window only.'
$forwardOptions = @()
if ($TaskKind -eq 'Cosim') {
    Write-Host 'Approved 30-second CARLA/SUMO clock test. Existing server/map are reused.'
    $remoteCommand = "tr -d '\r' | AEGIS_APPROVE_LIVE_COSIM=yes bash --noprofile --norc -s"
} elseif ($TaskKind -eq 'LiveFeed') {
    Write-Host 'This task runs a bounded camera/YOLO feed test and forwards it to http://127.0.0.1:8765.'
    $remoteCommand = "tr -d '\r' | AEGIS_APPROVE_LIVE_CAMERA_FEED=yes bash --noprofile --norc -s"
    $forwardOptions = @('-L','127.0.0.1:8765:127.0.0.1:8765','-o','ExitOnForwardFailure=yes')
} elseif ($TaskKind -eq 'Capture') {
    Write-Host 'This test warms YOLO, captures four angled views, and cleans up its temporary sensors.'
    $remoteCommand = "tr -d '\r' | AEGIS_APPROVE_FOUR_CAMERA_CAPTURE=yes bash --noprofile --norc -s"
} elseif ($TaskKind -eq 'SumoSetup') {
    Write-Host 'This task installs only the four approved SUMO/lxml packages and checks their versions/APIs.'
    $remoteCommand = "tr -d '\r' | AEGIS_APPROVE_SUMO_PACKAGES=yes bash --noprofile --norc -s"
} else {
    Write-Host 'This task exports the existing map and converts static network files. It starts no simulator.'
    $remoteCommand = "tr -d '\r' | bash --noprofile --norc -s"
}
if ($TaskKind -ne 'Cosim') { Write-Host 'CARLA stays on its current map; there are no manual simulation ticks.' }
$sshExitCode = 255
try {
    $destination = $RemoteUser + '@' + $RemoteHost
    Get-Content -Raw -LiteralPath $RunnerPath |
        & ssh -T -o StrictHostKeyChecking=yes -o UpdateHostKeys=no -o ConnectTimeout=10 `
          -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -i $IdentityFile -p $SshPort `
          @forwardOptions $destination $remoteCommand 2>&1 |
        Tee-Object -FilePath $LogPath
    $sshExitCode = $LASTEXITCODE
} finally {
    @{ phase='finished'; started_at_utc=$startedAt; finished_at_utc=[DateTime]::UtcNow.ToString('o');
       exit_code=$sshExitCode; log=$LogPath } |
        ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding UTF8
}
Write-Host ('AEGIS finished with SSH exit code ' + $sshExitCode + '. Codex can read the saved log.')
