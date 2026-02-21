$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$Cwd = Get-Location

Write-Host "REPO_ROOT: $RepoRoot"
Write-Host "SCRIPT_PATH: $ScriptPath"
Write-Host "CURRENT_WORKING_DIRECTORY: $Cwd"
function Get-HeaderValue($headers, $name) {
  if (-not $headers) { return $null }
  try { return $headers[$name] } catch { return $null }
}
# scripts/prod_smoke_test.ps1
$ErrorActionPreference = "Stop"

$Base = "https://mphai-portal-production.up.railway.app"
$Base = $Base.Trim().TrimEnd('/')

$HealthUrl = "$Base/health"
$LoginUrl  = "$Base/api/auth/login"

Write-Host "=== HEALTH CHECK ==="
Write-Host "HealthUrl: $HealthUrl"
$healthResp = Invoke-WebRequest -UseBasicParsing -Uri $HealthUrl -Method Get
$healthResp.Content | Write-Host

Write-Host "`n=== LOGIN CHECK ==="
Write-Host "LoginUrl: $LoginUrl"

# Validate URL parse BEFORE calling
try {
  [void][Uri]$LoginUrl
} catch {
  throw "LoginUrl is not a valid URI: <$LoginUrl>"
}


if (-not $env:DEMO_PASSWORD -or [string]::IsNullOrWhiteSpace($env:DEMO_PASSWORD)) {
  throw "SMOKE_FAIL:missing_demo_password"
}

function Invoke-Capture($method, $url, $headers, $bodyJson) {
  try {
    if ($null -ne $bodyJson -and $bodyJson -isnot [string]) {
      $bodyJson = $bodyJson | ConvertTo-Json -Compress
    }
    $resp = Invoke-WebRequest -UseBasicParsing -Method $method -Uri $url -Headers $headers -ContentType "application/json" -Body $bodyJson
    return [pscustomobject]@{
      Status           = [int]$resp.StatusCode
      RequestId        = (Get-HeaderValue $resp.Headers 'X-Request-Id')
      RailwayRequestId = (Get-HeaderValue $resp.Headers 'X-Railway-Request-Id')
      Date             = (Get-HeaderValue $resp.Headers 'Date')
      ContentType      = (Get-HeaderValue $resp.Headers 'Content-Type')
      Server           = (Get-HeaderValue $resp.Headers 'Server')
      Body             = $resp.Content
    }
  } catch {
    $r = $_.Exception.Response
    $respHeaders = $null
    if ($r) { $respHeaders = $r.Headers }
    $body = $null
    if ($r) {
      $sr = New-Object System.IO.StreamReader($r.GetResponseStream())
      $body = $sr.ReadToEnd()
    }
    return [pscustomobject]@{
      Status           = if ($r) { [int]$r.StatusCode } else { $null }
      RequestId        = (Get-HeaderValue $respHeaders 'X-Request-Id')
      RailwayRequestId = (Get-HeaderValue $respHeaders 'X-Railway-Request-Id')
      Date             = (Get-HeaderValue $respHeaders 'Date')
      ContentType      = (Get-HeaderValue $respHeaders 'Content-Type')
      Server           = (Get-HeaderValue $respHeaders 'Server')
      Body             = $body
    }
  }
}

# LOGIN
$loginBody = @{ password = [string]$env:DEMO_PASSWORD } | ConvertTo-Json -Compress

$login = Invoke-Capture "POST" $LoginUrl @{} $loginBody
Write-Host "LOGIN_STATUS: $($login.Status)"
Write-Host "LOGIN_X_REQUEST_ID: $($login.RequestId)"
Write-Host "LOGIN_RAILWAY_REQUEST_ID: $($login.RailwayRequestId)"
Write-Host "LOGIN_DATE: $($login.Date)"
Write-Host "LOGIN_BODY: $($login.Body)"

try {
    $token = ($login.Body | ConvertFrom-Json).access_token
} catch { throw "SMOKE_FAIL:token_parse" }
if (-not $token) { throw "SMOKE_FAIL:token_missing" }

if ($login.Status -ne 200) { throw "SMOKE_FAIL:login_status" }


# GENERATE
Write-Host "`n=== GENERATE CHECK ==="

$session_id = "prod-smoke-$([Guid]::NewGuid().ToString('N').Substring(0,8))"
$genBody = @{ session_id = $session_id; raw_text = "Smoke test: verify AiDoc fallback + per-session PDF generation." } | ConvertTo-Json -Compress

try {
  $gen = Invoke-Capture "POST" "$Base/api/proposals/generate" @{ Authorization = "Bearer $token" } $genBody
  if ($gen.Status -ne 200) { throw "SMOKE_FAIL:generate_status_$($gen.Status) $($gen.Body)" }
  $generateJson = $gen.Body | ConvertFrom-Json
  if ($generateJson.session_id -and $generateJson.session_id -ne $session_id) { throw "SMOKE_FAIL:session_id_mismatch" }
} catch { throw "SMOKE_FAIL:generate_exception" }

$tmpDir = Join-Path $RepoRoot "tmp"
if (-not (Test-Path $tmpDir)) { New-Item -ItemType Directory -Path $tmpDir | Out-Null }


$outFile = Join-Path $tmpDir "$session_id.pdf"
Write-Host "OUTFILE: $outFile"
try {
  $downloadResponse = Invoke-WebRequest `
    -Method GET `
    -MaximumRedirection 0 `
    -Uri "$Base/api/proposals/download/$session_id" `
    -Headers @{ Authorization = "Bearer $token" } `
    -OutFile $outFile
} catch { throw "SMOKE_FAIL:download_exception" }

$downloadSize = 0
if (Test-Path $outFile) {
  $downloadSize = (Get-Item $outFile).Length
}
Write-Host "DOWNLOAD_SIZE_BYTES: $downloadSize"
if ($downloadSize -le 0) { throw "SMOKE_FAIL:download_size" }
Write-Host "SMOKE_OK"
