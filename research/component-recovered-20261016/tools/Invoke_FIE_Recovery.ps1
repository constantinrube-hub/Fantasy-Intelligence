param(
 [Parameter(Mandatory=$true)][ValidateSet('Replay','Capture','FitFresh','Forecast','Baselines','Freeze','Actuals','Review','Validate','Test')][string]$Action,
 [string]$Python = '',
 [int]$StartWeek = 6,
 [int]$Stage = 4,
 [int]$Week = 5,
 [string]$Output = '',
 [string]$Bundle = 'data/research/components/2026-10-15/joint-v5/observations/observation-bundle.json',
 [string]$Fitted = 'data/research/components/recovery-20261016/fit/fitted.json',
 [string]$Training = 'data/research/components/2026-10-14/c2-c4-v1/priors',
 [string]$Reference = 'data/research/components/recovery-20261016/verified/stage4',
 [string[]]$Issuances = @(),
 [string]$Freeze = 'data/research/components/recovery-20261016/freeze',
 [string[]]$Actuals = @()
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
if (-not $Python) { $Python = Join-Path $Root '.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw "Python missing: $Python. Create .venv and install research/requirements-recovery.txt first." }
function Run-Python { param([string[]]$Items) & $Python @Items; if ($LASTEXITCODE -ne 0) { throw "Python failed (exit $LASTEXITCODE): $($Items -join ' ')" } }
if (-not $Output) { $Output = 'data/research/components/recovery-20261016/runs/' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + $Action }
switch ($Action) {
 'Replay' { Run-Python -Items @('research/recovery_pipeline.py','--output',$Output,'--bundle',$Bundle,'--fitted',$Fitted,'--training-dir',$Training,'--start-week',"$StartWeek",'--stage',"$Stage",'--replay'); Run-Python -Items @('research/recovery_validate.py','--base',$Output) }
 'Capture' { Run-Python -Items @('research/recovery_capture.py','--output',$Output,'--start-week',"$StartWeek") }
 'FitFresh' { $Through = $StartWeek - 1; Run-Python -Items @('research/recovery_refit.py','--output',$Output,'--bundle',$Bundle,'--training-dir',$Training,'--through-week',"$Through") }
 'Forecast' { Run-Python -Items @('research/recovery_pipeline.py','--output',$Output,'--bundle',$Bundle,'--fitted',$Fitted,'--training-dir',$Training,'--start-week',"$StartWeek",'--stage',"$Stage"); Run-Python -Items @('research/recovery_validate.py','--base',$Output) }
 'Baselines' { Run-Python -Items @('research/recovery_comparators.py','--output',$Output,'--reference',$Reference) }
 'Freeze' { if ($Issuances.Count -eq 0) { throw 'Supply -Issuances as an array of issuance directories.' }; Run-Python -Items (@('research/recovery_evaluate.py','freeze','--output',$Output,'--issuance') + $Issuances) }
 'Actuals' { Run-Python -Items @('research/recovery_outcomes.py','--output',$Output,'--week',"$Week",'--bundle',$Bundle,'--training-output',($Output + '-training')) }
 'Review' { Run-Python -Items (@('research/recovery_evaluate.py','review','--freeze',$Freeze,'--output',$Output,'--actual') + $Actuals) }
 'Validate' { Run-Python -Items @('research/recovery_validate.py','--base',$Reference) }
 'Test' { Run-Python -Items @('-m','unittest','discover','-s','research','-p','integrity_recovery_test.py','-v') }
}
Write-Host "Completed $Action. Output: $Output"
