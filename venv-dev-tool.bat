@echo off

setlocal
:PROMPT
SET /P PROMPT=Do you want to download the latest webdrivers (y/n)? 
IF /I "%PROMPT%" NEQ "y" GOTO END

echo|set /p="Getting drivers... "
cmd /k "cd /d venv\Scripts & activate & cd /d ..\..\scripts & python driver_fetcher.py & exit"
echo Done. & echo.

:END
endlocal

setlocal
:PROMPT
SET /P PROMPT=Do you want to enter new account credentials (y/n)? 
IF /I "%PROMPT%" NEQ "y" GOTO END

echo.
cmd /k "cd /d venv\Scripts & activate & cd /d ..\..\scripts & python credential_generator.py & exit"
echo Done. & echo.

:END
endlocal

setlocal
:PROMPT
SET /P PROMPT=Do you want to launch the auto-messaging script (y/n)? 
IF /I "%PROMPT%" NEQ "y" GOTO END

echo. & echo Waiting for social.py to work from any account for this to be implemented.
echo.

:END
endlocal

echo. & echo Virtual environment activated.
cmd /k venv\Scripts\activate