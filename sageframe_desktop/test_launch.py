import sys
import traceback
import asyncio

# Verify we're using the correct Python interpreter
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

sys.path.insert(0, '.')

try:
    print("1. Initializing database...")
    from app.database import init_db
    init_db()
    print("   ✓ Database initialized")
    
    print("2. Importing MainWindow...")
    from app.main_window import MainWindow
    print("   ✓ Import successful")
    
    print("3. Importing QApplication from qasync...")
    from qasync import QApplication, QEventLoop
    print("   ✓ QApplication imported")
    
    print("4. Creating QApplication instance...")
    app = QApplication([])
    
    # Load Space Grotesk font
    import os
    from PySide6.QtGui import QFontDatabase
    fonts_path = os.path.join(os.path.dirname(__file__), "app", "resources", "fonts")
    if os.path.exists(fonts_path):
        for file_name in os.listdir(fonts_path):
            if file_name.endswith((".ttf", ".otf")):
                font_file_path = os.path.join(fonts_path, file_name)
                font_id = QFontDatabase.addApplicationFont(font_file_path)
                if font_id == -1:
                    print(f"   ⚠ Failed to load font from {font_file_path}")
                else:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    print(f"   ✓ Loaded font families: {families}")
    
    # Load stylesheet
    qss_path = os.path.join(os.path.dirname(__file__), "app", "resources", "styles", "main.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())
        print("   ✓ Stylesheet loaded")
    
    # Create event loop for async operations
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    print("   ✓ QApplication and event loop created")
    
    print("5. Creating MainWindow...")
    w = MainWindow()
    print("   ✓ MainWindow created")
    
    print("6. Showing window...")
    w.show()
    w.raise_()
    w.activateWindow()
    print("   ✓ Window shown")
    
    print("7. Starting event loop...")
    with loop:
        loop.run_forever()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
    input("\nPress Enter to exit...")
