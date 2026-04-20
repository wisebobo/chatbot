# Quick Start Script for Chatbot Frontend Testing
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Chatbot 测试页面快速启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
Write-Host "检查后端服务状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -Method Get -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        Write-Host " 后端服务正在运行" -ForegroundColor Green
    }
} catch {
    Write-Host " 后端服务未运行" -ForegroundColor Red
    Write-Host ""
    $answer = Read-Host "是否要启动后端服务？(y/n)"
    if ($answer -eq 'y' -or $answer -eq 'Y') {
        Write-Host "正在启动后端服务..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; cd ..; python main.py"
        Write-Host "等待后端服务启动..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

Write-Host ""
Write-Host "打开前端测试页面..." -ForegroundColor Green
Start-Process "file:///$PWD/index.html"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  使用说明：" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. 在浏览器中可以使用登录功能（需配置LDAP）" -ForegroundColor White
Write-Host "2. 或点击'跳过登录'直接体验聊天功能" -ForegroundColor White
Write-Host "3. 输入消息并按 Enter 发送" -ForegroundColor White
Write-Host "4. 查看右下角的 Session ID" -ForegroundColor White
Write-Host ""
Write-Host "后端 API 地址: http://localhost:8000" -ForegroundColor Cyan
Write-Host "前端页面路径: $PWD\index.html" -ForegroundColor Cyan
Write-Host ""
