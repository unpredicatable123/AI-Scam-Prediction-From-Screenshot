@echo off
REM Runs a command fully detached from whatever shell launched it, via Windows
REM Task Scheduler. Needed because processes started with a normal background
REM `&`/job — including through the Claude Code session's own backgrounding —
REM stay children of that session's process tree and get killed when the
REM session ends (confirmed twice on this project: a training run silently
REM died with zero output partway through, both after a `cmd &` mistake and,
REM separately, just from an overnight session gap). A Task-Scheduler-launched
REM process is owned by the Schedule service instead, so it survives regardless
REM of what happens to the calling session.
REM
REM Usage: run-detached.bat <task-name> <working-dir> <log-file> <command...>
REM   task-name   short unique name, e.g. train-model-v4
REM   working-dir directory to run the command in
REM   log-file    where stdout+stderr are captured; a sibling <log-file>.exitcode
REM               file is written when the command finishes (absence = still running)
REM   command     the actual command line to run, e.g. python -m src.training.train ...
REM
REM Check on it later with:
REM   type <log-file>                 (see progress/output so far)
REM   type <log-file>.exitcode        (only exists once finished; 0 = success)
REM   schtasks /query /tn <task-name>  (fails once cleaned up -- that's expected)

setlocal enabledelayedexpansion

set "TASKNAME=%~1"
set "WORKDIR=%~2"
set "LOGFILE=%~3"
if "%TASKNAME%"=="" goto :usage
if "%WORKDIR%"=="" goto :usage
if "%LOGFILE%"=="" goto :usage

shift
shift
shift

REM NOTE: %* does NOT reflect `shift` in cmd.exe -- it always holds the
REM original full argument list. Rebuilding the remainder manually via %1
REM (which DOES advance with shift) is the only reliable way to do this.
set "CMD="
:collect
if "%~1"=="" goto :collected
if defined CMD (set "CMD=!CMD! %1") else (set "CMD=%1")
shift
goto :collect
:collected
if "%CMD%"=="" goto :usage

set "RUNNER=%TEMP%\run-detached-%TASKNAME%.bat"
> "%RUNNER%" (
    echo @echo off
    echo cd /d "%WORKDIR%"
    echo %CMD% ^> "%LOGFILE%" 2^>^&1
    echo echo %%errorlevel%% ^> "%LOGFILE%.exitcode"
)

del "%LOGFILE%.exitcode" 2>nul

schtasks /create /tn "%TASKNAME%" /tr "\"%RUNNER%\"" /sc once /st 23:59 /f >nul
if errorlevel 1 (
    echo Failed to create scheduled task.
    exit /b 1
)

schtasks /run /tn "%TASKNAME%" >nul
if errorlevel 1 (
    echo Failed to trigger scheduled task.
    exit /b 1
)

REM Give the task a moment to actually spawn its process before we clean up
REM the task definition (the definition isn't needed once the process is
REM running -- it's owned by the Schedule service by then). Fully-qualified
REM path avoids Git-Bash's coreutils `ping`/`timeout` shadowing the real ones.
"%SystemRoot%\System32\ping.exe" -n 4 127.0.0.1 >nul
schtasks /delete /tn "%TASKNAME%" /f >nul 2>&1

echo Launched detached: %CMD%
echo   Log:         %LOGFILE%
echo   Done marker: %LOGFILE%.exitcode
exit /b 0

:usage
echo Usage: run-detached.bat ^<task-name^> ^<working-dir^> ^<log-file^> ^<command...^>
exit /b 1
