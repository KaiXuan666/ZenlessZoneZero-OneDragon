Write-Host "1. Setting system volume to mute..."
try {
    $w = New-Object -ComObject Wscript.Shell
    for ($i = 0; $i -lt 50; $i++) {
        $w.SendKeys([char]174)
    }
    $w.SendKeys([char]173)
} catch {
    Write-Warning "Volume control failed: $_"
}

$maxRetries = 3
$retryCount = 0
$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
}
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = "e:\ZenlessZoneZero-OneDragon-v2.3.3"
}
$exePath = Join-Path $scriptDir "OneDragon-Launcher.exe"

do {
    $startTime = [System.DateTime]::Now
    Write-Host ("2. Starting OneDragon task (Attempt: {0})..." -f ($retryCount + 1))
    Write-Host "Executable path: $exePath"
    
    try {
        $process = Start-Process -FilePath $exePath -ArgumentList "-o -c" -WorkingDirectory $scriptDir -PassThru -Wait
        $exitCode = $process.ExitCode
        Write-Host "Process finished, ExitCode: $exitCode"
    } catch {
        Write-Error "Failed to start process: $_"
        $exitCode = -1
    }
    
    $endTime = [System.DateTime]::Now
    $duration = $endTime - $startTime
    Write-Host ("Task finished, Duration: {0:N2} seconds" -f $duration.TotalSeconds)

    if ($duration.TotalSeconds -lt 480) {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "Detected task finished in less than 8 minutes (possible crash or locked screen)."
            Write-Host "Waiting 60 seconds before next attempt..."
            
            try {
                $shell = New-Object -ComObject Wscript.Shell
                for ($i = 0; $i -lt 5; $i++) {
                    Start-Sleep -Seconds 2
                    $shell.SendKeys(" ")
                    $shell.SendKeys([char]16)
                }
            } catch {
                $null = $_
            }
            
            Start-Sleep -Seconds 50
        } else {
            Write-Host "Task failed repeatedly in less than 8 minutes, stopping retry."
            exit 1
        }
    } else {
        Write-Host "OneDragon task ran successfully for over 8 minutes."
        exit 0
    }
} while ($retryCount -lt $maxRetries)
