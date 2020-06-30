@ECHO OFF
CMDOW @ /ren "Dynamic Wallpaper" /mov 1174 452 /siz 217 120 /top
CD "C:\Users\Dave\DEVENV\Python\PythonUtilityProjects"
@ECHO Dynamic Wallpaper is initiating...
TIMEOUT 3
python wallpaper.py
@ECHO Dynamic Wallpaper closing...
TIMEOUT 3
EXIT