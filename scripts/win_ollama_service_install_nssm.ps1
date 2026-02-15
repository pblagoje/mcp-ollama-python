<#
    Ollama Windows Service Installer using NSSM
    -------------------------------------------
    This script uses NSSM (Non-Sucking Service Manager) to wrap ollama.exe as a Windows service.
    NSSM will be automatically downloaded if not present.
    
    Run as Administrator:
    Start-Process powershell -Verb RunAs -ArgumentList "-NoExit", "-Command", "cd 'C:\myCode\gitHub\mcp-ollama-python\scripts'; .\win_ollama_service_install_nssm.ps1"

    Features:
    - Auto-downloads NSSM if needed
    - Detects Ollama installation path
    - Supports custom port (default: 11434)
    - Supports custom model storage path
    - Creates firewall rule
    - Supports uninstall mode
#>

[CmdletBinding()]
param(
    [string]$ServiceName = "ollama",
    [string]$DisplayName = "Ollama Service",
    [int]$Port = 11434,
    [string]$ModelPath,
    [string]$OllamaPath,
    [switch]$Uninstall,
    [switch]$Silent
)

$LogFile = Join-Path -Path $PSScriptRoot -ChildPath "OllamaServiceInstall.log"
$NssmPath = Join-Path -Path $PSScriptRoot -ChildPath "nssm.exe"

function Log {
    param([string]$Message, [switch]$NoConsole)
    
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "$timestamp  $Message"
    $line | Out-File -FilePath $LogFile -Append -Encoding UTF8
    
    if (-not $Silent -and -not $NoConsole) {
        Write-Host $Message
    }
}

Log "=== Ollama Service Installer (NSSM) started ==="
Log "Parameters: ServiceName=$ServiceName, Port=$Port, ModelPath=$ModelPath, OllamaPath=$OllamaPath, Uninstall=$Uninstall"

# --- Check admin ---
function Assert-Admin {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Log "ERROR: Script must be run as Administrator."
        throw "Run this script in an elevated PowerShell session."
    }
}
Assert-Admin

# --- Uninstall mode ---
if ($Uninstall) {
    Log "Uninstall mode requested."
    
    if (Test-Path $NssmPath) {
        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc) {
            Log "Stopping and removing service '$ServiceName'..."
            & $NssmPath stop $ServiceName | Out-Null
            Start-Sleep -Seconds 2
            & $NssmPath remove $ServiceName confirm | Out-Null
            Log "Service '$ServiceName' removed."
        } else {
            Log "Service '$ServiceName' not found."
        }
    } else {
        Log "NSSM not found, attempting manual service removal..."
        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc) {
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            sc.exe delete $ServiceName | Out-Null
            Log "Service '$ServiceName' removed."
        }
    }
    
    # Remove firewall rule
    $fwRuleName = "Ollama Port $Port"
    $rule = Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue
    if ($rule) {
        Log "Removing firewall rule '$fwRuleName'..."
        Remove-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue
        Log "Firewall rule removed."
    }
    
    Log "=== Uninstall completed ==="
    if (-not $Silent) {
        Write-Host "Ollama service uninstalled. Log: $LogFile"
    }
    exit 0
}

# --- Download NSSM if not present ---
if (-not (Test-Path $NssmPath)) {
    Log "NSSM not found. Downloading..."
    
    try {
        $nssmZipUrl = "https://nssm.cc/release/nssm-2.24.zip"
        $nssmZipPath = Join-Path -Path $PSScriptRoot -ChildPath "nssm.zip"
        $nssmExtractPath = Join-Path -Path $PSScriptRoot -ChildPath "nssm_temp"
        
        # Download
        Log "Downloading NSSM from $nssmZipUrl..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $nssmZipUrl -OutFile $nssmZipPath -UseBasicParsing
        
        # Extract
        Log "Extracting NSSM..."
        Expand-Archive -Path $nssmZipPath -DestinationPath $nssmExtractPath -Force
        
        # Determine architecture and copy appropriate nssm.exe
        $arch = if ([Environment]::Is64BitOperatingSystem) { "win64" } else { "win32" }
        $nssmExeSource = Get-ChildItem -Path $nssmExtractPath -Recurse -Filter "nssm.exe" | 
            Where-Object { $_.FullName -like "*\$arch\*" } | 
            Select-Object -First 1
        
        if ($nssmExeSource) {
            Copy-Item -Path $nssmExeSource.FullName -Destination $NssmPath -Force
            Log "NSSM copied to $NssmPath"
        } else {
            throw "Could not find nssm.exe for $arch architecture"
        }
        
        # Cleanup
        Remove-Item -Path $nssmZipPath -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $nssmExtractPath -Recurse -Force -ErrorAction SilentlyContinue
        
        Log "NSSM downloaded and extracted successfully."
    }
    catch {
        Log "ERROR downloading NSSM: $_"
        throw "Failed to download NSSM. Please download manually from https://nssm.cc/download and place nssm.exe in the scripts folder."
    }
}

if (-not (Test-Path $NssmPath)) {
    Log "ERROR: NSSM not found at $NssmPath"
    throw "NSSM is required but not found."
}

Log "Using NSSM at: $NssmPath"

# --- Detect Ollama path ---
if (-not $OllamaPath) {
    $PossiblePaths = @(
        "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
        "$env:PROGRAMFILES\Ollama\ollama.exe",
        "$env:PROGRAMFILES(X86)\Ollama\ollama.exe"
    )
    
    $OllamaPath = $PossiblePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $OllamaPath -or -not (Test-Path $OllamaPath)) {
    Log "ERROR: Could not find ollama.exe."
    throw "Ollama executable not found. Install Ollama or specify -OllamaPath."
}

Log "Using Ollama executable: $OllamaPath"

# --- Remove existing service if present ---
$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Log "Existing service '$ServiceName' found. Removing..."
    & $NssmPath stop $ServiceName | Out-Null
    Start-Sleep -Seconds 2
    & $NssmPath remove $ServiceName confirm | Out-Null
    Start-Sleep -Seconds 2
    Log "Old service removed."
}

# --- Build environment variables ---
$envVars = @{
    "OLLAMA_HOST" = "0.0.0.0:$Port"
}

if ($ModelPath) {
    $envVars["OLLAMA_MODELS"] = $ModelPath
    Log "Using custom model path: $ModelPath"
}

# --- Install service with NSSM ---
try {
    Log "Installing service '$ServiceName' with NSSM..."
    
    # Install service
    & $NssmPath install $ServiceName $OllamaPath serve
    
    if ($LASTEXITCODE -ne 0) {
        throw "NSSM install failed with exit code $LASTEXITCODE"
    }
    
    # Configure service
    & $NssmPath set $ServiceName DisplayName $DisplayName
    & $NssmPath set $ServiceName Description "Ollama AI model server running on port $Port"
    & $NssmPath set $ServiceName Start SERVICE_AUTO_START
    
    # Set environment variables
    foreach ($key in $envVars.Keys) {
        & $NssmPath set $ServiceName AppEnvironmentExtra "$key=$($envVars[$key])"
        Log "Set environment: $key=$($envVars[$key])"
    }
    
    # Configure stdout/stderr logging
    $logDir = Join-Path -Path $PSScriptRoot -ChildPath "logs"
    if (-not (Test-Path $logDir)) {
        New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    }
    
    $stdoutLog = Join-Path -Path $logDir -ChildPath "ollama-stdout.log"
    $stderrLog = Join-Path -Path $logDir -ChildPath "ollama-stderr.log"
    
    & $NssmPath set $ServiceName AppStdout $stdoutLog
    & $NssmPath set $ServiceName AppStderr $stderrLog
    & $NssmPath set $ServiceName AppRotateFiles 1
    & $NssmPath set $ServiceName AppRotateBytes 1048576  # 1MB
    
    Log "Service '$ServiceName' installed successfully."
}
catch {
    Log "ERROR installing service: $_"
    throw "Failed to install service with NSSM."
}

# --- Configure firewall rule ---
try {
    $fwRuleName = "Ollama Port $Port"
    $existingRule = Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue
    
    if ($existingRule) {
        Log "Firewall rule '$fwRuleName' already exists."
    } else {
        Log "Creating firewall rule '$fwRuleName' for TCP port $Port..."
        New-NetFirewallRule `
            -DisplayName $fwRuleName `
            -Direction Inbound `
            -Action Allow `
            -Protocol TCP `
            -LocalPort $Port `
            -Profile Any | Out-Null
        
        Log "Firewall rule created."
    }
}
catch {
    Log "Warning: Failed to create firewall rule: $_"
}

# --- Start service ---
try {
    Log "Starting service '$ServiceName'..."
    & $NssmPath start $ServiceName
    
    if ($LASTEXITCODE -eq 0) {
        Start-Sleep -Seconds 3
        $svc = Get-Service -Name $ServiceName
        if ($svc.Status -eq 'Running') {
            Log "Service '$ServiceName' started successfully."
        } else {
            Log "Warning: Service status is $($svc.Status)"
        }
    } else {
        throw "NSSM start failed with exit code $LASTEXITCODE"
    }
}
catch {
    Log "ERROR starting service: $_"
    throw "Service installed but failed to start. Check logs in $logDir"
}

Log "=== Ollama Service Installer completed successfully ==="

if (-not $Silent) {
    Write-Host ""
    Write-Host "Ollama service installed and running on port $Port." -ForegroundColor Green
    Write-Host "Service logs: $logDir"
    Write-Host "Installation log: $LogFile"
    Write-Host ""
    Write-Host "To manage the service:"
    Write-Host "  Start:   Start-Service $ServiceName"
    Write-Host "  Stop:    Stop-Service $ServiceName"
    Write-Host "  Status:  Get-Service $ServiceName"
    Write-Host "  Uninstall: .\win_ollama_service_install_nssm.ps1 -Uninstall"
}
