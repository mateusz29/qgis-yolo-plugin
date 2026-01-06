import os
import pytest
from qgis.core import QgsApplication

@pytest.fixture(scope="session", autouse=True)
def qgis_app():
    """Initializes the QgsApplication with the correct prefix."""
    # This path(system specific) is where QGIS is installed
    prefix = r"C:\Program Files\QGIS 3.40.4\apps\qgis-ltr"
    
    # Required for Windows to find plugins correctly in headless mode
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    app = QgsApplication([], False)
    app.setPrefixPath(prefix, True)
    app.initQgis()
    
    yield app
    
    app.exitQgis()