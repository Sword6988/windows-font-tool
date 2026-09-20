@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "%~dp0app.ico" "C:\Users\Shibeng\AppData\Local\Programs\Python\Python314\python.exe" "%~dp0make_icon.py"
"C:\Users\Shibeng\AppData\Local\Programs\Python\Python314\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name "字体名称提取工具" --icon "%~dp0app.ico" --add-data "%~dp0app.ico;." --distpath "%~dp0dist" --workpath "%~dp0build" --specpath "%~dp0" "%~dp0字体名称提取工具.py"
echo.
echo 打包完成，exe 位于 dist 文件夹（已含自定义图标）。
pause
