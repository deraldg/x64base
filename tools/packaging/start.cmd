@echo off
rem start.cmd -- launch DotTalk++ from an unzipped x64base release, for
rem double-click or cmd.exe use. Same behaviour as start.ps1: start from data\
rem so the runtime finds its data, pass any arguments through, and return to
rem the original folder afterwards.
rem   start.cmd                  interactive shell
rem   start.cmd --script my.dts  arguments pass straight through
setlocal
pushd "%~dp0data" || (echo start.cmd: data folder not found beside this script & exit /b 1)
"%~dp0bin\dottalkpp.exe" %*
set "RC=%ERRORLEVEL%"
popd
endlocal & exit /b %RC%
