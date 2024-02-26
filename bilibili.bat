@echo off
cd /d %~dp0
set p=%1
if not defined p goto main

set params=

:while
set p=%1
if not defined p (
    goto elihw
)
set params=%params% %p%
shift /0
goto while

:elihw
python bDownloader.py %params%
goto end

:main
echo «Î ‰»Î ”∆µÕ¯÷∑£∫
set /p site=
echo «Î ‰»Îsessdata£∫
set /p sess=
if "%sess%" neq "" (set sess=-s %sess%)
set params=%sess% %site%
python bDownloader.py %params%

:end
pause