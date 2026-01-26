import asyncio
import os
import sys

from PySide6.QtCore import QTranslator, QLocale, QLockFile, Qt
from PySide6.QtGui import QFontDatabase, QGuiApplication
from qasync import QApplication, run

from app.builtin.gitlab_updater import GitlabUpdater
from app.builtin.locale import detect_system_ui_language
from app.main_window import MainWindow
# from qdarktheme import enable_hi_dpi


def enable_hi_dpi():
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


async def task():
    app_close_event = asyncio.Event()
    app = QApplication.instance()
    assert isinstance(app, QApplication)
    app.aboutToQuit.connect(app_close_event.set)

    main_window = MainWindow()
    main_window.show()
    await main_window.async_init()
    await app_close_event.wait()


def main(enable_updater: bool = True):
    updater = GitlabUpdater()
    updater.base_url = "https://gitlab.mikumikumi.xyz"
    updater.project_name = "Timothy/sageframe"
    updater.is_enable = enable_updater

    lock_file = QLockFile("App.lock")
    if not lock_file.lock():
        sys.exit(0)

    if os.path.exists("updater.json"):
        updater.load_from_file_and_override("updater.json")

    # enable hdpi (must be BEFORE QApplication)
    enable_hi_dpi()

    # init QApplication (must come BEFORE QFontDatabase, most GUI stuff)
    app = QApplication(sys.argv)

    # Load custom fonts (NOW it's safe)
    fonts_path = os.path.join(os.path.dirname(__file__), "resources", "fonts")
    if os.path.exists(fonts_path):
        for file_name in os.listdir(fonts_path):
            if file_name.endswith((".ttf", ".otf")):
                font_file_path = os.path.join(fonts_path, file_name)
                if QFontDatabase.addApplicationFont(font_file_path) == -1:
                    print(f"Warning: Failed to load font from {font_file_path}", file=sys.stderr)

    # i18n
    translator = QTranslator()
    lang_code = detect_system_ui_language()
    translator.load(f":/i18n/{lang_code}.qm")
    app.installTranslator(translator)

    # keep a reference so it doesn't get GC'ed
    app._translator = translator

    # Load and apply QSS stylesheet
    qss_path = os.path.join(os.path.dirname(__file__), "resources", "styles", "main.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: main.qss not found at {qss_path}", file=sys.stderr)
    
    # Initialize database (create tables if they don't exist)
    from app.database import init_db
    init_db()

    # start event loop
    try:
        run(task())
    except Exception as e:
        print(f"An error occurred during application startup: {e}", file=sys.stderr)
        sys.exit(1)


def main_no_updater():
    main(enable_updater=False)


def run_module():
    main()


if __name__ == "__main__":
    main_no_updater()