# -*- coding: utf-8 -*-
"""
/***************************************************************************
 YOLOPluginDialog
                                 A QGIS plugin
 Detect planes, airports, ships, helicopters and oil tankers from satellite imagery using a YOLO model.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2025-04-26
        git sha              : $Format:%H$
        copyright            : (C) 2025 by John doe
        email                : john.doe@email.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from functools import partial

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtWidgets import QColorDialog, QHBoxLayout, QLabel, QPushButton

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "yolo_plugin_dialog_base.ui"))


class YOLOPluginDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(YOLOPluginDialog, self).__init__(parent)
        self.setupUi(self)
        self.class_names = ["airport", "helicopter", "oiltank", "plane", "warship"]
        self.default_colors = {
            "airport": "blue",
            "helicopter": "orange",
            "plane": "yellow",
            "oiltank": "red",
            "warship": "cyan",
        }
        self.color_buttons = {}
        self.populate_color_pickers()
        self.checkBox_fill.stateChanged.connect(self.update_transparency_enabled)
        self.update_transparency_enabled()

    def populate_color_pickers(self):
        for class_name in self.class_names:
            layout = QHBoxLayout()
            label = QLabel(class_name)
            outline_btn = QPushButton()
            fill_btn = QPushButton()

            outline_btn.setStyleSheet(f"background-color: {self.default_colors[class_name]}")
            fill_btn.setStyleSheet(f"background-color: {self.default_colors[class_name]}")

            outline_btn.clicked.connect(partial(self.select_color, class_name, "outline"))
            fill_btn.clicked.connect(partial(self.select_color, class_name, "fill"))

            layout.addWidget(label)
            layout.addWidget(outline_btn)
            layout.addWidget(fill_btn)

            self.verticalLayout_colors.addLayout(layout)
            self.color_buttons[class_name] = {"outline": outline_btn, "fill": fill_btn}

    def select_color(self, class_name, kind):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_buttons[class_name][kind].setStyleSheet(f"background-color: {color.name()}")

    def get_class_colors(self):
        return {
            class_name: {
                "outline": self.color_buttons[class_name]["outline"].palette().button().color().name(),
                "fill": self.color_buttons[class_name]["fill"].palette().button().color().name(),
            }
            for class_name in self.class_names
        }

    def get_confidence_threshold(self):
        return self.spinBox_confidence.value()

    def get_fill_enabled(self):
        return self.checkBox_fill.isChecked()

    def get_fill_transparency(self):
        return self.spinBox_fill_transparency.value()

    def get_outline_transparency(self):
        return self.spinBox_outline_transparency.value()

    def get_create_new_layer(self):
        return self.checkBox_new_layer.isChecked()

    def update_transparency_enabled(self):
        self.spinBox_fill_transparency.setEnabled(self.checkBox_fill.isChecked())
