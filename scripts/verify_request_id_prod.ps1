# Verify Request ID propagation in production (Railway)
# - Ensures X-Request-Id is always present in responses (success and error)
# - Echoes inbound X-Request-Id if provided, else generates UUIDv4
# - No log lines in Railway should show request_id: null
# Usage: powershell -ExecutionPolicy Bypass -File scripts\verify_request_id_prod.ps1

$BaseUrl = "https://mphai-portal-production.up.railway.app"

function Print-Pass($msg) { Write-Host "PASS: $msg" -ForegroundColor Green }
function Print-Fail($msg) { Write-Host "FAIL: $msg" -ForegroundColor Red }
function Assert($cond, $msg) { if (-not $cond) { Print-Fail $msg; exit 1 } else { Print-Pass $msg } }

# Helper to extract header (case-insensitive)
function Get-Header($headers, $name) {
  foreach ($k in $headers.Keys) { if ($k -ieq $name) { return $headers[$k] } }
  return $null
}

# 1A: GET /health with X-Request-Id
$customRid = "rid-prod-123"
try {
  $respA = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/health" -Headers @{"X-Request-Id"=$customRid} -Method GET
} catch { $respA = $_.Exception.Response }
$ridA = Get-Header $respA.Headers "X-Request-Id"
Assert ($respA.StatusCode -eq 200) "/health with X-Request-Id returns 200"
Assert ($ridA) "/health with X-Request-Id echoes header"
Assert ($ridA -eq $customRid) "/health X-Request-Id matches sent value"

# 1B: GET /health without X-Request-Id
try {
  $respB = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/health" -Method GET
} catch { $respB = $_.Exception.Response }
$ridB = Get-Header $respB.Headers "X-Request-Id"
Assert ($respB.StatusCode -eq 200) "/health without X-Request-Id returns 200"
Assert ($ridB) "/health without X-Request-Id returns X-Request-Id"
$uuidRegex = '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
Assert ($ridB -match $uuidRegex) "/health X-Request-Id is UUIDv4"

# 2: POST /api/proposals/generate with minimal stub
$genUrl = "$BaseUrl/api/proposals/generate"
$genBody = '{}' # minimal JSON
try {
  $respGen = Invoke-WebRequest -UseBasicParsing -Uri $genUrl -Method POST -ContentType "application/json" -Body $genBody -Headers @{"X-Request-Id"="rid-prod-gen"}
} catch { $respGen = $_.Exception.Response }
$ridGen = Get-Header $respGen.Headers "X-Request-Id"
Assert ($ridGen) "/api/proposals/generate returns X-Request-Id on error or success"
Write-Host "StatusCode: $($respGen.StatusCode)"
Write-Host "X-Request-Id: $ridGen"
Write-Host "All request ID propagation checks PASSED."
exit 0
