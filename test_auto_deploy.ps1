# ============================================
# Script para Probar Auto-Deploy
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Auto-Deploy - BioStar Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
$currentDir = Get-Location
Write-Host "📁 Directorio actual: $currentDir" -ForegroundColor Yellow

# Verificar conexión con GitHub
Write-Host ""
Write-Host "🔍 Verificando conexión con GitHub..." -ForegroundColor Yellow
git remote -v

# Verificar estado del repositorio
Write-Host ""
Write-Host "🔍 Estado del repositorio:" -ForegroundColor Yellow
git status

# Verificar rama actual
Write-Host ""
Write-Host "🌿 Rama actual:" -ForegroundColor Yellow
git branch --show-current

# Verificar últimos commits
Write-Host ""
Write-Host "📝 Últimos 5 commits:" -ForegroundColor Yellow
git log --oneline -5

# Preguntar si quiere hacer un test commit
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ¿Quieres hacer un test commit?" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Esto creará un commit de prueba y lo enviará a GitHub" -ForegroundColor Yellow
Write-Host "para activar el auto-deploy." -ForegroundColor Yellow
Write-Host ""
$response = Read-Host "¿Continuar? (S/N)"

if ($response -eq "S" -or $response -eq "s") {
    Write-Host ""
    Write-Host "✅ Creando commit de prueba..." -ForegroundColor Green
    
    # Crear archivo de prueba
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $testContent = "# Test Auto-Deploy`n`nÚltima prueba: $timestamp`n"
    Set-Content -Path "TEST_AUTO_DEPLOY.txt" -Value $testContent
    
    # Agregar al stage
    git add TEST_AUTO_DEPLOY.txt
    git add CONFIGURAR_AUTO_DEPLOY.md
    git add test_auto_deploy.ps1
    
    # Commit
    git commit -m "test: Probar sistema de auto-deploy desde Windows"
    
    # Mostrar confirmación
    Write-Host ""
    Write-Host "📦 Commit creado exitosamente" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  ¿Hacer PUSH a GitHub?" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⚠️  IMPORTANTE: Asegúrate de haber configurado los GitHub Secrets:" -ForegroundColor Red
    Write-Host "   - SSH_PRIVATE_KEY" -ForegroundColor Yellow
    Write-Host "   - SERVER_HOST" -ForegroundColor Yellow
    Write-Host "   - SERVER_USER" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Si NO los has configurado, el deploy FALLARÁ." -ForegroundColor Red
    Write-Host ""
    $pushResponse = Read-Host "¿Hacer push a origin/main? (S/N)"
    
    if ($pushResponse -eq "S" -or $pushResponse -eq "s") {
        Write-Host ""
        Write-Host "🚀 Haciendo push a GitHub..." -ForegroundColor Green
        git push origin main
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ✅ PUSH EXITOSO" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Monitorea el progreso en:" -ForegroundColor Yellow
        Write-Host "   https://github.com/ezraidenn/DEBUGBI0/actions" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "⏱️  El deploy tomará aproximadamente 2-3 minutos" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "🌐 Una vez completado, verifica en:" -ForegroundColor Yellow
        Write-Host "   http://10.0.2.64" -ForegroundColor Cyan
        Write-Host ""
        
        # Preguntar si quiere abrir el navegador
        $openBrowser = Read-Host "¿Abrir GitHub Actions en el navegador? (S/N)"
        if ($openBrowser -eq "S" -or $openBrowser -eq "s") {
            Start-Process "https://github.com/ezraidenn/DEBUGBI0/actions"
        }
    }
    else {
        Write-Host ""
        Write-Host "❌ Push cancelado" -ForegroundColor Red
        Write-Host ""
        Write-Host "Para hacer push manualmente:" -ForegroundColor Yellow
        Write-Host "   git push origin main" -ForegroundColor Cyan
    }
}
else {
    Write-Host ""
    Write-Host "❌ Operación cancelada" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Comandos Útiles" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ver estado:" -ForegroundColor Yellow
Write-Host "   git status" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ver logs:" -ForegroundColor Yellow
Write-Host "   git log --oneline -10" -ForegroundColor Cyan
Write-Host ""
Write-Host "Hacer push manual:" -ForegroundColor Yellow
Write-Host "   git push origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ver GitHub Actions:" -ForegroundColor Yellow
Write-Host "   https://github.com/ezraidenn/DEBUGBI0/actions" -ForegroundColor Cyan
Write-Host ""
