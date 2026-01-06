import pytest
from unittest.mock import patch
from qgis.PyQt.QtCore import Qt
from  yolo_plugin.yolo_plugin_dialog import YOLOPluginDialog

@pytest.fixture
def dialog(qtbot):
    """Fixture to initialize the dialog for each test."""
    test_dialog = YOLOPluginDialog()
    test_dialog.show() # Necessary for some UI events to trigger
    qtbot.addWidget(test_dialog)
    return test_dialog

def test_initial_state(dialog):
    """Verify default UI states upon opening."""
    assert dialog.lineEdit_model2.isEnabled() is False
    assert dialog.toolButton_model2.isEnabled() is False
    assert dialog.spinBox_fill_transparency.isEnabled() == dialog.checkBox_fill.isChecked()

def test_toggle_multiple_models(dialog, qtbot):
    """Test that checking 'Run Multiple' enables the second model inputs."""
    qtbot.mouseClick(dialog.checkBox_run_multiple, Qt.LeftButton)
    
    assert dialog.lineEdit_model2.isEnabled() is True
    assert dialog.toolButton_model2.isEnabled() is True
    assert dialog.get_run_multiple() is True

    qtbot.mouseClick(dialog.checkBox_run_multiple, Qt.LeftButton)
    assert dialog.lineEdit_model2.isEnabled() is False

def test_fill_transparency_logic(dialog):
    """Test that the fill transparency spinbox enables/disables correctly."""
    dialog.checkBox_fill.setChecked(True)
    assert dialog.spinBox_fill_transparency.isEnabled() is True

    dialog.checkBox_fill.setChecked(False)
    assert dialog.spinBox_fill_transparency.isEnabled() is False

def test_get_confidence_threshold(dialog):
    """Verify the spinbox value retrieval."""
    dialog.spinBox_confidence.setValue(0.75)
    assert dialog.get_confidence_threshold() == 0.75

@patch('qgis.PyQt.QtWidgets.QFileDialog.getOpenFileName')
def test_select_model_path(mock_file_dialog, dialog, qtbot):
    """Test that selecting a file updates the lineEdit."""
    mock_file_dialog.return_value = ("/path/to/model.pt", "All Files (*)")
    
    qtbot.mouseClick(dialog.toolButton_model1, Qt.LeftButton)
    
    assert dialog.lineEdit_model1.text() == "/path/to/model.pt"

def test_populate_color_pickers(dialog):
    """Check if all classes from the list are created in the UI."""
    for class_name in ["airport", "helicopter", "oiltank", "plane", "warship", "ship"]:
        assert class_name in dialog.color_buttons
        assert "outline" in dialog.color_buttons[class_name]
        assert "fill" in dialog.color_buttons[class_name]

        