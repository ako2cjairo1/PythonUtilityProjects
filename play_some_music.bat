@ECHO OFF
CD "C:\Users\Dave\DEVENV\Python\PythonUtilityProjects"
CMDOW @ /ren \"Music Player\" /mov 601 -35 /siz 790 110
@ECHO Music Player is initiating...
python musicplayer.py random
@ECHO Music Player closing...
TIMEOUT 2
EXIT