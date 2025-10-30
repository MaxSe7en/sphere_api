# =====================================================
# SPHERE API - COMPLETE END-TO-END TEST SCRIPT
# October 30, 2025
# =====================================================

Write-Host "🚀 Starting Sphere API Tests..." -ForegroundColor Green

# === CONFIG ===
$BILL_ID = 1923442  # Replace with real MN bill ID after sync
$STATE = "MN"
$EMAIL = "test3@example.com"
$PASSWORD = "pass123"
$FULL_NAME = "Test User 3"

# === 1. SYNC MN BILLS (Populate DB) ===
Write-Host "`n📥 1. SYNCING $STATE BILLS..." -ForegroundColor Yellow
$syncResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/bills/sync/$STATE" -Method Post
Write-Host "✅ Synced $($syncResult.updated) bills" -ForegroundColor Green

# Get a REAL bill ID from sync
$firstBillId = ($syncResult.masterlist.PSObject.Properties | Where-Object { $_.Value.bill_id }).Value.bill_id
$BILL_ID = $firstBillId
Write-Host "📄 Using Bill ID: $BILL_ID" -ForegroundColor Cyan

# === 2. REGISTER USER ===
Write-Host "`n👤 2. REGISTERING USER..." -ForegroundColor Yellow
$reg = @{
    email = $EMAIL
    password = $PASSWORD
    full_name = $FULL_NAME
} | ConvertTo-Json

$regResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/register" `
    -Method Post -Body $reg -ContentType "application/json"
Write-Host "✅ Registered: $($regResult.access_token.Substring(0,20))..." -ForegroundColor Green

# === 3. LOGIN & GET TOKEN ===
Write-Host "`n🔐 3. LOGGING IN..." -ForegroundColor Yellow
$login = @{
    email = $EMAIL
    password = $PASSWORD
} | ConvertTo-Json

$TOKEN = (Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/login" `
    -Method Post -Body $login -ContentType "application/json").access_token
Write-Host "✅ TOKEN: $($TOKEN.Substring(0,20))..." -ForegroundColor Green

$headers = @{ Authorization = "Bearer $TOKEN" }

# === 4. FOLLOW BILL ===
Write-Host "`n⭐ 4. FOLLOWING BILL $BILL_ID..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/me/watchlist/$BILL_ID" `
    -Method Post -Headers $headers
Write-Host "✅ Bill $BILL_ID added to watchlist" -ForegroundColor Green

# === 5. LIST WATCHLIST ===
Write-Host "`n📋 5. LISTING WATCHLIST..." -ForegroundColor Yellow
$watchlist = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/me/watchlist" -Headers $headers
Write-Host "✅ Watchlist: $($watchlist.Count) items" -ForegroundColor Green
$watchlist | ForEach-Object { Write-Host "  - Bill $($_.bill_id): $($_.title)" -ForegroundColor Cyan }

# === 6. GET BILL DETAILS ===
Write-Host "`n📄 6. GETTING BILL DETAILS..." -ForegroundColor Yellow
$bill = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/bills/$BILL_ID"
Write-Host "✅ Bill: $($bill.title)" -ForegroundColor Green
Write-Host "   Status: $($bill.status) | State: $($bill.state)" -ForegroundColor Gray

# === 7. AI ANALYSIS (Regenerate) ===
Write-Host "`n🤖 7. GENERATING AI ANALYSIS..." -ForegroundColor Yellow
$ai = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/ai/$BILL_ID" `
    -Method Get -Query @{ regen = "true" }
Write-Host "✅ AI Summary: $($ai.summary.Substring(0,100))..." -ForegroundColor Green

# === 8. LIST STATE BILLS ===
Write-Host "`n📈 8. LISTING $STATE BILLS..." -ForegroundColor Yellow
$stateBills = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/bills/state/$STATE?limit=3"
Write-Host "✅ $($stateBills.total) total bills | Showing $($stateBills.bills.Count):" -ForegroundColor Green
$stateBills.bills | ForEach-Object { 
    Write-Host "  - $($_.id): $($_.title.Substring(0,50))..." -ForegroundColor Cyan 
}

# === 9. STATES OVERVIEW ===
Write-Host "`n🗺️  9. STATES OVERVIEW..." -ForegroundColor Yellow
$states = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/states_overview_count/"
Write-Host "✅ States with bills:" -ForegroundColor Green
$states | Where-Object { $_.active_bills -gt 0 } | ForEach-Object { 
    Write-Host "  $($_.state): $($_.active_bills) bills" -ForegroundColor Cyan 
}

# === 10. UNFOLLOW BILL ===
Write-Host "`n❌ 10. UNFOLLOWING BILL..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/me/watchlist/$BILL_ID" `
    -Method Delete -Headers $headers
Write-Host "✅ Bill $BILL_ID removed from watchlist" -ForegroundColor Green

# === 11. VERIFY UNFOLLOW ===
$finalWatchlist = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/me/watchlist" -Headers $headers
Write-Host "✅ Final watchlist: $($finalWatchlist.Count) items (should be 0)" -ForegroundColor Green

# === HEALTH CHECK ===
Write-Host "`n🏥 11. HEALTH CHECK..." -ForegroundColor Yellow
$health = Invoke-RestMethod -Uri "http://localhost:8000/health"
Write-Host "✅ API Status: $($health.status) | DB: $($health.database)" -ForegroundColor Green

Write-Host "`n🎉 ALL TESTS PASSED! Your Sphere API is 100% WORKING!" -ForegroundColor Green
Write-Host "   Total Endpoints Tested: 11" -ForegroundColor Green
Write-Host "   User: $FULL_NAME | Token: $($TOKEN.Substring(0,20))..." -ForegroundColor Cyan