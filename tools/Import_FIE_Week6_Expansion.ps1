param(
    [Parameter(Mandatory=$true)][string]$RepoPath,
    [string]$DeliveryFolder = $PSScriptRoot,
    [string]$WorktreePath = (Join-Path $env:USERPROFILE ('FIE\Expansion-' + (Get-Date -Format 'yyyyMMdd-HHmmss')))
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Add-Type -AssemblyName System.IO.Compression.FileSystem
$IndexPath = Join-Path $DeliveryFolder 'FIE_Week6_Expansion_AM_2026-10-14_index.json'
$Index = Get-Content -LiteralPath $IndexPath -Raw | ConvertFrom-Json
if ($Index.schema -ne 'fie-recovery-volumes-v1' -or $Index.checkpoint.stage -ne 'AM_READY') {
    throw 'This importer requires the final AM_READY delivery index. Intermediate checkpoints are not releases.'
}
if ([System.IO.Path]::GetFileName($Index.archive_name) -ne $Index.archive_name) { throw 'Unsafe archive name.' }
if ($Index.checkpoint.head -notmatch '^[0-9a-f]{40}$' -or $Index.checkpoint.branch -ne 'ops/waiver-profile-expansion-2026-10-14') { throw 'Unexpected final commit or branch identity.' }
if (@($Index.checkpoint.uncommitted_files).Count -ne 0) { throw 'The final delivery must have a fully committed tree.' }
if (Test-Path -LiteralPath $WorktreePath) { throw 'Choose a new short worktree path; existing worktrees are preserved.' }
$Staging = Join-Path $DeliveryFolder ('join-' + [guid]::NewGuid().ToString('N').Substring(0,10))
New-Item -ItemType Directory -Path $Staging | Out-Null
$Archive = Join-Path $Staging $Index.archive_name
$Output = [System.IO.File]::Open($Archive,[System.IO.FileMode]::CreateNew)
try {
    foreach ($Part in $Index.parts) {
        if ([System.IO.Path]::GetFileName($Part.file_name) -ne $Part.file_name -or
            [System.IO.Path]::GetFileName($Part.payload) -ne $Part.payload) { throw 'Unsafe volume name.' }
        $Volume = Join-Path $DeliveryFolder $Part.file_name
        if ((Get-FileHash -LiteralPath $Volume -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Part.sha256) {
            throw ('Volume hash mismatch: ' + $Part.file_name)
        }
        $Zip = [System.IO.Compression.ZipFile]::OpenRead($Volume)
        try {
            $Entry = $Zip.GetEntry($Part.payload)
            if ($null -eq $Entry) { throw ('Missing payload: ' + $Part.file_name) }
            $Payload = Join-Path $Staging $Part.payload
            $SourceStream = $Entry.Open()
            $Piece = [System.IO.File]::Open($Payload,[System.IO.FileMode]::CreateNew)
            try { $SourceStream.CopyTo($Piece) } finally { $Piece.Dispose(); $SourceStream.Dispose() }
            if ((Get-FileHash -LiteralPath $Payload -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Part.payload_sha256) {
                throw ('Payload hash mismatch: ' + $Part.file_name)
            }
            $SourceStream = [System.IO.File]::OpenRead($Payload)
            try { $SourceStream.CopyTo($Output) } finally { $SourceStream.Dispose() }
        } finally { $Zip.Dispose() }
    }
} finally { $Output.Dispose() }
if ((Get-Item -LiteralPath $Archive).Length -ne $Index.archive_size -or
    (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Index.archive_sha256) {
    throw 'Reconstructed archive hash or size mismatch.'
}
$Unpacked = Join-Path $Staging 'ready'
Expand-Archive -LiteralPath $Archive -DestinationPath $Unpacked
$Bundle = Join-Path $Unpacked 'recovery.bundle'
if ((Get-FileHash -LiteralPath $Bundle -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Index.checkpoint.bundle_sha256) {
    throw 'Git bundle hash mismatch.'
}
git -C $RepoPath config --local core.longpaths true
if ($LASTEXITCODE -ne 0) { throw 'Could not enable repository long-path support.' }
git -C $RepoPath fetch origin main
if ($LASTEXITCODE -ne 0) { throw 'Could not fetch main.' }
git -C $RepoPath bundle verify $Bundle
if ($LASTEXITCODE -ne 0) { throw 'Bundle prerequisites are missing or invalid.' }
git -C $RepoPath fetch $Bundle $Index.checkpoint.branch
if ($LASTEXITCODE -ne 0) { throw 'Could not import the verified bundle.' }
$Imported = (git -C $RepoPath rev-parse FETCH_HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $Imported -ne $Index.checkpoint.head) { throw 'Imported commit differs from the delivery receipt.' }
git -C $RepoPath worktree add -b $Index.checkpoint.branch $WorktreePath $Imported
if ($LASTEXITCODE -ne 0) { throw 'Could not create the new worktree. Preserve all existing worktrees.' }
$Dirty = @(git -C $WorktreePath status --porcelain)
if ($LASTEXITCODE -ne 0 -or $Dirty.Count -ne 0) { throw 'The imported worktree is not clean.' }
Write-Host ('IMPORTED: ' + $WorktreePath)
Write-Host ('COMMIT: ' + $Imported)
Write-Host 'Continue with docs/audits/WAIVER_EXPANSION_IMPLEMENTATION_2026-10-14.md, Step 2. Nothing was pushed or merged.'
