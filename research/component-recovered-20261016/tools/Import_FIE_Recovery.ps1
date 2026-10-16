param(
 [Parameter(Mandatory=$true)][string]$SourceZip,
 [Parameter(Mandatory=$true)][string]$RuntimeZip,
 [Parameter(Mandatory=$true)][string]$Destination,
 [string]$Repository = '',
 [string]$Branch = 'research/component-recovered-20261016',
 [switch]$Push,
 [string]$Python = 'py'
)
$ErrorActionPreference = 'Stop'
$SourceZip = (Resolve-Path -LiteralPath $SourceZip).Path
$RuntimeZip = (Resolve-Path -LiteralPath $RuntimeZip).Path
$Destination = [IO.Path]::GetFullPath($Destination)
function Git-Run { param([string[]]$Items) & git @Items; if ($LASTEXITCODE -ne 0) { throw "Git failed: $($Items -join ' ')" } }
if (Test-Path -LiteralPath $Destination) { throw 'Destination must be a new directory.' }
if ($Repository) {
 $Repository = (Resolve-Path -LiteralPath $Repository).Path
 Git-Run -Items @('-C',$Repository,'fetch','origin','main')
 Git-Run -Items @('-C',$Repository,'worktree','add','-b',$Branch,$Destination,'origin/main')
 $Target = Join-Path $Destination 'research/component-recovered-20261016'
} else {
 if ($Push) { throw '-Push requires -Repository.' }
 $Target = $Destination
}
New-Item -ItemType Directory -Path $Target -Force | Out-Null
Expand-Archive -LiteralPath $SourceZip -DestinationPath $Target
Expand-Archive -LiteralPath $RuntimeZip -DestinationPath $Target -Force
Set-Location $Target
& $Python 'research/recovery_verify_delivery.py'
if ($LASTEXITCODE -ne 0) { throw 'Extracted package verification failed. Nothing will be committed or pushed.' }
if ($Repository) {
 $Attributes = "data/** -text`nconfig/** -text`nresearch/** text eol=lf`ntools/** text eol=lf`n*.json -text`n*.md text eol=lf`n"
 [IO.File]::WriteAllText((Join-Path $Target '.gitattributes'),$Attributes,[Text.UTF8Encoding]::new($false))
 Git-Run -Items @('-C',$Destination,'add','--','research/component-recovered-20261016')
 Git-Run -Items @('-C',$Destination,'commit','-m','Restore isolated component generation and evaluation pipeline')
 if ($Push) { Git-Run -Items @('-C',$Destination,'push','-u','origin',$Branch) }
 Write-Host "Research branch prepared: $Branch"
}
Write-Host "Verified project: $Target"
Write-Host 'Create .venv, install research/requirements-recovery.txt, then run tools/Invoke_FIE_Recovery.ps1 -Action Test.'
