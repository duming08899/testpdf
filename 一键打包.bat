@echo off
chcp 65001 >nul
title PDF图片提取工具 - 一键打包脚本

echo ========================================
echo   PDF图片提取工具 - 打包成 EXE
echo ========================================
echo.

:: 检查是否安装了 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.7+
    echo 下载地址: https://www.python.org/downloads/windows/
    echo.
    pause
    exit /b 1
)

echo [1/4] 正在安装打包工具 PyInstaller...
pip install pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [错误] PyInstaller 安装失败，请检查网络连接
    pause
    exit /b 1
)
echo PyInstaller 安装完成！

echo.
echo [2/4] 正在检查脚本依赖...
pip install pymupdf pillow >nul 2>&1
echo 依赖安装完成！

echo.
echo [3/4] 正在打包成 EXE，稍等片刻...
echo （首次打包会慢一些，请耐心等待）

:: 使用 PyInstaller 打包
:: --onefile: 打包成单个 exe
:: --console: 保留控制台窗口（需要显示进度）
:: --name: 指定exe名称
:: --hidden-import: 隐藏导入的模块（防止打包遗漏）
pyinstaller --onefile --console ^
    --name "PDF图片提取工具" ^
    --hidden-import pymupdf ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    pdf_image_extractor.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    echo 请检查是否有杀毒软件拦截，或尝试以管理员身份运行
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] 打包完成！

:: 把生成的 exe 移动到当前目录
if exist "dist\PDF图片提取工具.exe" (
    move /y "dist\PDF图片提取工具.exe" ".\" >nul
    echo EXE 文件已生成: PDF图片提取工具.exe
)

:: 清理临时文件
rmdir /s /q build >nul 2>&1
rmdir /s /q dist >nul 2>&1
del /q "PDF图片提取工具.spec" >nul 2>&1
echo 临时文件已清理

echo.
echo ========================================
echo   打包成功！
echo ========================================
echo.
echo 使用方法:
echo   1. 打开命令行，进入 exe 所在目录
echo   2. 提取图片: PDF图片提取工具.exe 你的文件.pdf --extract-only
echo   3. 提取+压缩: PDF图片提取工具.exe 你的文件.pdf -q 85
echo   4. 查看帮助: PDF图片提取工具.exe --help
echo.
echo 更多用法请参考 使用说明.md
echo.
pause
