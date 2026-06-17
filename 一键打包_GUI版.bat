@echo off
chcp 65001 >nul
title PDF图片提取工具 - 打包 GUI 版

echo ========================================
echo   PDF图片提取工具 - 打包 GUI 版
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python
    pause
    exit /b 1
)

echo [1/3] 安装 PyInstaller...
pip install pyinstaller pymupdf pillow >nul 2>&1

echo.
echo [2/3] 正在打包 GUI 版...
echo （打包过程可能需要 1-2 分钟，请耐心等待）

pyinstaller --onefile --windowed ^
    --name "PDF图片提取工具" ^
    --hidden-import pymupdf ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    pdf_image_extractor_gui.py

if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo [3/3] 清理临时文件...

if exist "dist\PDF图片提取工具.exe" (
    move /y "dist\PDF图片提取工具.exe" ".\" >nul
)

rmdir /s /q build >nul 2>&1
rmdir /s /q dist >nul 2>&1
del /q "PDF图片提取工具.spec" >nul 2>&1

echo.
echo ========================================
echo   打包成功！
echo ========================================
echo.
echo 已生成: PDF图片提取工具.exe
echo 双击即可运行，无需命令行
echo.
pause
