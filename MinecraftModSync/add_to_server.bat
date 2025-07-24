@ECHO OFF
py "%AppData%\MinecraftModSync\add_to_server.py" "%~1"
COPY "%~1" "%USERPROFILE%\mcserv\mods\"