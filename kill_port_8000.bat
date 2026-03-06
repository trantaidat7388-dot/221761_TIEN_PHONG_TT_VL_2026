@echo off
echo Looking for process listening on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    if NOT "%%a"=="0" (
        echo Killing PID %%a
        taskkill /F /PID %%a
    )
)
echo Done.
