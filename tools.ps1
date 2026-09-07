[CmdletBinding()]
param(
    [ValidateSet("Setup", "Test", "VerifySources", "ValidateArtifact", "CheckCoverage")]
    [string]$Task = "Test",
    [string]$Artifact = "",
    [string]$Schema = "schemas/translation_candidate.schema.json"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if ($Task -eq "Setup") {
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        py -3.12 -m venv (Join-Path $RepoRoot ".venv")
    }
    & $VenvPython -m pip install --require-virtualenv --disable-pip-version-check `
        -r (Join-Path $RepoRoot "requirements-dev.lock")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $VenvPython -m pip install --require-virtualenv --disable-pip-version-check `
        --no-deps -e $RepoRoot
    exit $LASTEXITCODE
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Missing .venv. Run: .\tools.ps1 -Task Setup"
}

switch ($Task) {
    "Test" {
        & $VenvPython -m pytest
    }
    "VerifySources" {
        & $VenvPython -m spict4all.cli --root $RepoRoot verify-sources
    }
    "ValidateArtifact" {
        if (-not $Artifact) { throw "-Artifact is required" }
        & $VenvPython -m spict4all.cli --root $RepoRoot validate-artifact $Artifact --schema $Schema
    }
    "CheckCoverage" {
        if (-not $Artifact) { throw "-Artifact is required" }
        & $VenvPython -m spict4all.cli --root $RepoRoot check-coverage $Artifact
    }
}
exit $LASTEXITCODE
