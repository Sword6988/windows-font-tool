@echo off
"C:\Users\Shibeng\AppData\Local\Programs\Python\Python314\python.exe" "%~dp0字体名称提取工具.py"
if %errorlevel% neq 0 (echo 运行出错，请确认已安装 Python 3.14 且包含 tkinter & pause)
