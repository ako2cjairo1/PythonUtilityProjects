@ECHO OFF
SET option=%1
SET shuffle=%2
SET mode=%3
SET title=%4
SET artist=%5
SET genre=%6

CD C:\Users\Dave\DEVENV\Python\PythonUtilityProjects
@ECHO     Music Player is initiating...
python musicplayer.py --option %option% --shuffle %shuffle% --mode %mode% --title %title% --artist %artist% --genre %genre%
@ECHO Music Player closing...
TIMEOUT 1
EXIT