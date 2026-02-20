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
$Base = $Base.Trim()

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
  Write-Error "DEMO_PASSWORD environment variable is not set. Exiting."
  exit 1
}

function Invoke-Capture($method, $url, $headers, $bodyJson) {
  try {
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

if ($login.Status -ne 200) { throw "Login failed; stop." }

$loginJson = $login.Body | ConvertFrom-Json
$token = $loginJson.access_token

# GENERATE

$genBody = @{
  session_id = "prod-debug-1"
  raw_text = "Test proposal: paint walls, 2 coats, total 1200."
  document_type = "proposal"
} | ConvertTo-Json -Compress


$gen = Invoke-Capture "POST" "$Base/api/proposals/generate" @{ Authorization = "Bearer $token" } $genBody
Write-Host "GENERATE_STATUS: $($gen.Status)"
Write-Host "GENERATE_X_REQUEST_ID: $($gen.RequestId)"
Write-Host "GENERATE_RAILWAY_REQUEST_ID: $($gen.RailwayRequestId)"
Write-Host "GENERATE_DATE: $($gen.Date)"
Write-Host "GENERATE_BODY: $($gen.Body)"
