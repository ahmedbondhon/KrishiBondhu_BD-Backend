# ============================================================
# KrishiBondhu Bangladesh - Run Database Migrations
# ============================================================
# Works with any PostgreSQL database: Neon, Supabase, local, etc.
#
# Prerequisites:
#   psql installed (PostgreSQL client tools)
#   Windows: https://www.postgresql.org/download/windows/
#            (only "Command Line Tools" component is needed)
#
# Usage:
#   .\migrate.ps1 -ConnectionString "postgresql://user:pass@host/db"
#
# Examples:
#   Neon:     "postgresql://user:pass@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
#   Local:    "postgresql://postgres:password@localhost:5432/krishibondhu_db"
# ============================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ConnectionString = ""
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$migrationsDir = Join-Path $root "database\migrations"

Write-Host ""
Write-Host "  =======================================" -ForegroundColor Green
Write-Host "  KrishiBondhu - Database Migrations"     -ForegroundColor Green
Write-Host "  =======================================" -ForegroundColor Green
Write-Host ""

# --- Check psql is available ---
try {
    $null = & psql --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Host "  [ERROR] psql not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Install PostgreSQL client tools from:" -ForegroundColor Yellow
    Write-Host "  https://www.postgresql.org/download/windows/" -ForegroundColor White
    Write-Host "  (Only the 'Command Line Tools' component is needed)" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# --- Get connection string interactively if not provided ---
if ($ConnectionString -eq "") {
    Write-Host "  Enter your PostgreSQL connection string." -ForegroundColor Yellow
    Write-Host "  Neon:  postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require" -ForegroundColor Gray
    Write-Host "  Local: postgresql://postgres:password@localhost:5432/krishibondhu_db" -ForegroundColor Gray
    Write-Host ""
    $ConnectionString = Read-Host "  Connection string"
    Write-Host ""
}

# --- Run migrations in order ---
$migrations = Get-ChildItem -Path $migrationsDir -Filter "*.sql" | Sort-Object Name

Write-Host "  Running $($migrations.Count) migration files..." -ForegroundColor Cyan
Write-Host ""

$success = 0
$failed  = 0

foreach ($file in $migrations) {
    Write-Host "  -> $($file.Name)" -NoNewline

    $output = & psql $ConnectionString -f $file.FullName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        $success++
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "     $output" -ForegroundColor DarkRed
        $failed++
    }
}

Write-Host ""
if ($failed -eq 0) {
    Write-Host "  =======================================" -ForegroundColor Green
    Write-Host "  All $success migrations applied OK"     -ForegroundColor Green
    Write-Host "  Database is ready. Run: .\start.ps1"    -ForegroundColor White
    Write-Host "  =======================================" -ForegroundColor Green
} else {
    Write-Host "  =======================================" -ForegroundColor Yellow
    Write-Host "  $success OK, $failed failed"            -ForegroundColor Yellow
    Write-Host "  Fix errors above and re-run."           -ForegroundColor Yellow
    Write-Host "  =======================================" -ForegroundColor Yellow
}
Write-Host ""
