$BASE = "https://mphai-portal-production.up.railway.app"


# --- 404 Test ---
try {
    $headers = @{ "x-request-id" = "smoke-404-test" }
    $resp = Invoke-WebRequest "$BASE/does-not-exist" -Headers $headers -UseBasicParsing -ErrorAction Stop
    $status = $resp.StatusCode
    $body = $resp.Content
    $xreq = $resp.Headers["x-request-id"]
} catch {
    $resp = $_.Exception.Response
    $status = $resp.StatusCode.value__
    $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
    $body = $reader.ReadToEnd()
    $xreq = $resp.Headers["x-request-id"]
}
Write-Host "status=$status"
Write-Host "x-request-id=$xreq"
Write-Host "body=$body"
Write-Host ""


# --- Login Test ---
try {
    $loginBody = '{"password": "demo2026"}'
    $resp = Invoke-WebRequest "$BASE/api/auth/login" -Method POST -Body $loginBody -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $status = $resp.StatusCode
    $body = $resp.Content
} catch {
    $resp = $_.Exception.Response
    $status = $resp.StatusCode.value__
    $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
    $body = $reader.ReadToEnd()
}
Write-Host "status=$status"
Write-Host "body=$body"
Write-Host ""


# --- Protected Endpoint Without Auth ---
try {
    $resp = Invoke-WebRequest "$BASE/api/proposals/generate" -Method POST -Body '{}' -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $status = $resp.StatusCode
    $body = $resp.Content
} catch {
    $resp = $_.Exception.Response
    $status = $resp.StatusCode.value__
    $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
    $body = $reader.ReadToEnd()
}
Write-Host "status=$status"
Write-Host "body=$body"
