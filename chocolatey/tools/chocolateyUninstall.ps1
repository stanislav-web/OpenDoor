# chocolatey/tools/uninstall.ps1
$ErrorActionPreference = 'Stop'

$packageName = 'opendoor'

function Get-OpenDoorPython {
  $candidates = @(
    'C:\Python313\python.exe',
    'C:\Program Files\Python313\python.exe',
    'C:\Python312\python.exe',
    'C:\Program Files\Python312\python.exe'
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  $python = Get-Command python.exe -ErrorAction SilentlyContinue
  if ($python) {
    return $python.Source
  }

  return $null
}

$pythonExe = Get-OpenDoorPython

if ($pythonExe) {
  Write-Host "Uninstalling $packageName using Python: $pythonExe"
  & $pythonExe -m pip uninstall -y $packageName
} else {
  Write-Warning 'Python was not found. Skipping pip uninstall for opendoor.'
}