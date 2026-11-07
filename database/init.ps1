param(
    [string]$Server = "localhost",
    [string]$DbName = "FamilyConnect",
    [string]$User = "",
    [string]$Password = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$Folders = @("schema", "views", "procedures", "triggers", "seed")

foreach ($dir in $Folders) {
    $targetPath = Join-Path $ScriptDir $dir
    if (-not (Test-Path $targetPath)) { continue }

    Get-ChildItem -Path $targetPath -Filter "*.sql" | Sort-Object Name | ForEach-Object {
        Write-Host "Dang chay $dir/$($_.Name)..." -ForegroundColor Cyan

        $argsList = @("-S", $Server, "-C", "-b", "-I", "-v", "DB_NAME=$DbName", "-i", $_.FullName)
        if ($_.Name -ne "00_schemas.sql") {
            $argsList = @("-d", $DbName) + $argsList
        }

        if ([string]::IsNullOrWhiteSpace($User)) {
            $argsList = @("-E") + $argsList
        } else {
            $argsList = @("-U", $User, "-P", $Password) + $argsList
        }

        & sqlcmd @argsList
        if ($LASTEXITCODE -ne 0) {
            throw "Loi khi chay file $dir/$($_.Name) (ExitCode: $LASTEXITCODE)"
        }
    }
}

Write-Host "Hoan tat khoi tao Database '$DbName' tren '$Server'!" -ForegroundColor Green
