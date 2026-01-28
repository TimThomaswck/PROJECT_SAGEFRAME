# Story 6.1: Implement Windows Desktop Platform Support

Status: ready-for-dev

## Epic Context

**Epic 6: Extensibility & Platform Integration**

Users can trust that the system operates reliably within its defined technical boundaries by running Sageframe on the Windows desktop platform.

This story ensures Windows platform compatibility and proper OS integration.

## Story

As a user,
I want to run Sageframe on the Windows desktop platform,
so that I can use the application on my primary operating system.

## Acceptance Criteria

1. **Given** the application is built, **When** I run the installer or executable on a Windows desktop, **Then** the application installs and launches correctly without platform-specific errors.

2. **Given** the application is running on Windows, **Then** it integrates as expected with the operating system (e.g., appears in the taskbar, can be pinned to the start menu, and can be properly uninstalled).

3. **Given** the application is running on Windows, **Then** all features defined in previous stories function as expected within the Windows environment.

4. **Given** the application is built for Windows, **Then** the CI/CD pipeline (as per Architecture) produces a valid Windows installer or executable.

## Business Value & Context

**Primary User Need:** Windows is the primary desktop platform for most business users. Proper Windows integration is essential for user adoption.

**Why This Matters:**
- Windows is target platform per architecture (Windows Desktop First)
- Proper OS integration improves user experience (taskbar, start menu, notifications)
- Professional installer builds trust (not just a .py script)
- Foundation for future platform expansion (Android)

**Related FRs:**
- FR27: Windows desktop platform support

## Tasks / Subtasks

- [ ] PySide6 Windows compatibility (AC: #1, #3)
  - [ ] Verify PySide6 Qt framework works on Windows 10/11
  - [ ] Test all UI components on Windows
  - [ ] Handle Windows-specific UI quirks (DPI scaling, dark mode)
  
- [ ] Windows OS integration (AC: #2)
  - [ ] Implement Windows taskbar integration
  - [ ] Add system tray icon support
  - [ ] Enable Windows notifications
  - [ ] Support start menu pinning
  - [ ] Implement Windows protocol handler (optional: `sageframe://` URLs)
  
- [ ] Build Windows installer (AC: #1, #4)
  - [ ] Use PyInstaller or cx_Freeze to create standalone executable
  - [ ] Create Windows installer using Inno Setup or WiX
  - [ ] Include all dependencies (Qt DLLs, Python runtime, SQLite)
  - [ ] Sign executable with code signing certificate (optional but recommended)
  
- [ ] CI/CD pipeline for Windows builds (AC: #4)
  - [ ] Add Windows build job to CI pipeline (GitHub Actions or similar)
  - [ ] Automate installer creation
  - [ ] Run tests on Windows environment
  - [ ] Publish installer as build artifact
  
- [ ] Uninstaller implementation (AC: #2)
  - [ ] Create uninstaller script
  - [ ] Clean up AppData files on uninstall (optionally keep user data)
  - [ ] Remove start menu shortcuts
  - [ ] Remove registry entries
  
- [ ] Testing (AC: all)
  - [ ] Test installer on clean Windows 10/11 machines
  - [ ] Test all features on Windows
  - [ ] Test uninstaller
  - [ ] Visual regression tests (Windows-specific UI)

## Dev Notes

### Architecture Compliance

**Platform (from architecture.md):**
- **Windows Desktop First** - Primary target platform
- **PySide6** - Qt framework for cross-platform GUI
- **Python 3.11+** - Runtime requirement

**Build Tools:**
- **PyInstaller** - Recommended for creating standalone executables
- **Inno Setup** - Recommended for creating Windows installers
- **GitHub Actions** - CI/CD pipeline

**Windows Integration:**
- System tray icon for background sync
- Windows notifications for AI suggestions, calendar events
- Start menu integration
- AppData for local storage

### Windows Executable Creation

**Using PyInstaller:**

```bash
# Install PyInstaller
pip install pyinstaller

# Create standalone executable
pyinstaller --name="SageFrame" \
            --windowed \
            --onefile \
            --icon=resources/icon.ico \
            --add-data="resources;resources" \
            src/main.py

# Output: dist/SageFrame.exe
```

**PyInstaller spec file (`sageframe.spec`):**
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources', 'resources')],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'sqlalchemy',
        'alembic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SageFrame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
)
```

### Windows Installer Creation

**Using Inno Setup:**

Create `installer.iss`:
```inno
[Setup]
AppName=SageFrame
AppVersion=1.0.0
DefaultDirName={autopf}\SageFrame
DefaultGroupName=SageFrame
OutputDir=dist
OutputBaseFilename=SageFrame-Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=resources\icon.ico
UninstallDisplayIcon={app}\SageFrame.exe

[Files]
Source: "dist\SageFrame.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\SageFrame"; Filename: "{app}\SageFrame.exe"
Name: "{autodesktop}\SageFrame"; Filename: "{app}\SageFrame.exe"
Name: "{group}\Uninstall SageFrame"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\SageFrame.exe"; Description: "Launch SageFrame"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\SageFrame"
```

**Build installer:**
```bash
iscc installer.iss
# Output: dist/SageFrame-Setup.exe
```

### Windows OS Integration

**System Tray Icon:**
```python
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction

class SystemTrayService:
    def __init__(self, app):
        self.tray_icon = QSystemTrayIcon(QIcon("resources/icon.ico"), app)
        
        # Create context menu
        menu = QMenu()
        show_action = QAction("Show SageFrame", app)
        show_action.triggered.connect(self.show_main_window)
        menu.addAction(show_action)
        
        quit_action = QAction("Quit", app)
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
```

**Windows Notifications:**
```python
from PySide6.QtWidgets import QSystemTrayIcon

def show_notification(title: str, message: str):
    """Show Windows notification."""
    tray_icon.showMessage(
        title,
        message,
        QSystemTrayIcon.Information,
        5000  # Duration in ms
    )
```

### CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/build-windows.yml`:
```yaml
name: Build Windows Installer

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-windows:
    runs-on: windows-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build executable
        run: pyinstaller sageframe.spec
      
      - name: Install Inno Setup
        run: choco install innosetup -y
      
      - name: Build installer
        run: iscc installer.iss
      
      - name: Upload installer
        uses: actions/upload-artifact@v3
        with:
          name: SageFrame-Setup
          path: dist/SageFrame-Setup.exe
```

### Common LLM Mistakes to AVOID

- ❌ Don't forget to include Qt DLLs in PyInstaller build
- ❌ Don't use console window for GUI app (windowed mode)
- ❌ Don't forget icon files for installer and executable
- ❌ Don't hardcode paths - use `os.path.join()` and environment variables
- ❌ Don't forget to test on clean Windows machine (not dev environment)
- ❌ Don't leave debugging console enabled in production build
- ❌ Don't forget to handle Windows-specific paths (`AppData`, `ProgramFiles`)

### References

- [Source: architecture.md#Platform] - Windows Desktop First
- [Source: architecture.md#Technology Stack] - PySide6, Python 3.11+
- [Source: epics.md#Story 6.1 Acceptance Criteria]

## Dev Agent Record

### Agent Model Used
_To be filled by dev agent_

### Completion Notes List
_To be filled by dev agent_

### File List
_To be filled by dev agent_
