$root = Split-Path -Parent $PSScriptRoot
$destination = Join-Path $root 'bar-association-hall.zip'
Compress-Archive -Path (Join-Path $root 'bar-association-hall') -DestinationPath $destination -Force
Write-Host "Created: $destination"
