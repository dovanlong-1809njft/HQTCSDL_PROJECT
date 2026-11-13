# Parse only: does not open any SQL connection or execute T-SQL.
param([string]$ScriptDomPath = 'C:\Program Files\Microsoft SQL Server Management Studio 22\Release\Common7\IDE\Extensions\Application\Microsoft.SqlServer.TransactSql.ScriptDom.dll')
$ErrorActionPreference = 'Stop'
Add-Type -Path $ScriptDomPath
$repoPath = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$parser = [Microsoft.SqlServer.TransactSql.ScriptDom.TSql160Parser]::new($true)
$files = @('database/views/04_heritage_views.sql', 'database/procedures/04_heritage_procs.sql', 'database/triggers/04_heritage_triggers.sql', 'tests/database/tv4.integration.sql')
$failed = $false
foreach ($file in $files) {
    $source = [IO.File]::ReadAllText((Join-Path $repoPath $file)).Replace('$(DB_NAME)', 'TV4_Static_Only')
    $errors = $null
    $null = $parser.Parse([IO.StringReader]::new($source), [ref]$errors)
    if ($errors.Count) { $failed = $true; $errors | ForEach-Object { Write-Output "$file line $($_.Line): $($_.Message)" } }
    else { Write-Output "PASS parse: $file" }
}
if ($failed) { throw 'TV4 T-SQL parse failed.' }
