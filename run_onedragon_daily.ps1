Write-Host "1. Setting system volume to mute..."
try {
    $code = @'
using System;
using System.Runtime.InteropServices;

[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IAudioEndpointVolume {
    int f1(); int f2(); int f3(); int f4();
    int SetMasterVolumeLevelScalar(float fLevel, Guid pguidEventContext);
    int f6();
    int GetMasterVolumeLevelScalar(out float pfLevel);
    int f8(); int f9(); int f10(); int f11();
    int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, Guid pguidEventContext);
    int GetMute(out bool pbMute);
}

[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDevice {
    int Activate(ref Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev);
}

[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMMDeviceEnumerator {
    int f1();
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
}

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
public class MMDeviceEnumeratorComObject { }

public class AudioController {
    public static void SetMute(bool mute) {
        var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
        IMMDevice dev = null;
        enumerator.GetDefaultAudioEndpoint(0, 1, out dev);
        
        IAudioEndpointVolume epv = null;
        Guid epvid = new Guid("5CDF2C82-841E-4546-9722-0CF74078229A");
        dev.Activate(ref epvid, 23, 0, out epv);
        
        epv.SetMute(mute, Guid.Empty);
    }
}
'@

    Add-Type -TypeDefinition $code -ReferencedAssemblies "System.Runtime.InteropServices"
    [AudioController]::SetMute($true)
    Write-Host "System volume successfully muted."
} catch {
    Write-Warning "System mute control failed: $_"
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
