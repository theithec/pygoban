from PyQt6.QtWidgets import QSpinBox

from pygoban.gui.settingsdialog import SettingsDialog


class TestMainWindow:
    def test_main_window_initialization(self, main_window):
        """Test MainWindow initializes correctly"""
        assert main_window.windowTitle() == "Pygoban"
        assert main_window.minimumSize().width() == 1060
        assert main_window.minimumSize().height() == 600
        assert main_window.tabs is not None
        assert main_window.tabs.tabsClosable() is True
        assert main_window.startwidget is not None

    def test_main_window_has_welcome_tab(self, main_window):
        """Test MainWindow shows welcome tab when no SGF path provided"""
        assert main_window.tabs.count() == 1
        assert main_window.tabs.tabText(0) == "Welcome"

    def test_close_tab_functionality(self, main_window, qt_app):
        """Test tab closing functionality"""
        initial_count = main_window.tabs.count()
        # Simulate tab close request
        main_window.close_tab(0)
        assert main_window.tabs.count() == initial_count - 1

    def test_add_game_dialog(self, main_window, qt_app):
        """Test add game dialog functionality"""
        # This should not raise an exception
        main_window.show_add_game_dialog()
        qt_app.processEvents()  # Allow dialog to appear

    def test_edit_board_dialog(self, main_window, qt_app):
        """Test edit board dialog functionality"""
        # This should not raise an exception
        main_window.show_edit_board_dialog()
        qt_app.processEvents()  # Allow dialog to appear

    def test_settings_dialog(self, main_window, qt_app):
        """Test settings dialog functionality"""
        # This should not raise an exception
        main_window.show_settings_dialog()
        qt_app.processEvents()  # Allow dialog to appear

    def test_analysis_variation_interval_setting(self, main_window):
        dialog = SettingsDialog(main_window)
        widget = dialog.elems["analysis_variation_interval_ms"]
        assert isinstance(widget, QSpinBox)
        assert widget.value() == 180

        class MemorySettings:
            def __init__(self):
                self.values = {}

            def setValue(self, name, value):
                self.values[name] = value

            def sync(self):
                pass

        dialog.qsettings = MemorySettings()
        widget.setValue(420)
        dialog.save()

        assert main_window.settings.analysis_variation_interval_ms == 420
        assert dialog.qsettings.values["analysis/variation_interval_ms"] == 420
