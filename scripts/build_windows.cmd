@echo off
setlocal enabledelayedexpansion

set "TARGET=gui"
set "CLEAN=0"
set "RECREATE_VENV=0"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="gui" (
    set "TARGET=gui"
    shift
    goto parse_args
)
if /I "%~1"=="cli" (
    set "TARGET=cli"
    shift
    goto parse_args
)
if /I "%~1"=="both" (
    set "TARGET=both"
    shift
    goto parse_args
)
if /I "%~1"=="clean" (
    set "CLEAN=1"
    shift
    goto parse_args
)
if /I "%~1"=="venvclean" (
    set "RECREATE_VENV=1"
    shift
    goto parse_args
)
if /I "%~1"=="--clean" (
    set "CLEAN=1"
    shift
    goto parse_args
)
if /I "%~1"=="/clean" (
    set "CLEAN=1"
    shift
    goto parse_args
)
if /I "%~1"=="--venvclean" (
    set "RECREATE_VENV=1"
    shift
    goto parse_args
)

echo Unknown argument: %~1
echo Usage: scripts\build_windows.cmd [gui^|cli^|both] [clean] [venvclean]
exit /b 2

:args_done
pushd "%~dp0" || exit /b 1
if not exist pyproject.toml (
    if exist ..\pyproject.toml (
        cd ..
    ) else (
        echo Could not find pyproject.toml from "%~dp0" or its parent.
        popd
        exit /b 1
    )
)
set "PROJECT_ROOT=%CD%"
echo Project root: "%PROJECT_ROOT%"

where uv >nul 2>nul
if errorlevel 1 (
    echo uv not found. Install uv and make sure it is available on PATH.
    popd
    exit /b 1
)

if "%CLEAN%"=="1" (
    if exist "%PROJECT_ROOT%\build" rmdir /s /q "%PROJECT_ROOT%\build"
    if exist "%PROJECT_ROOT%\dist" rmdir /s /q "%PROJECT_ROOT%\dist"
)

if "%RECREATE_VENV%"=="1" (
    if exist "%PROJECT_ROOT%\.venv" rmdir /s /q "%PROJECT_ROOT%\.venv"
)

call :prepare_env
if not errorlevel 1 goto env_ready

echo Existing virtual environment looks incomplete. Recreating .venv and retrying...
if exist "%PROJECT_ROOT%\.venv" rmdir /s /q "%PROJECT_ROOT%\.venv"
call :prepare_env
if errorlevel 1 goto failed

:env_ready

if /I "%TARGET%"=="gui" (
    call :build_gui
    if errorlevel 1 goto failed
) else if /I "%TARGET%"=="both" (
    call :build_gui
    if errorlevel 1 goto failed
)

if /I "%TARGET%"=="cli" (
    call :build_cli
    if errorlevel 1 goto failed
) else if /I "%TARGET%"=="both" (
    call :build_cli
    if errorlevel 1 goto failed
)

echo Build output:
if exist dist (
    dir /b dist\*.exe 2>nul
)

popd
exit /b 0

:build_gui
uv --project "%PROJECT_ROOT%" run pyinstaller -F -n pdf-tools-gui --clean --noconfirm --collect-all fitz --collect-all numpy --collect-all lxml --icon assets\icon\app.ico --windowed pdf_tools\gui_main.py
exit /b %errorlevel%

:build_cli
uv --project "%PROJECT_ROOT%" run pyinstaller -F -n pdf-tools --clean --noconfirm --collect-all fitz --collect-all numpy --collect-all lxml --icon assets\icon\app.ico pdf_tools\__main__.py
exit /b %errorlevel%

:prepare_env
if not exist "%PROJECT_ROOT%\.venv" (
    uv venv "%PROJECT_ROOT%\.venv"
    if errorlevel 1 exit /b 1
)

uv --project "%PROJECT_ROOT%" sync
if errorlevel 1 exit /b 1

uv pip install --python "%PROJECT_ROOT%\.venv\Scripts\python.exe" pyinstaller
if errorlevel 1 exit /b 1

uv --project "%PROJECT_ROOT%" run python -c "import importlib.metadata as m; assert m.version('numpy'); assert m.version('PyMuPDF')"
exit /b %errorlevel%

:failed
set "EXIT_CODE=%errorlevel%"
popd
exit /b %EXIT_CODE%
