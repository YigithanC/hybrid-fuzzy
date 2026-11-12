# Export presentation.pptx to presentation.pdf with PowerPoint (COM).
#   powershell -ExecutionPolicy Bypass -File presentation/export_pdf.ps1
param(
    [string]$pptx = (Join-Path $PSScriptRoot "presentation.pptx"),
    [string]$pdf = (Join-Path $PSScriptRoot "presentation.pdf")
)
$pptx = [string](Resolve-Path $pptx)
$app = New-Object -ComObject PowerPoint.Application
try {
    # Open(FileName, ReadOnly, Untitled, WithWindow)
    $p = $app.Presentations.Open($pptx, -1, 0, 0)
    $p.SaveAs([string]$pdf, 32)   # 32 = ppSaveAsPDF
    $p.Close()
    Write-Output "wrote $pdf"
}
finally {
    $app.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
