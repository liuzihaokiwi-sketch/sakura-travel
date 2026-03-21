@echo off
title Travel-AI Dev Server
echo ========================================
echo   Travel-AI 开发环境一键启动
echo ========================================
echo.

:: 检查端口是否被占用，如果是就先杀掉
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTEN" 2^>nul') do (
    echo [Backend] 端口 8000 已被占用，正在清理 PID %%a ...
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTEN" 2^>nul') do (
    echo [Frontend] 端口 3000 已被占用，正在清理 PID %%a ...
    taskkill /PID %%a /F >nul 2>&1
)

timeout /t 2 /nobreak >nul

:: 启动后端
echo [1/2] 启动后端 FastAPI (port 8000) ...
start "Backend-FastAPI" cmd /k "cd /d d:\projects\projects\travel-ai && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

:: 启动前端
echo [2/2] 启动前端 Next.js (port 3000) ...
start "Frontend-NextJS" cmd /k "cd /d d:\projects\projects\travel-ai\web && npm run dev"

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   全部启动完成！
echo   前端: http://localhost:3000
echo   后端: http://localhost:8000
echo   管理: http://localhost:3000/admin
echo   密码: admin123
echo ========================================
echo.
echo 关闭此窗口不会影响服务运行。
echo 要停止服务请关闭 Backend-FastAPI 和 Frontend-NextJS 窗口。
pause
