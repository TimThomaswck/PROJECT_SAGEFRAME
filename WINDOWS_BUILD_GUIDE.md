# Windows Build and Deployment Guide

**For Story 6.1: Windows Desktop Platform Support**

---

## Quick Start

### Build Windows Installer (Local)

```bash
# 1. Install build dependencies
pip install -e .[dev]
pip install pyinstaller

# 2. Build executable
pyinstaller sageframe.spec

# 3. Install Inno Setup (from https://jrsoftware.org/isinfo.php)
# Windows: Download and run installer
# Or via Chocolatey: choco install innosetup

# 4. Build Windows installer
iscc.exe installer.iss

# Results:
# - dist/SageFrame.exe (Standalone executable ~150-200MB)
# - dist/SageFrame-Setup.exe (Installer ~50-100MB)
```

### Automatic Build (GitHub Actions)

```bash
# Just push to main or develop branch
git push origin main

# GitHub Actions will:
# 1. Build executable with PyInstaller
# 2. Build installer with Inno Setup
# 3. Run tests on Windows
# 4. Upload artifacts
# 5. Create release (on tag)
```

---

## Build Process Details

### Step 1: Prepare Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/sageframe.git
cd sageframe/sageframe_desktop

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -e .[dev]

# Install PyInstaller
pip install pyinstaller>=5.0.0
```

### Step 2: Build Standalone Executable

**What**: Creates single `.exe` file that can run without Python installation

**Command**:
```bash
pyinstaller sageframe.spec
```

**Configuration** (from `sageframe.spec`):
- Entry point: `app/__main__.py`
- Standalone mode: Yes
- Hidden imports: PySide6, SQLAlchemy, Google APIs, keyring, qasync
- Data files: `resources/`, `i18n/`
- Console: No (GUI only)
- Icon: `app/resources/icon.ico`

**Output**:
- `dist/SageFrame.exe` (150-200 MB)
- `build/` directory (temporary, can delete)

**Troubleshooting**:

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError" | Add to hidden_imports in sageframe.spec |
| Executable too large | Normal for bundled Python + all dependencies |
| Startup slow first time | Normal, extracts bundled Python |
| Missing icon | Verify `app/resources/icon.ico` exists |

### Step 3: Build Windows Installer

**What**: Creates `.exe` installer that users can run to install the application

**Prerequisites**:
```bash
# Download Inno Setup from: https://jrsoftware.org/isinfo.php
# Or install via Chocolatey:
choco install innosetup

# Verify installation
iscc.exe --help
```

**Command**:
```bash
iscc.exe installer.iss
```

**Configuration** (from `installer.iss`):
- Application: SageFrame v1.0.0
- Installation directory: `C:\Program Files\SageFrame`
- Start Menu: Yes (creates "SageFrame" folder)
- Desktop icon: Yes
- Registry integration: Yes
- Protocol handler: `sageframe://` URLs
- Uninstall cleanup: Removes AppData\Local\SageFrame\cache

**Output**:
- `dist/SageFrame-Setup.exe` (50-100 MB)
- `Output/` directory (can contain more installers if built multiple times)

**Installer Features**:
- ✅ Welcome screen with license agreement
- ✅ Installation directory selection
- ✅ Start Menu folder creation
- ✅ Desktop shortcut
- ✅ Quick start option
- ✅ Uninstall shortcut
- ✅ Registry entries
- ✅ Protocol handler for `sageframe://` URLs

**Troubleshooting**:

| Issue | Solution |
|-------|----------|
| "iscc.exe not found" | Inno Setup not installed or not in PATH |
| "Build failed with error" | Check installer.iss syntax (Inno Setup-specific) |
| "File not found" | Verify `dist/SageFrame.exe` exists before running iscc |

### Step 4: Test Installation

**Manual Testing**:

```bash
# 1. Run installer
dist/SageFrame-Setup.exe

# 2. Follow wizard
# - Accept license
# - Select installation directory
# - Check "Create Start Menu shortcuts"
# - Check "Create Desktop icon"
# - Install

# 3. Verify installation
# - Look in Program Files\SageFrame
# - Check Start Menu for "SageFrame" folder
# - Check Desktop for shortcut
# - Verify registry entries exist

# 4. Run application
# - Click Desktop shortcut OR
# - Click Start Menu → SageFrame → SageFrame OR
# - Run C:\Program Files\SageFrame\SageFrame.exe
```

**Uninstall Testing**:

```bash
# 1. Control Panel → Programs → Uninstall a program
# 2. Find "SageFrame"
# 3. Click "Uninstall"
# 4. Follow wizard
# 5. Verify:
#    - Files removed from Program Files\SageFrame
#    - Start Menu folder removed
#    - Desktop shortcut removed
#    - Registry entries cleaned
#    - AppData\Local\SageFrame\cache cleaned
```

### Step 5: Test Application Features

**Core Features**:
- ✅ Application launches without errors
- ✅ Main window displays
- ✅ UI renders correctly
- ✅ Dark/light theme works
- ✅ Database creates in local AppData

**Windows Integration**:
- ✅ System tray icon appears
- ✅ Right-click tray context menu works
- ✅ Double-click tray shows/hides window
- ✅ Windows notifications appear
- ✅ Engagement suggestions notify
- ✅ Calendar events notify
- ✅ Data sync notifies completion

**Data Features**:
- ✅ Create projects
- ✅ Create tasks
- ✅ Assign to calendar
- ✅ Generate suggestions
- ✅ Filter by tags
- ✅ Save to local database
- ✅ Close/reopen retains data

**Offline Features**:
- ✅ Works without internet
- ✅ Shows offline status
- ✅ Queues calendar sync
- ✅ Resumes on reconnection

---

## GitHub Actions CI/CD Pipeline

### Workflow Overview

**File**: `.github/workflows/build-windows.yml`

**Triggers**:
- ✅ Push to `main` or `develop` branches
- ✅ Pull requests
- ✅ Manual trigger (workflow_dispatch)
- ✅ Tag creation (for releases)

### Build Job

**Environment**: Windows Server 2022 (windows-latest)

**Steps**:

1. **Checkout code**
   ```bash
   actions/checkout@v4
   ```

2. **Setup Python 3.12**
   ```bash
   actions/setup-python@v4
   with:
     python-version: '3.12'
     cache: 'pip'
   ```

3. **Install dependencies**
   ```bash
   pip install -e .[dev]
   pip install pyinstaller
   ```

4. **Run tests**
   ```bash
   pytest test_story_6_1.py -v
   ```

5. **Build executable**
   ```bash
   pyinstaller sageframe.spec
   ```

6. **Setup Inno Setup**
   ```bash
   choco install innosetup
   ```

7. **Build installer**
   ```bash
   iscc.exe installer.iss
   ```

8. **Verify artifacts**
   ```bash
   ls dist/SageFrame*.exe
   ```

9. **Upload artifacts**
   ```bash
   actions/upload-artifact@v3
   # Artifacts: dist/SageFrame.exe, dist/SageFrame-Setup.exe
   # Retention: 30 days
   ```

10. **Create release** (on tag)
    ```bash
    softprops/action-gh-release@v1
    # Attaches executables to GitHub release
    ```

### Test Job

**Runs after build job**

- Re-runs test suite on Windows
- Validates all Story 6.1 tests
- Publishes test results

### Monitoring

**Check build status**:
```bash
# In GitHub repository
Actions tab → Build Windows Installer

# View logs
Click on workflow run → view build logs
```

**Download artifacts**:
```bash
# In GitHub repository
Actions tab → latest workflow run
# Download artifacts section
# SageFrame.exe, SageFrame-Setup.exe available for 30 days
```

**Create release**:
```bash
# On GitHub
Releases tab → Create release from tag
# Executables auto-attached to release
```

---

## Distribution

### Option 1: GitHub Releases

1. **Push tag to trigger build**:
   ```bash
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   ```

2. **Wait for CI/CD**:
   - GitHub Actions builds executable and installer
   - Uploads artifacts
   - Creates release

3. **Download from GitHub Releases**:
   - https://github.com/yourusername/sageframe/releases
   - Direct download links for users

### Option 2: Direct Download

1. **Manually build locally**:
   ```bash
   pyinstaller sageframe.spec
   iscc.exe installer.iss
   ```

2. **Host on your server**:
   - Upload `dist/SageFrame-Setup.exe` to your website
   - Create download link
   - Share with users

### Option 3: Microsoft Store (Future)

1. **Prerequisites**:
   - Microsoft Store app submission requirements
   - Package signing
   - Store listing

2. **Steps**:
   - Prepare installer for Store
   - Submit through Partner Center
   - Available in Microsoft Store

---

## Troubleshooting Guide

### Build Issues

#### "pyinstaller: command not found"
```bash
# Solution: Install PyInstaller
pip install pyinstaller
```

#### "Entry point app/__main__.py not found"
```bash
# Solution: Verify file exists
ls app/__main__.py

# Or check sageframe.spec path configuration
```

#### "Hidden import PySide6 failed"
```bash
# Solution: Add to hidden_imports in sageframe.spec
hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets']
```

#### "Icon file not found"
```bash
# Solution: Verify icon exists
ls app/resources/icon.ico

# Or update sageframe.spec with correct path
```

### Installer Issues

#### "iscc.exe not found"
```bash
# Solution 1: Install Inno Setup
# Download from https://jrsoftware.org/isinfo.php

# Solution 2: Use Chocolatey
choco install innosetup

# Solution 3: Add to PATH
# C:\Program Files (x86)\Inno Setup 6\
```

#### "File not found in [Files] section"
```bash
# Solution: Verify dist/SageFrame.exe exists
pyinstaller sageframe.spec
ls dist/SageFrame.exe

# Then rebuild installer
iscc.exe installer.iss
```

#### "Registry access denied"
```bash
# Solution: Run installer as Administrator
# Right-click installer.exe → Run as administrator
```

### Runtime Issues

#### "Application won't start"
```bash
# Check Windows Event Viewer for errors
# Event Viewer → Windows Logs → Application

# Or check console output:
SageFrame.exe 2>&1 | tee output.log
```

#### "Database permission denied"
```bash
# Solution: Check file permissions
# AppData\Local\SageFrame\sageframe.db should be readable/writable

# Or manually set permissions
icacls C:\Users\<username>\AppData\Local\SageFrame /grant:r "%USERNAME%":F
```

#### "System tray not showing"
```bash
# This is normal on some Windows installations
# Check taskbar notification area
# Or check Windows → Settings → System → Notifications

# App still works, just not in tray
```

#### "Notifications not appearing"
```bash
# Check Windows Settings:
# Settings → System → Notifications & Actions

# Verify:
# - "Notifications" is ON
# - SageFrame is listed and enabled
# - Do Not Disturb is OFF
```

---

## Performance Optimization

### Reduce Executable Size

**Current**: 150-200 MB

**Options**:
1. **Use UPX compression** (if needed):
   ```bash
   pyinstaller sageframe.spec --upx-dir=./upx
   ```

2. **Remove unnecessary hidden imports** from `sageframe.spec`

3. **Use OneDrive/cloud storage** for large assets

### Improve Startup Time

**Current**: ~2-5 seconds first run, <1 second cached

**Optimization**:
1. Use PyInstaller `--onefile` mode (included in spec)
2. Pre-extract bootloader
3. Lazy load feature modules

### Installer Size

**Current**: 50-100 MB

**Optimization**:
1. Delta updates (update only changed files)
2. Separate data download (post-install)
3. Incremental builds

---

## Security Considerations

### Code Signing

**Future enhancement**: Sign executable with certificate
```bash
# Sign executable
signtool sign /f cert.pfx /p password /t http://timestamp.digicert.com SageFrame.exe

# Sign installer
signtool sign /f cert.pfx /p password /t http://timestamp.digicert.com SageFrame-Setup.exe
```

### File Permissions

**Database security**:
```bash
# Restrictive permissions (Windows)
# AppData\Local\SageFrame\sageframe.db: Owner read/write only
```

**Verified in `app/database.py`**:
- `_set_database_security()` sets file permissions
- Prevents unauthorized access

### Registry Security

**Protocol handler**:
```
HKEY_CURRENT_USER\Software\Classes\sageframe
```
- Scoped to user, not system-wide
- Safe registry modifications

---

## Maintenance

### Update Application

**Version bump**:
1. Update version in `installer.iss`:
   ```ini
   AppVersion=1.0.1
   ```

2. Rebuild installer:
   ```bash
   pyinstaller sageframe.spec
   iscc.exe installer.iss
   ```

3. Tag and push:
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

### Rollback Installation

**If issues after update**:
```bash
# Uninstall current version
C:\Program Files\SageFrame\unins000.exe

# Install previous version
# Download from GitHub Releases or backup
SageFrame-Setup.exe
```

---

## References

### External Resources

| Resource | Link | Purpose |
|----------|------|---------|
| PyInstaller | https://pyinstaller.org/ | Executable creation |
| Inno Setup | https://jrsoftware.org/ | Windows installer |
| Python | https://python.org/ | Language runtime |
| PySide6 | https://wiki.qt.io/Qt_for_Python | GUI framework |
| GitHub Actions | https://docs.github.com/actions | CI/CD |

### Configuration Files

| File | Purpose |
|------|---------|
| `sageframe.spec` | PyInstaller configuration |
| `installer.iss` | Inno Setup configuration |
| `.github/workflows/build-windows.yml` | GitHub Actions workflow |
| `pyproject.toml` | Project metadata and dependencies |
| `app/__main__.py` | Application entry point |

---

## Support

### Common Questions

**Q: How do I build the Windows installer locally?**

A: Follow steps 1-4 in "Step 1: Prepare Development Environment" through "Step 3: Build Windows Installer"

**Q: Can I automate the build process?**

A: Yes, GitHub Actions workflow (`.github/workflows/build-windows.yml`) automates everything

**Q: What are the system requirements?**

A: Windows 10/11, 200MB disk space, no Python installation needed (bundled)

**Q: How do I distribute the installer?**

A: Upload to GitHub Releases, your website, or Microsoft Store (future)

**Q: Is the executable secure?**

A: Yes, includes file permission hardening and registry security measures from Story 5.1

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-26  
**Related Story**: 6.1 - Windows Desktop Platform Support  
