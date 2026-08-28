@echo off
setlocal enabledelayedexpansion
rem Run the Playwright test suite in CLI (default) or GUI mode.
rem
rem CLI mode (default):
rem   run_playwright_tests.bat [PAGE_SELECTION]
rem   PAGE_SELECTION is "all" (default) or a comma-separated list of page
rem   names defined in tests\test_config.py, e.g. "home,contact".
rem
rem GUI mode:
rem   run_playwright_tests.bat --gui
rem   Opens a checkbox dialog (tests\gui_page_selector.py) to pick pages.
rem
rem The site under test, its pages, base URL, and authentication are all
rem defined in tests\test_config.py, so this script can be reused for
rem other sites by editing that config file only.

set "ROOT_DIR=%~dp0.."
set "TEST_DIR=%ROOT_DIR%\tests"
set "VENV_DIR=%TEST_DIR%\.venv"
set "HOST=127.0.0.1"
set "PORT=4000"
set "BASE_URL=http://%HOST%:%PORT%"
set "MODE=cli"
set "PAGE_SELECTION=all"

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--gui" (
  set "MODE=gui"
  shift
  goto parse_args
)
if /i "%~1"=="-h" goto show_usage
if /i "%~1"=="--help" goto show_usage
set "PAGE_SELECTION=%~1"
shift
goto parse_args

:show_usage
echo Usage: run_playwright_tests.bat [--gui] [PAGE_SELECTION]
echo.
echo   PAGE_SELECTION   "all" (default) or a comma-separated list of page
echo                    names from tests\test_config.py (e.g. "home,contact")
echo   --gui            Open a checkbox dialog to choose pages instead of
echo                    passing PAGE_SELECTION on the command line
echo   -h, --help       Show this help
exit /b 0

:args_done
cd /d "%ROOT_DIR%"

if not exist "%VENV_DIR%" (
  python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\python.exe" -m pip install --disable-pip-version-check --quiet -r "%TEST_DIR%\requirements.txt"
call "%VENV_DIR%\Scripts\python.exe" -m playwright install chromium

if /i "%MODE%"=="gui" (
  for /f "usebackq delims=" %%P in (`"%VENV_DIR%\Scripts\python.exe" "%TEST_DIR%\gui_page_selector.py"`) do set "PAGE_SELECTION=%%P"
  if "!PAGE_SELECTION!"=="" (
    echo No pages selected. Aborting.
    exit /b 1
  )
  echo Selected pages: !PAGE_SELECTION!
)

start "arbyte-jekyll-server" /min cmd /c "bundle exec jekyll serve --host %HOST% --port %PORT% --no-watch > "%TEST_DIR%\jekyll-server.log" 2>&1"

set "READY="
for /l %%i in (1,1,30) do (
  curl --silent --fail "%BASE_URL%/index.html" >nul 2>&1
  if not errorlevel 1 (
    set "READY=1"
    goto server_ready
  )
  timeout /t 1 /nobreak >nul
)

:server_ready
if not defined READY (
  echo Jekyll server did not start. See %TEST_DIR%\jekyll-server.log
  taskkill /FI "WINDOWTITLE eq arbyte-jekyll-server*" /T /F >nul 2>&1
  exit /b 1
)

set "PAGE_SELECTION=%PAGE_SELECTION%"
"%VENV_DIR%\Scripts\python.exe" -m pytest "%TEST_DIR%\test_site_pages.py" -v
set "EXITCODE=%ERRORLEVEL%"

rem Best effort: stop the background Jekyll server started above.
taskkill /FI "WINDOWTITLE eq arbyte-jekyll-server*" /T /F >nul 2>&1

exit /b %EXITCODE%
