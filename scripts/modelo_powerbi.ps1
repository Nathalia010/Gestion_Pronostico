param([string]$Mode = 'inspect')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$lib = Join-Path $root '.tools\amo\lib\net8.0'
foreach ($dll in @('Microsoft.AnalysisServices.Runtime.Core.dll','Microsoft.AnalysisServices.Core.dll','Microsoft.AnalysisServices.Tabular.dll','Microsoft.AnalysisServices.Tabular.Json.dll')) {
    [Reflection.Assembly]::LoadFrom((Join-Path $lib $dll)) | Out-Null
}
$portFile = Get-ChildItem "$env:USERPROFILE\Microsoft\Power BI Desktop Store App\AnalysisServicesWorkspaces" -Recurse -Filter msmdsrv.port.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$port = Get-Content $portFile.FullName -Encoding Unicode
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("Data Source=localhost:$port")
$db = $server.Databases[0]
if ($Mode -eq 'inspect') {
    foreach ($table in $db.Model.Tables) {
        Write-Output ('TABLE '+$table.Name)
        $table.Columns | Select-Object Name,DataType | Format-Table
    }
    foreach ($rel in $db.Model.Relationships) { Write-Output ($rel.FromTable.Name+'.'+$rel.FromColumn.Name+' -> '+$rel.ToTable.Name+'.'+$rel.ToColumn.Name) }
} elseif ($Mode -eq 'apply') {
    foreach ($item in @(@('Ventas','FechaVenta'),@('Inventario','FechaCorte'),@('Importaciones','FechaPedido'))) {
        $relName = 'MPS_'+$item[0]+'_Calendario'
        if (!$db.Model.Relationships.Find($relName)) {
            $rel = New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship
            $rel.Name = $relName
            $rel.FromColumn = $db.Model.Tables[$item[0]].Columns[$item[1]]
            $rel.ToColumn = $db.Model.Tables['Calendario'].Columns['Fecha']
            $rel.FromCardinality = 'Many'
            $rel.ToCardinality = 'One'
            $rel.CrossFilteringBehavior = 'OneDirection'
            $db.Model.Relationships.Add($rel)
        }
    }
    $db.Model.Tables['Calendario'].Columns['AñoMes'].FormatString = 'yyyy-MM'
    $defs = Get-Content (Join-Path $root 'scripts\medidas.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($def in $defs) {
        $table = $db.Model.Tables[$def.table]
        $measure = $table.Measures.Find($def.name)
        if (!$measure) { $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure; $measure.Name=$def.name; $table.Measures.Add($measure) }
        $measure.Expression = $def.expression
        $measure.FormatString = $def.format
        $measure.DisplayFolder = 'MPS | Indicadores'
    }
    $db.Model.SaveChanges() | Out-Null
    foreach ($table in $db.Model.Tables) { foreach ($measure in $table.Measures) { Write-Output ($measure.Name+': '+$measure.State+' '+$measure.ErrorMessage) } }
}
$server.Disconnect()
