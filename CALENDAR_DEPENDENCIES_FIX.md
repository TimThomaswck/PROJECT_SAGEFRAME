# Calendar Dependencies Fix

## Problem
App wouldn't launch due to missing `icalendar` dependency imported at module level in `calendar_view.py`.

## Solution
Made calendar dependencies **optional and lazy-loaded**:

### Changed Dependencies
- `icalendar` - Now loaded only when ICS connection is used
- `requests` - Now loaded only when ICS connection is used  
- `google-auth-*` packages - Now loaded only when OAuth connection is used

### User Experience
1. **App launches without calendar dependencies** - No imports happen at startup
2. **User clicks "Connect via ICS URL"** - App checks if `icalendar` & `requests` are installed
3. **If missing** - Dialog offers to auto-install with one click
4. **Same for OAuth** - Auto-installs Google auth packages when needed

### Technical Implementation
- Removed module-level imports of optional dependencies
- Added `_check_icalendar_dependency()` - Checks & offers to install ICS packages
- Added `_check_google_auth_dependency()` - Checks & offers to install OAuth packages
- Added `_install_packages()` - Runs `pip install` via subprocess
- All calendar methods now use local imports after dependency check

### Benefits
✅ App launches immediately without extra dependencies  
✅ Users only install what they need (ICS OR OAuth, not both)  
✅ One-click installation when features are used  
✅ No manual pip commands required  

### Testing
```bash
# App now launches successfully without any calendar dependencies
python test_launch.py
# ✓ Launches correctly

# When user clicks "Connect via ICS URL":
# → Dialog: "Install icalendar & requests?" [Yes] [No]
# → Auto-installs if user clicks Yes
# → User can then enter ICS URL

# When user clicks "Connect via OAuth":
# → Dialog: "Install google-auth packages?" [Yes] [No]  
# → Auto-installs if user clicks Yes
# → User can then proceed with OAuth setup
```

## Status
✅ **FIXED** - App launches without calendar dependencies, installs them on-demand when features are used.
