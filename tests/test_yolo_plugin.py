import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from qgis.core import QgsProject, QgsVectorLayer, QgsPointXY
from qgis.PyQt.QtGui import QImage
from yolo_plugin.yolo_plugin import YOLOPlugin

@pytest.fixture
def plugin(qgis_app):
    """Fixture to initialize the plugin with a fully mocked spatial context."""
    iface = MagicMock()
    iface.mainWindow.return_value = None
    
    canvas = iface.mapCanvas()
    canvas.width.return_value = 640
    canvas.height.return_value = 480
    
    # Mock the Extent to prevent geometry collapse (Width/Height must not be 0)
    mock_extent = MagicMock()
    mock_extent.xMinimum.return_value = 0
    mock_extent.xMaximum.return_value = 100
    mock_extent.yMinimum.return_value = 0
    mock_extent.yMaximum.return_value = 100
    mock_extent.width.return_value = 100
    mock_extent.height.return_value = 100
    
    canvas.extent.return_value = mock_extent
    
    return YOLOPlugin(iface)

def test_init_gui(plugin):
    """Verify that actions are added to the QGIS interface."""
    plugin.initGui()
    assert len(plugin.actions) > 0
    plugin.iface.addToolBarIcon.assert_called()
    plugin.iface.addPluginToMenu.assert_called()

@patch('yolo_plugin.yolo_plugin.YOLO')
def test_get_model_caching(mock_yolo, plugin):
    """Verify that YOLO models are cached and not reloaded."""
    model_path = "fake/path/model.pt"
    
    with patch('os.path.exists', return_value=True):
        model1 = plugin.get_model(model_path)
        model2 = plugin.get_model(model_path)
        
    assert model1 == model2
    mock_yolo.assert_called_once_with(model_path)

def test_get_or_create_layer_new(plugin):
    """Test creating a brand new detection layer."""
    plugin.create_new_layer = True
    QgsProject.instance().removeAllMapLayers()
    
    layer = plugin.get_or_create_layer()
    
    assert isinstance(layer, QgsVectorLayer)
    assert layer.name() == "YOLO Detections 1"
    assert layer.fields().at(0).name() == "class"
    assert layer in QgsProject.instance().mapLayers().values()

@patch('yolo_plugin.yolo_plugin.YOLO')
@patch('yolo_plugin.yolo_plugin.YOLOPluginDialog')
def test_detect_objects_logic(mock_dialog, mock_yolo, plugin):
    QgsProject.instance().removeAllMapLayers()
    fake_path = "C:/fake/model.pt"
    
    plugin.models_to_run = [fake_path]
    plugin.conf_threshold = 0.1
    plugin.create_new_layer = True
    plugin.class_colors = {"plane": {"fill": "#ff0000", "outline": "#000000"}}
    plugin.dlg = mock_dialog.return_value
    
    # Force Model Cache to bypass os.path.exists checks
    mock_model = mock_yolo.return_value
    plugin.model_cache[fake_path] = mock_model
    
    mock_conf = MagicMock()
    mock_conf.item.return_value = 0.9
    mock_cls = MagicMock()
    mock_cls.item.return_value = 0
    
    mock_boxes = MagicMock()
    # Coordinates must be within the image width/height (640x480)
    mock_boxes.xyxy = [np.array([100, 100, 200, 200])] 
    mock_boxes.conf = [mock_conf]
    mock_boxes.cls = [mock_cls]
    
    mock_result = MagicMock()
    mock_result.boxes = mock_boxes
    mock_result.names = {0: "plane"}
    mock_model.predict.return_value = [mock_result]

    fake_image = QImage(640, 480, QImage.Format_ARGB32)
    plugin.selectedLayer = MagicMock()

    with patch.object(plugin, 'render_layer_to_image', return_value=fake_image):
        with patch.object(plugin, 'save_layer'): # Prevent Shapefile writing
            plugin.detect_objects()

    layers = QgsProject.instance().mapLayersByName("YOLO Detections 1")
    assert len(layers) > 0, "Layer 'YOLO Detections 1' was not found in project."
    
    detection_layer = layers[0]
    
    count = detection_layer.featureCount()
    assert count == 1, f"Expected 1 feature, but found {count}. Check for NaN geometries."
    
    feature = next(detection_layer.getFeatures())
    assert feature["class"] == "plane"