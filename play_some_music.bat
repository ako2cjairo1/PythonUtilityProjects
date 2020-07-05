@ECHO OFF
CD "C:\Users\Dave\DEVENV\Python\PythonUtilityProjects"
@ECHO Music Player is initiating...
python musicplayer.py --option "random" --shuffle True --compactmode True
@ECHO Music Player closing...
TIMEOUT 3
EXIT