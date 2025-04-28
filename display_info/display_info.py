# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DisplayInfo
                                 A QGIS plugin
 This plugin detects objects on selected layer using a YOLO model
 Generated manually
 ***************************************************************************/
"""
import os

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QMetaType
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import (QgsSymbol, QgsProject, QgsRectangle, QgsFeature, QgsGeometry, QgsVectorLayer,
                       QgsField, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat)
import numpy as np
from ultralytics import YOLO

from .display_info_dialog import DisplayInfoDialog


class DisplayInfo:
    def __init__(self, iface):
        """Constructor."""
        self.selectedLayer = None
        self.dlg = None
        self.model_path = None
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DisplayInfo_{}.qm'.format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&Display Info')
        self.first_start = None

    def tr(self, message):
        return QCoreApplication.translate('DisplayInfo', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip:
            action.setStatusTip(status_tip)
        if whats_this:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = ':/plugins/display_info/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Detect objects with model'),
            callback=self.run,
            parent=self.iface.mainWindow())
        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        if self.first_start:
            self.first_start = False
            self.dlg = DisplayInfoDialog()

            self.dlg.toolButton.clicked.connect(self.select_model_path)
            layers = QgsProject.instance().layerTreeRoot().children()
            self.dlg.comboBox.clear()
            self.dlg.comboBox.addItems([layer.name() for layer in layers])

        self.dlg.show()
        result = self.dlg.exec_()

        if result:
            self.model_path = self.dlg.lineEdit.text()
            selected_layer_index = self.dlg.comboBox.currentIndex()
            self.selectedLayer = QgsProject.instance().layerTreeRoot().children()[selected_layer_index].layer()

            self.process_layer()

    def select_model_path(self):
        filename, _ = QFileDialog.getOpenFileName(self.dlg, "Select YOLO Model", "", "*.pt")
        if filename:
            self.dlg.lineEdit.setText(filename)

    def process_layer(self):
        if not self.model_path or not os.path.exists(self.model_path):
            self.iface.messageBar().pushMessage("Error", "Model path is invalid", level=3, duration=5)
            return

        image = self.iface.mapCanvas().grab().toImage()

        width = image.width()
        height = image.height()
        ptr = image.bits()
        ptr.setsize(image.byteCount())

        img_array = np.array(ptr).reshape((height, width, 4))

        img_rgb = img_array[..., :3][..., ::-1]  # RGBA to BGR

        model = YOLO(self.model_path)
        results = model.predict(img_rgb)

        if results[0] is None or len(results[0].boxes) == 0:
            self.iface.messageBar().pushMessage("No objects detected", level=1, duration=3)
            return

        boxes = results[0].boxes

        detection_layer = QgsVectorLayer("Polygon?crs=" + self.selectedLayer.crs().authid(), "Detections", "memory")
        provider = detection_layer.dataProvider()
        confidence_field = QgsField("confidence", QMetaType.Type.Double)
        class_id_field = QgsField("class_id", QMetaType.Type.Int)

        provider.addAttributes([confidence_field, class_id_field])
        detection_layer.updateFields()
        extent = self.iface.mapCanvas().extent()
        features = []
        for i in range(len(boxes)):
            box = boxes[i].xyxy
            box = box.squeeze()
            x_min, y_min, x_max, y_max = box[0].item(), box[1].item(), box[2].item(), box[3].item()

            x1 = extent.xMinimum() + (x_min / width) * extent.width()
            y1 = extent.yMaximum() - (y_min / height) * extent.height()
            x2 = extent.xMinimum() + (x_max / width) * extent.width()
            y2 = extent.yMaximum() - (y_max / height) * extent.height()

            conf = round(boxes[i].conf.item(), 2)
            cls = boxes[i].cls.item()

            rect = QgsRectangle(x1, y1, x2, y2)
            geom = QgsGeometry.fromRect(rect)

            feat = QgsFeature()
            feat.setGeometry(geom)
            feat.setAttributes([conf, cls])
            features.append(feat)

        provider.addFeatures(features)
        detection_layer.updateExtents()

        symbol = QgsSymbol.defaultSymbol(detection_layer.geometryType())
        symbol.setOpacity(0.5)

        renderer = detection_layer.renderer()
        renderer.setSymbol(symbol)

        QgsProject.instance().addMapLayer(detection_layer)

        label_settings = QgsPalLayerSettings()
        label_settings.isExpression = True
        label_settings.fieldName = "confidence || ',class id - ' || class_id"
        label_settings.enabled = True

        text_format = QgsTextFormat()
        text_format.setSize(10)
        text_format.setColor(QColor('black'))
        label_settings.setFormat(text_format)

        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        detection_layer.setLabelsEnabled(True)
        detection_layer.setLabeling(labeling)
        detection_layer.triggerRepaint()

        self.iface.messageBar().pushMessage("Success", f"Detected {len(features)} objects.", level=0, duration=5)
        canvas = self.iface.mapCanvas()
        extent = detection_layer.extent()
        canvas.setExtent(extent)
        canvas.refresh()
