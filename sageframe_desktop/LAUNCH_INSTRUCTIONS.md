# SageFrame Desktop Application

## How to Launch the App

### Method 1: Batch Script (Easiest)
Double-click `launch.bat` in Windows Explorer

### Method 2: Command Line
```powershell
cd "c:\Users\LEGION\Documents\PROJECT_SAGEFRAME\sageframe_desktop"
python -m app
```

### Method 3: Test Launcher (with debug output)
```powershell
python test_launch.py
```

## Google Calendar Integration

You have **two options** to connect your Google Calendar:

### Option 1: ICS URL (Simplest - Read-Only)
1. Click **"Connect via ICS URL"** button in the Calendar view
2. Follow the instructions to get your calendar's private ICS link:
   - Go to [Google Calendar](https://calendar.google.com)
   - Settings → Select your calendar → Integrate calendar
   - Copy "Secret address in iCal format"
3. Paste the URL
4. ✅ Done! Events will sync automatically (read-only)

**Pros:** No setup required, works instantly  
**Cons:** Read-only (can't create/edit events from app)

### Option 2: OAuth (Full Access - Read & Write)
1. Click **"Connect via OAuth"** button
2. Follow the setup wizard:
   - Create Google Cloud project
   - Enable Calendar API
   - Create OAuth credentials
   - Download `client_secret.json`
   - Save to: `C:\Users\LEGION\.sageframe\client_secret.json`
3. Click connect again → Browser opens for authentication
4. ✅ Done! Full read/write access

**Pros:** Full access to create/edit events  
**Cons:** Requires initial Google Cloud Console setup

## Troubleshooting

**App won't start?**
- Make sure you're in the correct directory
- Use `python -m app` or `launch.bat`
- Check `test_launch.py` for detailed error messages

**Window not visible?**
- Check taskbar for Python icon
- Try Alt+Tab to find the window
- May be on another monitor if you have multiple displays

**Dependencies missing?**
```powershell
pip install icalendar requests
```

For OAuth support:
```powershell
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```
