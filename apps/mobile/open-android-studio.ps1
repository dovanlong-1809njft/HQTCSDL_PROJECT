$ErrorActionPreference = 'Stop'
$projectPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path.TrimEnd('\')
if (-not ('FamilyConnect.DemoDrive' -as [type])) {
    Add-Type -Namespace FamilyConnect -Name DemoDrive -MemberDefinition '[System.Runtime.InteropServices.DllImport("kernel32.dll", CharSet = System.Runtime.InteropServices.CharSet.Unicode, SetLastError = true)] public static extern uint QueryDosDevice(string name, System.Text.StringBuilder target, int maxLength);'
}
$driveTarget = New-Object Text.StringBuilder 32768
$found = [FamilyConnect.DemoDrive]::QueryDosDevice('F:', $driveTarget, $driveTarget.Capacity)
if ($found) {
    if ($driveTarget.ToString().TrimEnd('\') -ne ('\??\' + $projectPath)) {
        throw 'Drive F: is mapped to another folder. Choose a free drive before opening this project.'
    }
} else {
    if (Test-Path 'F:/') { throw 'Drive F: is already in use.' }
    subst.exe F: $projectPath
    if ($LASTEXITCODE -ne 0) { throw 'Could not map F: to the mobile project.' }
}
$studioPath = Join-Path $env:ProgramFiles 'Android/Android Studio/bin/studio64.exe'
if (-not (Test-Path -LiteralPath $studioPath)) { throw 'Install Android Studio first.' }
# Gradle on this Windows machine cannot load the wrapper through a path containing Vietnamese characters.
Start-Process -FilePath $studioPath -ArgumentList 'F:\apps\mobile' -WindowStyle Normal
