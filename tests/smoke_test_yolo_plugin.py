import os
import pytest
import numpy as np
from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer, QgsRectangle
from qgis.PyQt.QtGui import QImage
from unittest.mock import MagicMock, patch
from yolo_plugin.yolo_plugin import YOLOPlugin

@pytest.fixture
def real_data_plugin(qgis_app):
    """Initializes plugin with a mocked iface but real project data."""
    iface = MagicMock()

    iface.mapCanvas().extent.return_value = QgsRectangle(0, 0, 1000, 1000)
    iface.mapCanvas().width.return_value = 640
    iface.mapCanvas().height.return_value = 480
    
    return YOLOPlugin(iface)

def test_detect_objects_with_real_model(real_data_plugin):
    """
    Test using a real .pt model and a real image loaded into QgsProject.
    """

    base_path = os.path.dirname(__file__)
    model_path = os.path.join(base_path, "data", "DOTANA_no_ships_yolo12x.pt")
    image_path = os.path.join(base_path, "data", "test_image.png")

    if not os.path.exists(model_path) or not os.path.exists(image_path):
        raise FileNotFoundError(
            f"\nMissing required test data in {base_path}/data.\n"
            "PLEASE MANUALLY DOWNLOAD MODEL: Place 'DOTANA_no_ships_yolo12x.pt' and 'test_image.png' "
            "into the tests/data/ directory before running this suite."
        )

    QgsProject.instance().removeAllMapLayers()
    raster_layer = QgsRasterLayer(image_path, "Test Image")
    QgsProject.instance().addMapLayer(raster_layer)
    
    # Configure Plugin to use real data
    real_data_plugin.selectedLayer = raster_layer
    real_data_plugin.models_to_run = [model_path]
    real_data_plugin.conf_threshold = 0.25
    real_data_plugin.create_new_layer = True
    real_data_plugin.class_colors = {"plane": {"fill": "#ff0000", "outline": "#000000"}}
    
    # Mock the Dialog UI calls that the logic expects
    real_data_plugin.dlg = MagicMock()
    real_data_plugin.dlg.get_fill_enabled.return_value = True
    real_data_plugin.dlg.get_fill_transparency.return_value = 0
    real_data_plugin.dlg.get_outline_transparency.return_value = 0

    # Use a real QImage from the file to simulate map rendering
    # This bypasses the need for a visible MapCanvas
    real_image = QImage(image_path)
    
    # Only patch 'render_layer_to_image' to return our real file-based QImage
    with patch.object(real_data_plugin, 'render_layer_to_image', return_value=real_image):
        with patch.object(real_data_plugin, 'save_layer'):
            real_data_plugin.detect_objects()

    yolo_layers = [l for l in QgsProject.instance().mapLayers().values() if "YOLO Detections" in l.name()]
    assert len(yolo_layers) > 0
    
    result_layer = yolo_layers[0]
    print(f"\nDetected {result_layer.featureCount()} objects.")
    
    assert result_layer.featureCount() >= 0