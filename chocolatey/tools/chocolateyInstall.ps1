# chocolatey/tools/install.ps1
$ErrorActionPreference = 'Stop'

$packageName = 'opendoor'
$version = $env:ChocolateyPackageVersion

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

  throw 'Python 3.12/3.13 was not found. The Chocolatey python313 dependency should have installed it.'
}

function Get-OpenDoorCommand {
  param(
    [string] $PythonExe
  )

  $command = Get-Command opendoor.exe -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }

  $scriptsDir = Join-Path (Split-Path $PythonExe -Parent) 'Scripts'
  $opendoorPath = Join-Path $scriptsDir 'opendoor.exe'

  if (Test-Path $opendoorPath) {
    return $opendoorPath
  }

  throw 'opendoor.exe was not found after installation.'
}

$pythonExe = Get-OpenDoorPython
$pipInstallTarget = "$packageName==$version"

if ($env:OPENDOOR_CHOCOLATEY_PIP_SPEC) {
  $pipInstallTarget = $env:OPENDOOR_CHOCOLATEY_PIP_SPEC
  Write-Host "Using OpenDoor pip install override: $pipInstallTarget"
}

Write-Host "Using Python: $pythonExe"
& $pythonExe -m pip install --disable-pip-version-check --no-input --upgrade pip
& $pythonExe -m pip install --disable-pip-version-check --no-input --upgrade $pipInstallTarget

if ($LASTEXITCODE -ne 0) {
  throw "Failed to install $pipInstallTarget."
}

$opendoorExe = Get-OpenDoorCommand -PythonExe $pythonExe
Write-Host "OpenDoor command: $opendoorExe"
& $opendoorExe --version