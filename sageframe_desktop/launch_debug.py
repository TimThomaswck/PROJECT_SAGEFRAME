"""Debug launcher to capture errors"""
import sys
import traceback

try:
    print("Starting application...")
    from app.__main__ import main
    print("Imported main successfully")
    main(enable_updater=False)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")
