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
