@echo off
cd /d "e:\ZenlessZoneZero-OneDragon-v2.3.3"
powershell -NoProfile -ExecutionPolicy Bypass -File "e:\ZenlessZoneZero-OneDragon-v2.3.3\run_onedragon_daily.ps1" > "e:\ZenlessZoneZero-OneDragon-v2.3.3\scheduler_debug.log" 2>&1
