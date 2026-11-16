# Convert report/report.docx to report/report.pdf with Microsoft Word (COM automation).
# Usage: powershell -ExecutionPolicy Bypass -File report/export_pdf.ps1
# Note: Document.ExportAsFixedFormat hung on this machine; SaveAs2 with wdFormatPDF (17) works.
# Word sometimes reports success without overwriting an existing PDF in the project folder,
# so the PDF is written to %TEMP% first and then copied over report.pdf.
$ErrorActionPreference = 'Stop'
[string]$docx = (Join-Path $PSScriptRoot 'report.docx')
[string]$pdf = (Join-Path $PSScriptRoot 'report.pdf')
[string]$tmp = (Join-Path $env:TEMP 'report_export.pdf')
$format = 17   # wdFormatPDF
if (Test-Path $tmp) { Remove-Item $tmp }
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0          # wdAlertsNone
try {
    # Open(FileName, ConfirmConversions, ReadOnly, AddToRecentFiles)
    $d = $word.Documents.Open($docx, $false, $true, $false)
    $d.SaveAs2([ref]$tmp, [ref]$format)
    "pages: " + $d.ComputeStatistics(2)
    $d.Close([ref]0)
} finally {
    $word.Quit()
}
Copy-Item $tmp $pdf -Force
"saved $pdf"
