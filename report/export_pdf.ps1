# Convert report/report.docx to report/report.pdf with Microsoft Word (COM automation).
# Usage: powershell -ExecutionPolicy Bypass -File report/export_pdf.ps1
# Note: Document.ExportAsFixedFormat hung on this machine; SaveAs2 with wdFormatPDF (17) works.
$ErrorActionPreference = 'Stop'
[string]$docx = (Join-Path $PSScriptRoot 'report.docx')
[string]$pdf = (Join-Path $PSScriptRoot 'report.pdf')
$format = 17   # wdFormatPDF
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0          # wdAlertsNone
try {
    # Open(FileName, ConfirmConversions, ReadOnly, AddToRecentFiles)
    $d = $word.Documents.Open($docx, $false, $true, $false)
    $d.SaveAs2([ref]$pdf, [ref]$format)
    "pages: " + $d.ComputeStatistics(2)
    $d.Close([ref]0)
    "saved $pdf"
} finally {
    $word.Quit()
}
