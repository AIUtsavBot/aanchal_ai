# Test script to verify frontend-backend connection
# Run this in PowerShell to check everything

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Aanchal AI - Connection Test" -ForegroundColor Cyan  
Write-Host "========================================`n" -ForegroundColor Cyan

# Test 1: Check if backend is running
Write-Host "[Test 1] Checking backend on port 8000..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ Backend is responding (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend NOT responding on port 8000" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Check health endpoint
Write-Host "`n[Test 2] Testing /health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ Health endpoint OK" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Health endpoint failed" -ForegroundColor Red
}

# Test 3: Check CORS headers
Write-Host "`n[Test 3] Checking CORS configuration..." -ForegroundColor Yellow
try {
    $headers = @{ "Origin" = "http://localhost:5173" }
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method OPTIONS -Headers $headers -TimeoutSec 5 -UseBasicParsing
    $corsHeader = $response.Headers["Access-Control-Allow-Origin"]
   if ($corsHeader) {
        Write-Host "✅ CORS header present: $corsHeader" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No CORS header found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ CORS check failed" -ForegroundColor Red
}

# Test 4: Check if frontend is running
Write-Host "`n[Test 4] Checking frontend on port 5173..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173/" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ Frontend is responding (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Frontend NOT responding on port 5173" -ForegroundColor Red
    Write-Host "   Make sure 'npm run dev' is running" -ForegroundColor Yellow
}

# Test 5: Check .env.local configuration
Write-Host "`n[Test 5] Verifying frontend .env.local..." -ForegroundColor Yellow
$envPath = "d:\SantanRaksha\frontend\.env.local"
if (Test-Path $envPath) {
    $content = Get-Content $envPath -Raw
    if ($content -match "VITE_API_URL=http://localhost:8000") {
        Write-Host "✅ VITE_API_URL correctly set to port 8000" -ForegroundColor Green
    } elseif ($content -match "VITE_API_URL=http://localhost:8001") {
        Write-Host "❌ WRONG PORT! VITE_API_URL is set to 8001" -ForegroundColor Red
        Write-Host "   Backend is on 8000, not 8001!" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  VITE_API_URL not found in .env.local" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ .env.local file not found" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Backend should be at: http://localhost:8000" -ForegroundColor White
Write-Host "2. Frontend should be at: http://localhost:5173" -ForegroundColor White
Write-Host "3. After fixing .env.local, RESTART frontend with Ctrl+C then 'npm run dev'" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan
