@echo off
echo 正在安装视频生成器GUI应用...
echo.

REM 检查Python版本
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到pip，请重新安装Python
    pause
    exit /b 1
)

echo 正在安装依赖包...
pip install -r requirements.txt

if errorlevel 1 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

echo.
echo 正在创建启动脚本...
echo @echo off > start_gui.bat
echo cd /d "%~dp0" >> start_gui.bat
echo python src/main.py >> start_gui.bat
echo pause >> start_gui.bat

echo.
echo 正在创建桌面快捷方式...
set SCRIPT="%TEMP%\create_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\视频生成器.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%CD%\start_gui.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%CD%" >> %SCRIPT%
echo oLink.IconLocation = "%SystemRoot%\System32\shell32.dll,277" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript //nologo %SCRIPT%
del %SCRIPT%

echo.
echo 安装完成！
echo.
echo 使用方法：
echo 1. 双击桌面上的"视频生成器"快捷方式
echo 2. 或直接运行 scripts/start_gui.bat
echo 3. 或运行 python src/main.py
echo.
echo 首次运行请先在"配置管理"标签页中配置相关API信息
echo.
pause