import sys
import os
import json
import re
from pathlib import Path
import numpy as np
import tempfile
import threading
import wave
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import logging

# Set up logging first
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize global variables
HAS_TTS = False
tts_engine = None
stt_recognizer = None

# Add Kokoro TTS repo to path if it exists
kokoro_path = Path(__file__).parent / "kokoro-tts-repo"
if kokoro_path.exists():
    sys.path.append(str(kokoro_path))

# Initialize TTS
HAS_TTS = False
tts_engine = None

try:
    from kokoro_tts import KokoroTTS
    HAS_TTS = True
    logging.info("Kokoro TTS found and initialized")
except ImportError:
    HAS_TTS = False
    logging.error("Kokoro TTS not found. Voice output will be disabled.")

# Initialize TTS engine if available
if HAS_TTS:
    try:
        logging.info("Initializing Kokoro TTS...")
        from tts_handler import TTSHandler
        tts_handler = TTSHandler()
        logging.info("Kokoro TTS initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Kokoro TTS: {e}")
        HAS_TTS = False

# Then your existing imports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QComboBox, 
                            QLineEdit, QFileDialog, QListWidget, QSplitter,
                            QTextEdit, QScrollArea, QFrame, QDialog, QTabWidget,
                            QDialogButtonBox, QFormLayout, QCheckBox, QMessageBox,
                            QSlider)  # Add QSlider here
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer, QSize, QDateTime
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QIcon, QFont, QFontMetrics
from urllib.parse import quote_plus

# Import components from other files
from ollama_handler import HAS_OLLAMA, OllamaHandler
from ui_components import (AudioVisualizer, NodeCanvas, ConversationPanel, 
                          DARK_BG, DARKER_BG, LIGHT_TEXT, ACCENT_BLUE, 
                          ACCENT_RED, NODE_BG, CONNECTOR_COLOR, GRID_COLOR, 
                          ACCENT_GREEN, HAS_TTS)

# Initialize models (lazy loading)
stt_recognizer = None
tts_engine = None

# Initialize global variables
HAS_TTS = False
tts_engine = None
stt_recognizer = None

# Remove old TTS imports and replace with:
from pathlib import Path
import sys

# Node Dialog for adding/editing nodes
class NodeDialog(QDialog):
    def __init__(self, parent=None, workflow_name=None):
        super().__init__(parent)
        self.parent = parent
        self.workflow_name = workflow_name
        self.setWindowTitle("Add Node")
        self.setMinimumWidth(400)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # Node type selection
        type_layout = QFormLayout()
        self.type_selector = QComboBox()
        self.type_selector.addItems(["start", "intent", "response", "end"])
        self.type_selector.currentTextChanged.connect(self.update_form)
        type_layout.addRow("Node Type:", self.type_selector)
        layout.addLayout(type_layout)
        
        # Node details form
        form_layout = QFormLayout()
        
        # Node ID
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("node_id")
        form_layout.addRow("ID:", self.id_input)
        
        # Node Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Node Title")
        form_layout.addRow("Title:", self.title_input)
        
        # Node Content
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Node content/message")
        form_layout.addRow("Content:", self.content_input)
        
        # Required Entities (for intent nodes)
        self.entities_container = QWidget()
        self.entities_layout = QVBoxLayout(self.entities_container)
        self.entities_layout.setContentsMargins(0, 0, 0, 0)
        
        self.add_entity_btn = QPushButton("Add Required Entity")
        self.add_entity_btn.clicked.connect(self.add_entity_field)
        self.entities_layout.addWidget(self.add_entity_btn)
        
        form_layout.addRow("Required Entities:", self.entities_container)
        
        # Outputs
        self.outputs_container = QWidget()
        self.outputs_layout = QVBoxLayout(self.outputs_container)
        self.outputs_layout.setContentsMargins(0, 0, 0, 0)
        
        self.add_output_btn = QPushButton("Add Output")
        self.add_output_btn.clicked.connect(self.add_output_field)
        self.outputs_layout.addWidget(self.add_output_btn)
        
        form_layout.addRow("Outputs:", self.outputs_container)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Initialize form based on default type
        self.update_form(self.type_selector.currentText())
        
    def update_form(self, node_type):
        # Hide/show form elements based on node type
        if node_type == "start":
            self.entities_container.setVisible(False)
        elif node_type == "intent":
            self.entities_container.setVisible(True)
        elif node_type == "response":
            self.entities_container.setVisible(False)
        elif node_type == "end":
            self.entities_container.setVisible(False)
            
        # End nodes don't have outputs
        self.outputs_container.setVisible(node_type != "end")
        
    def add_entity_field(self):
        entity_input = QLineEdit()
        entity_input.setPlaceholderText("Entity name (e.g., account_type)")
        
        entity_layout = QHBoxLayout()
        entity_layout.addWidget(entity_input)
        
        remove_btn = QPushButton("×")
        remove_btn.setFixedWidth(30)
        remove_btn.setProperty("id", "redButton")
        remove_btn.clicked.connect(lambda: self.remove_field(entity_layout))
        entity_layout.addWidget(remove_btn)
        
        self.entities_layout.insertLayout(self.entities_layout.count() - 1, entity_layout)
        
    def add_output_field(self):
        output_input = QLineEdit()
        output_input.setPlaceholderText("Output node ID")
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(output_input)
        
        remove_btn = QPushButton("×")
        remove_btn.setFixedWidth(30)
        remove_btn.setProperty("id", "redButton")
        remove_btn.clicked.connect(lambda: self.remove_field(output_layout))
        output_layout.addWidget(remove_btn)
        
        self.outputs_layout.insertLayout(self.outputs_layout.count() - 1, output_layout)
        
    def remove_field(self, layout):
        # Remove all widgets from layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Remove layout itself
        self.entities_layout.removeItem(layout)
        self.outputs_layout.removeItem(layout)
        
    def get_node_data(self):
        node_type = self.type_selector.currentText()
        node_id = self.id_input.text() or f"node_{len(self.parent.nodes) + 1}"
        
        # Get required entities
        required_entities = []
        for i in range(self.entities_layout.count() - 1):  # Exclude the add button
            layout_item = self.entities_layout.itemAt(i)
            if layout_item and layout_item.layout():
                layout = layout_item.layout()
                entity_input = layout.itemAt(0).widget()
                if entity_input and entity_input.text():
                    required_entities.append(entity_input.text())
        
        # Get outputs
        outputs = []
        for i in range(self.outputs_layout.count() - 1):  # Exclude the add button
            layout_item = self.outputs_layout.itemAt(i)
            if layout_item and layout_item.layout():
                layout = layout_item.layout()
                output_input = layout.itemAt(0).widget()
                if output_input and output_input.text():
                    outputs.append(output_input.text())
        
        # Create node data
        node_data = {
            'id': node_id,
            'type': node_type,
            'title': self.title_input.text() or node_id,
            'content': self.content_input.toPlainText(),
            'position': {'x': 100, 'y': 100}
        }
        
        if node_type == 'intent':
            node_data['required_entities'] = required_entities
            
        if node_type != 'end':
            node_data['outputs'] = outputs
            
        return node_data

# New Workflow Dialog
class NewWorkflowDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Workflow")
        self.setMinimumWidth(300)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        form_layout.addRow("Workflow Name:", self.name_input)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

# Node Editor for designing workflow
class NodeEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.nodes = []
        self.edges = []
        self.selected_node = None
        self.dragging = False
        self.drag_start = QPointF()
        self.creating_edge = False
        self.temp_edge_start = None
        self.temp_edge_end = None
        self.temp_edge_output = None
        self.workflow_name = ""
        
        self.initUI()
        
    def initUI(self):
        self.setMouseTracking(True)  # Enable mouse tracking for hover effects
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add toolbar for node operations
        toolbar = QWidget()
        toolbar.setMaximumHeight(50)
        toolbar.setStyleSheet(f"background-color: {DARKER_BG};")
        toolbar_layout = QHBoxLayout(toolbar)
        
        self.add_node_btn = QPushButton("Add Node")
        self.add_node_btn.clicked.connect(self.add_node_dialog)
        toolbar_layout.addWidget(self.add_node_btn)
        
        self.add_edge_btn = QPushButton("Add Connection")
        self.add_edge_btn.clicked.connect(self.start_edge_creation)
        toolbar_layout.addWidget(self.add_edge_btn)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setProperty("id", "redButton")
        self.delete_btn.clicked.connect(self.delete_selected)
        toolbar_layout.addWidget(self.delete_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setProperty("id", "redButton")
        self.clear_btn.clicked.connect(self.clear)
        toolbar_layout.addWidget(self.clear_btn)
        
        # Properties button
        self.properties_btn = QPushButton("Edit Properties")
        self.properties_btn.clicked.connect(self.edit_node_properties)
        toolbar_layout.addWidget(self.properties_btn)
        
        layout.addWidget(toolbar)
        
        # Add canvas for node editing
        self.canvas = NodeCanvas(self)
        layout.addWidget(self.canvas, 1)
        
    def add_node_dialog(self):
        dialog = NodeDialog(self, self.parent.current_workflow)
        if dialog.exec():
            node_data = dialog.get_node_data()
            self.add_node(node_data)
            
    def add_node(self, node_data):
        self.nodes.append(node_data)
        self.canvas.update()
        
    def start_edge_creation(self):
        self.creating_edge = True
        self.canvas.setCursor(Qt.CursorShape.CrossCursor)
        
    def delete_selected(self):
        if self.selected_node:
            # Remove all edges connected to this node
            self.edges = [edge for edge in self.edges if edge['from'] != self.selected_node['id'] and edge['to'] != self.selected_node['id']]
            
            # Remove the node
            self.nodes = [node for node in self.nodes if node['id'] != self.selected_node['id']]
            self.selected_node = None
            self.canvas.update()
            
    def clear(self):
        self.nodes = []
        self.edges = []
        self.selected_node = None
        self.canvas.update()
        
    def save_to_dict(self):
        return {
            'nodes': self.nodes.copy(),
            'edges': self.edges.copy()
        }
        
    def load_from_dict(self, data):
        self.nodes = data.get('nodes', []).copy()
        self.edges = data.get('edges', []).copy()
        self.selected_node = None
        self.canvas.update()
        
    def edit_node_properties(self):
        if not self.selected_node:
            QMessageBox.information(self, "No Node Selected", "Please select a node to edit its properties.")
            return
            
        dialog = NodeDialog(self, self.workflow_name)
        
        # Pre-fill dialog with node data
        dialog.id_input.setText(self.selected_node.get('id', ''))
        dialog.id_input.setEnabled(False)  # Don't allow changing ID
        dialog.title_input.setText(self.selected_node.get('title', ''))
        dialog.content_input.setText(self.selected_node.get('content', ''))
        dialog.type_selector.setCurrentText(self.selected_node.get('type', 'default'))
        dialog.type_selector.setEnabled(False)  # Don't allow changing type
        
        # Add entity fields
        required_entities = self.selected_node.get('required_entities', [])
        if required_entities:
            for entity in required_entities:
                dialog.add_entity_field()
                layout_item = dialog.entities_layout.itemAt(dialog.entities_layout.count() - 2)  # Skip add button
                if layout_item and layout_item.layout():
                    entity_input = layout_item.layout().itemAt(0).widget()
                    if entity_input:
                        entity_input.setText(entity)
        
        # Add output fields
        outputs = self.selected_node.get('outputs', [])
        if outputs:
            for output in outputs:
                dialog.add_output_field()
                layout_item = dialog.outputs_layout.itemAt(dialog.outputs_layout.count() - 2)  # Skip add button
                if layout_item and layout_item.layout():
                    output_input = layout_item.layout().itemAt(0).widget()
                    if output_input:
                        output_input.setText(output)
        
        if dialog.exec():
            updated_data = dialog.get_node_data()
            
            # Preserve the node ID and type
            updated_data['id'] = self.selected_node['id']
            updated_data['type'] = self.selected_node['type']
            
            # Preserve position
            updated_data['position'] = self.selected_node['position']
            
            # Update node data
            for i, node in enumerate(self.nodes):
                if node['id'] == self.selected_node['id']:
                    self.nodes[i] = updated_data
                    self.selected_node = updated_data
                    break
                    
            self.canvas.update()

# Settings Panel
class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # AI Settings
        ai_frame = QFrame()
        ai_frame.setFrameShape(QFrame.Shape.StyledPanel)
        ai_layout = QFormLayout(ai_frame)
        
        # Ollama model
        self.ollama_model = QComboBox()
        
        if HAS_OLLAMA:
            try:
                # Get available models
                import ollama
                models = ollama.list()
                model_names = [model['name'] for model in models.get('models', [])]
                self.ollama_model.addItems(model_names)
            except:
                self.ollama_model.addItems(["llama3", "mistral", "phi3"])
        else:
            self.ollama_model.addItems(["llama3", "mistral", "phi3"])
            self.ollama_model.setEnabled(False)
            
        ai_layout.addRow("Ollama Model:", self.ollama_model)
        
        # API settings
        self.api_url = QLineEdit("http://localhost:11434")
        ai_layout.addRow("Ollama API URL:", self.api_url)
        
        # Temperature slider
        temperature_layout = QHBoxLayout()
        self.temperature_label = QLabel("0.7")
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setMinimum(0)
        self.temperature_slider.setMaximum(100)
        self.temperature_slider.setValue(70)  # Default to 0.7
        self.temperature_slider.valueChanged.connect(self.update_temperature)
        
        temperature_layout.addWidget(QLabel("Temperature:"))
        temperature_layout.addWidget(self.temperature_slider)
        temperature_layout.addWidget(self.temperature_label)
        
        ai_layout.addRow("Generation:", temperature_layout)
        
        layout.addWidget(ai_frame)
        
        # Voice Settings
        voice_frame = QFrame()
        voice_frame.setFrameShape(QFrame.Shape.StyledPanel)
        voice_layout = QFormLayout(voice_frame)
        
        # TTS Voice selection
        self.tts_voice = QComboBox()
        
        if HAS_TTS:
            self.tts_voice.addItems(["default", "female", "male"])
        else:
            self.tts_voice.addItems(["default", "female", "male"])
            self.tts_voice.setEnabled(False)
            
        voice_layout.addRow("TTS Voice:", self.tts_voice)
        
        # Speech recognition model
        self.stt_model = QComboBox()
        self.stt_model.addItems(["Google", "Whisper"])
        
        if not HAS_TTS:
            self.stt_model.setEnabled(False)
            
        voice_layout.addRow("STT Model:", self.stt_model)
        
        # Enable TTS and STT options
        self.enable_tts = QCheckBox("Enable Text-to-Speech")
        self.enable_tts.setChecked(HAS_TTS)
        self.enable_tts.setEnabled(HAS_TTS)
        voice_layout.addRow("", self.enable_tts)
        
        self.enable_stt = QCheckBox("Enable Speech Recognition")
        self.enable_stt.setChecked(True)
        voice_layout.addRow("", self.enable_stt)
        
        layout.addWidget(voice_frame)
        
        # Appearance Settings
        appearance_frame = QFrame()
        appearance_frame.setFrameShape(QFrame.Shape.StyledPanel)
        appearance_layout = QFormLayout(appearance_frame)
        
        # Dark/Light mode toggle
        self.dark_mode = QCheckBox("Dark Mode")
        self.dark_mode.setChecked(True)
        appearance_layout.addRow("", self.dark_mode)
        
        layout.addWidget(appearance_frame)
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        
        # Add spacer at bottom
        layout.addStretch()
        
    def update_temperature(self, value):
        """Update temperature label when slider is moved"""
        temp = value / 100.0
        self.temperature_label.setText(f"{temp:.2f}")
        
    def save_settings(self):
        """Save settings"""
        # This would normally save to a config file
        # For this demo, we'll just show a message
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")

# Workflow Test Panel
class WorkflowTestPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # Test configuration
        config_frame = QFrame()
        config_frame.setFrameShape(QFrame.Shape.StyledPanel)
        config_layout = QFormLayout(config_frame)
        
        # AI model selection
        self.model_selector = QComboBox()
        self.model_selector.addItems(["llama3", "mistral", "phi3"])
        config_layout.addRow("AI Model:", self.model_selector)
        
        # Test method
        self.test_method = QComboBox()
        self.test_method.addItems(["Step by Step", "Full Conversation"])
        config_layout.addRow("Test Method:", self.test_method)
        
        # Sample user inputs
        self.sample_inputs = QTextEdit()
        self.sample_inputs.setPlaceholderText("Enter sample user inputs, one per line")
        config_layout.addRow("Sample Inputs:", self.sample_inputs)
        
        # Entity values for testing
        self.entity_values = QTextEdit()
        self.entity_values.setPlaceholderText("Enter test entity values in format: entity_name=value, one per line")
        config_layout.addRow("Entity Values:", self.entity_values)
        
        layout.addWidget(config_frame)
        
        # Test execution buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        # Analyze workflow button
        analyze_btn = QPushButton("Analyze Workflow")
        analyze_btn.clicked.connect(self.analyze_workflow)
        button_layout.addWidget(analyze_btn)
        
        # Run test button
        test_btn = QPushButton("Run Test")
        test_btn.setProperty("id", "greenButton")
        test_btn.clicked.connect(self.run_test)
        button_layout.addWidget(test_btn)
        
        layout.addWidget(button_frame)
        
        # Test results area
        results_label = QLabel("Test Results")
        results_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(results_label)
        
        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)
        self.results_area.setStyleSheet(f"background-color: {DARKER_BG}; border: 1px solid #333;")
        layout.addWidget(self.results_area, 1)
# Add this method to your WorkflowTestPanel class in workflow_manager_final.py
# Insert it right after the initUI method

    def log_result(self, message, level="info"):
        """Log a message to the results area with formatting based on level"""
        if level == "header":
            html = f'<h2 style="color: {ACCENT_BLUE};">{message}</h2>'
        elif level == "subheader":
            html = f'<h3 style="color: {ACCENT_GREEN};">{message}</h3>'
        elif level == "success":
            html = f'<div style="color: {ACCENT_GREEN};">{message}</div>'
        elif level == "warning":
            html = f'<div style="color: #FFA500;">{message}</div>'
        elif level == "error":
            html = f'<div style="color: {ACCENT_RED};">{message}</div>'
        else:  # info
            html = f'<div>{message}</div>'
            
        self.results_area.insertHtml(html)
        self.results_area.insertHtml("<br>")
        
        # Scroll to bottom
        scrollbar = self.results_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def analyze_workflow(self):
        if not self.parent.current_workflow:
            self.log_result("No workflow selected. Please select a workflow first.", "error")
            return
            
        workflow_data = self.parent.workflows.get(self.parent.current_workflow, {})
        
        # Clear previous results
        self.results_area.clear()
        
        # Basic analysis
        nodes = workflow_data.get('nodes', [])
        edges = workflow_data.get('edges', [])
        
        self.log_result(f"# Workflow Analysis: {self.parent.current_workflow}", "header")
        self.log_result(f"## Overview", "subheader")
        self.log_result(f"Total nodes: {len(nodes)}", "info")
        self.log_result(f"Total connections: {len(edges)}", "info")
        
        # Node type breakdown
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
            
        self.log_result("## Node Types", "subheader")
        for node_type, count in node_types.items():
            self.log_result(f"{node_type}: {count}", "info")
            
        # Check for starting nodes
        start_nodes = [node for node in nodes if node.get('type') == 'start']
        if not start_nodes:
            self.log_result("⚠️ No start node found", "warning")
        elif len(start_nodes) > 1:
            self.log_result(f"⚠️ Multiple start nodes found: {len(start_nodes)}", "warning")
            
        # Check for end nodes
        end_nodes = [node for node in nodes if node.get('type') == 'end']
        if not end_nodes:
            self.log_result("⚠️ No end node found", "warning")
            
        # Check for disconnected nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge['from'])
            connected_nodes.add(edge['to'])
            
        disconnected = [node['id'] for node in nodes if node['id'] not in connected_nodes]
        if disconnected:
            self.log_result("## Disconnected Nodes", "subheader")
            for node_id in disconnected:
                self.log_result(f"- {node_id}", "warning")
                
        # Check for circular references
        self.log_result("## Path Analysis", "subheader")
        start_ids = [node['id'] for node in start_nodes]
        end_ids = [node['id'] for node in end_nodes]
        
        if start_ids and end_ids:
            for start_id in start_ids:
                paths_to_end = self.find_paths(start_id, end_ids, edges)
                if paths_to_end:
                    self.log_result(f"✅ Path exists from start '{start_id}' to end node(s)", "success")
                    self.log_result(f"Shortest path length: {min(len(p) for p in paths_to_end)}", "info")
                else:
                    self.log_result(f"⚠️ No path from start '{start_id}' to any end node", "warning")
                    
            # Check for loops
            loops = self.find_loops(edges)
            if loops:
                self.log_result(f"Found {len(loops)} potential loops in workflow", "warning")
                
        # Check intent nodes for required entities
        intent_nodes = [node for node in nodes if node.get('type') == 'intent']
        self.log_result("## Intent Nodes", "subheader")
        
        for node in intent_nodes:
            required_entities = node.get('required_entities', [])
            if not required_entities:
                self.log_result(f"Node '{node['id']}' has no required entities", "info")
            else:
                self.log_result(f"Node '{node['id']}' requires: {', '.join(required_entities)}", "info")
                
    def find_paths(self, start, ends, edges, path=None, visited=None):
        if path is None:
            path = []
        if visited is None:
            visited = set()
            
        path = path + [start]
        visited.add(start)
        
        if start in ends:
            return [path]
            
        paths = []
        for edge in edges:
            if edge['from'] == start and edge['to'] not in visited:
                new_paths = self.find_paths(edge['to'], ends, edges, path, visited.copy())
                paths.extend(new_paths)
                
        return paths
        
    def find_loops(self, edges):
        # Simple loop detection
        loops = []
        for edge in edges:
            if edge['from'] == edge['to']:
                loops.append([edge['from']])
                continue
                
            # Check for paths that lead back to the source
            for check_edge in edges:
                if check_edge['from'] == edge['to'] and check_edge['to'] == edge['from']:
                    loops.append([edge['from'], edge['to']])
                    
        return loops
        
    def run_test(self):
        if not self.parent.current_workflow:
            self.log_result("No workflow selected. Please select a workflow first.", "error")
            return
            
        workflow_data = self.parent.workflows.get(self.parent.current_workflow, {})
        
        # Clear previous results
        self.results_area.clear()
        
        self.log_result(f"# Test Results: {self.parent.current_workflow}", "header")
        
        # Parse entity values
        entity_values = {}
        for line in self.entity_values.toPlainText().strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                entity_values[key.strip()] = value.strip()
        
        # Parse sample inputs
        sample_inputs = [line.strip() for line in self.sample_inputs.toPlainText().strip().split('\n') if line.strip()]
        
        # Get model and test method
        model = self.model_selector.currentText()
        test_method = self.test_method.currentText()
        
        # Find starting node
        start_node = next((node for node in workflow_data.get('nodes', []) if node.get('type') == 'start'), None)
        
        if not start_node:
            self.log_result("No start node found in the workflow.", "error")
            return
            
        self.log_result(f"Using model: {model}", "info")
        self.log_result(f"Test method: {test_method}", "info")
        
        if entity_values:
            self.log_result("## Test Entity Values", "subheader")
            for entity, value in entity_values.items():
                self.log_result(f"{entity} = {value}", "info")
                
        # Step-by-step test
        if test_method == "Step by Step":
            self.run_step_by_step_test(start_node, workflow_data, entity_values, sample_inputs, model)
        else:
            self.run_full_conversation_test(start_node, workflow_data, entity_values, sample_inputs, model)
            
    def run_step_by_step_test(self, start_node, workflow_data, entity_values, sample_inputs, model):
        """Run a step-by-step test of the workflow"""
        self.log_result("\n## Step-by-Step Test", "header")
        
        current_node = start_node
        conversation = []
        extracted_entities = {}
        
        # Initialize with start node content
        self.log_result(f"\nStarting at node: {current_node['id']}", "info")
        self.log_result(f"Bot: {current_node['content']}", "info")
        
        # Process each sample input
        for input_text in sample_inputs:
            self.log_result(f"\nUser: {input_text}", "info")
            
            # Extract entities if current node is intent type
            if (current_node['type'] == 'intent'):
                required_entities = current_node.get('required_entities', [])
                if required_entities:
                    new_entities = OllamaHandler.extract_entities_for_test(input_text, required_entities, model)
                    extracted_entities.update(new_entities)
                    
                    if new_entities:
                        self.log_result("Extracted entities:", "info")
                        for entity, value in new_entities.items():
                            self.log_result(f"- {entity}: {value}", "info")
                    
                    # Check if all required entities are present
                    missing = [e for e in required_entities if e not in extracted_entities]
                    if missing:
                        self.log_result(f"⚠️ Missing required entities: {', '.join(missing)}", "warning")
                        continue
            
            # Add to conversation history
            conversation.append({"role": "user", "content": input_text})
            
            # Get next node
            outputs = current_node.get('outputs', [])
            if not outputs:
                if current_node['type'] == 'end':
                    self.log_result("\n✅ Reached end node", "success")
                else:
                    self.log_result("\n⚠️ Dead end: Node has no outputs", "warning")
                break
            
            # Predict next node
            next_node_id = OllamaHandler.predict_next_node(current_node, input_text, workflow_data, model, conversation)
            next_node = next((node for node in workflow_data['nodes'] if node['id'] == next_node_id), None)
            
            if not next_node:
                self.log_result(f"\n❌ Error: Could not find next node {next_node_id}", "error")
                break
            
            # Log transition
            self.log_result(f"\nTransitioning to node: {next_node['id']}", "info")
            
            # Update current node
            current_node = next_node
            
            # Format and log node content
            content = current_node['content']
            for entity, value in extracted_entities.items():
                content = content.replace(f"{{{entity}}}", value)
            
            self.log_result(f"Bot: {content}", "info")
            conversation.append({"role": "assistant", "content": content})
            
            # Check if we've reached an end node
            if current_node['type'] == 'end':
                self.log_result("\n✅ Reached end node", "success")
                break
        
        # Summary
        self.log_result("\n## Test Summary", "header")
        self.log_result(f"Total steps: {len(conversation) // 2}", "info")
        self.log_result(f"Extracted entities: {json.dumps(extracted_entities, indent=2)}", "info")
        if current_node['type'] == 'end':
            self.log_result("Test completed successfully", "success")
        else:
            self.log_result("Test ended before reaching end node", "warning")

    def create_sample_workflows(self):
        # Sample workflow 1: Simple greeting
        greeting_workflow = {
            'nodes': [
                {
                    'id': 'start',
                    'type': 'start',
                    'title': 'Greeting',
                    'content': 'Hello! How can I help you today?',
                    'position': {'x': 100, 'y': 100},
                    'outputs': ['intent_help', 'intent_account']
                },
                {
                    'id': 'intent_help',
                    'type': 'intent',
                    'title': 'Help Request',
                    'content': 'I can help you with several things. What specifically do you need help with?',
                    'position': {'x': 400, 'y': 50},
                    'outputs': ['response_help']
                },
                {
                    'id': 'intent_account',
                    'type': 'intent',
                    'title': 'Account Request',
                    'content': 'I see you want to manage your account. What would you like to do?',
                    'position': {'x': 400, 'y': 200},
                    'required_entities': ['account_type'],
                    'outputs': ['end_node']
                },
                {
                    'id': 'response_help',
                    'type': 'response',
                    'title': 'Help Response',
                    'content': 'Here is some helpful information for you.',
                    'position': {'x': 700, 'y': 50},
                    'outputs': ['end_node']
                },
                {
                    'id': 'end_node',
                    'type': 'end',
                    'title': 'End Conversation',
                    'content': 'Thank you for using our service. Is there anything else I can help with?',
                    'position': {'x': 700, 'y': 200}
                }
            ],
            'edges': [
                {'from': 'start', 'to': 'intent_help', 'label': 'help intent'},
                {'from': 'start', 'to': 'intent_account', 'label': 'account intent'},
                {'from': 'intent_help', 'to': 'response_help', 'label': 'help response'},
                {'from': 'intent_account', 'to': 'end_node', 'label': 'end'},
                {'from': 'response_help', 'to': 'end_node', 'label': 'end'}
            ]
        }
        
        # Add sample workflows to available workflows
        self.workflows["Sample Greeting"] = greeting_workflow
        
        # Update workflow selector
        self.workflow_selector.addItems(self.workflows.keys())
        self.current_workflow = "Sample Greeting"
        
        # Load initial workflow
        self.load_selected_workflow()
        
    def new_workflow(self):
        """Create a new workflow"""
        dialog = NewWorkflowDialog(self)
        if dialog.exec():
            name = dialog.name_input.text()
            if not name:
                name = f"Workflow {len(self.workflows) + 1}"
                
            # Check for duplicate names
            if name in self.workflows:
                i = 1
                while f"{name} ({i})" in self.workflows:
                    i += 1
                name = f"{name} ({i})"
                
            # Create empty workflow
            self.workflows[name] = {'nodes': [], 'edges': []}
            
            # Add to selector and select
            self.workflow_selector.addItem(name)
            self.workflow_selector.setCurrentText(name)

    def save_workflow(self):
        """Save current workflow to file"""
        if not self.current_workflow:
            QMessageBox.warning(self, "No Workflow", "No workflow selected.")
            return
            
        # Get current data from editor
        self.workflows[self.current_workflow] = self.node_editor.save_to_dict()
        
        # Show file dialog
        filename, _ = QFileDialog.getSaveFileName(self, "Save Workflow", "", "JSON Files (*.json)")
        if not filename:
            return
            
        # Ensure it has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
            
        try:
            with open(filename, 'w') as f:
                json.dump(self.workflows[self.current_workflow], f, indent=2)
                
            self.statusBar().showMessage(f"Workflow saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error Saving", f"Error saving workflow: {e}")
            
    def load_workflow(self):
        """Load workflow from file"""
        filename, _ = QFileDialog.getOpenFileName(self, "Load Workflow", "", "JSON Files (*.json)")
        if not filename:
            return
            
        try:
            with open(filename, 'r') as f:
                workflow_data = json.load(f)
                
            # Generate name based on filename
            name = Path(filename).stem
            
            # Check for duplicate names
            if name in self.workflows:
                i = 1
                while f"{name} ({i})" in self.workflows:
                    i += 1
                name = f"{name} ({i})"
                
            # Add to workflows
            self.workflows[name] = workflow_data
            
            # Add to selector and select
            self.workflow_selector.addItem(name)
            self.workflow_selector.setCurrentText(name)
            
            self.statusBar().showMessage(f"Workflow loaded from {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error Loading", f"Error loading workflow: {e}")
                
    def load_selected_workflow(self):
        """Load workflow data into editor"""
        if not self.workflow_selector.currentText():
            return
            
        self.current_workflow = self.workflow_selector.currentText()
        workflow_data = self.workflows.get(self.current_workflow, {'nodes': [], 'edges': []})
        
        # Set workflow name in editor
        self.node_editor.workflow_name = self.current_workflow
        
        # Load data
        self.node_editor.load_from_dict(workflow_data)
        
        # Update status bar
        self.statusBar().showMessage(f"Loaded workflow: {self.current_workflow}")

class ConversationalAgentIVR(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conversational Agent IVR")
        self.setMinimumSize(1200, 800)
        
        # Initialize TTS if available
        self.tts_engine = None
        global HAS_TTS, tts_engine
        
        if HAS_TTS:
            try:
                logger.info("Initializing F5-TTS engine...")
                # Initialize with default device selection
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.tts_engine = F5TTS(
                    model="F5TTS_v1_Base",
                    device=device,
                    use_ema=True,
                    hf_cache_dir=None  # Will use default HF cache
                )
                tts_engine = self.tts_engine
                logger.info(f"F5-TTS engine initialized successfully on {device}")
            except Exception as e:
                logger.error(f"Failed to initialize F5-TTS engine: {str(e)}")
                HAS_TTS = False
        else:
            logger.info("F5-TTS not available, skipping initialization")
        
        # Initialize state
        self.workflows = {}
        self.current_workflow = None
        self.is_listening = False
        
        self.initUI()
        
        # Create sample workflows
        self.create_sample_workflows()
        
    def initUI(self):
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Toolbar with workflow controls
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        
        # Workflow selector
        self.workflow_selector = QComboBox()
        self.workflow_selector.currentTextChanged.connect(self.load_selected_workflow)
        toolbar_layout.addWidget(QLabel("Current Workflow:"))
        toolbar_layout.addWidget(self.workflow_selector)
        
        # Workflow management buttons
        new_btn = QPushButton("New Workflow")
        new_btn.clicked.connect(self.new_workflow)
        toolbar_layout.addWidget(new_btn)
        
        save_btn = QPushButton("Save Workflow")
        save_btn.clicked.connect(self.save_workflow)
        toolbar_layout.addWidget(save_btn)
        
        load_btn = QPushButton("Load Workflow")
        load_btn.clicked.connect(self.load_workflow)
        toolbar_layout.addWidget(load_btn)
        
        layout.addWidget(toolbar)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Node editor
        self.node_editor = NodeEditor(self)
        splitter.addWidget(self.node_editor)
        
        # Right side: Testing and conversation
        right_panel = QTabWidget()
        
        # Add test panel
        self.test_panel = WorkflowTestPanel(self)
        right_panel.addTab(self.test_panel, "Test Workflow")
        
        # Add conversation panel
        conversation_tab = QWidget()
        conversation_layout = QVBoxLayout(conversation_tab)
        
        # Add audio visualizer
        self.audio_visualizer = AudioVisualizer()
        conversation_layout.addWidget(self.audio_visualizer)
        
        # Add speech text display
        self.speech_text = QLabel()
        self.speech_text.setWordWrap(True)
        self.speech_text.setStyleSheet(f"background-color: {DARKER_BG}; padding: 10px;")
        conversation_layout.addWidget(self.speech_text)
        
        # Add conversation panel
        self.conversation_panel = ConversationPanel(self)
        conversation_layout.addWidget(self.conversation_panel)
        
        right_panel.addTab(conversation_tab, "Live Conversation")
        
        # Add settings panel
        self.settings_panel = SettingsPanel(self)
        right_panel.addTab(self.settings_panel, "Settings")
        
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([600, 600])
        
        layout.addWidget(splitter)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #121212;
                color: #F0F0F0;
            }
            QPushButton {
                background-color: #1E1E1E;
                border: 1px solid #333;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2E2E2E;
            }
            QPushButton[id="redButton"] {
                background-color: #FF3366;
                color: white;
            }
            QPushButton[id="greenButton"] {
                background-color: #00CC66;
                color: white;
            }
            QComboBox, QLineEdit {
                background-color: #1E1E1E;
                border: 1px solid #333;
                padding: 5px;
            }
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #333;
            }
        """)

    def load_selected_workflow(self):
        """Load workflow data into editor"""
        if not self.workflow_selector.currentText():
            return
            
        self.current_workflow = self.workflow_selector.currentText()
        workflow_data = self.workflows.get(self.current_workflow, {'nodes': [], 'edges': []})
        
        # Set workflow name in editor
        self.node_editor.workflow_name = self.current_workflow
        
        # Load data
        self.node_editor.load_from_dict(workflow_data)
        
        # Update status bar
        self.statusBar().showMessage(f"Loaded workflow: {self.current_workflow}")

    def new_workflow(self):
        """Create a new workflow"""
        dialog = NewWorkflowDialog(self)
        if dialog.exec():
            name = dialog.name_input.text()
            if not name:
                name = f"Workflow {len(self.workflows) + 1}"
                
            # Check for duplicate names
            if name in self.workflows:
                i = 1
                while f"{name} ({i})" in self.workflows:
                    i += 1
                name = f"{name} ({i})"
                
            # Create empty workflow
            self.workflows[name] = {'nodes': [], 'edges': []}
            
            # Add to selector and select
            self.workflow_selector.addItem(name)
            self.workflow_selector.setCurrentText(name)

    def create_sample_workflows(self):
        # Sample workflow 1: Simple greeting
        greeting_workflow = {
            'nodes': [
                {
                    'id': 'start',
                    'type': 'start',
                    'title': 'Greeting',
                    'content': 'Hello! How can I help you today?',
                    'position': {'x': 100, 'y': 100},
                    'outputs': ['intent_help', 'intent_account']
                },
                {
                    'id': 'intent_help',
                    'type': 'intent',
                    'title': 'Help Request',
                    'content': 'I can help you with several things. What specifically do you need help with?',
                    'position': {'x': 400, 'y': 50},
                    'outputs': ['response_help']
                },
                {
                    'id': 'intent_account',
                    'type': 'intent',
                    'title': 'Account Request',
                    'content': 'I see you want to manage your account. What would you like to do?',
                    'position': {'x': 400, 'y': 200},
                    'required_entities': ['account_type'],
                    'outputs': ['end_node']
                },
                {
                    'id': 'response_help',
                    'type': 'response',
                    'title': 'Help Response',
                    'content': 'Here is some helpful information for you.',
                    'position': {'x': 700, 'y': 50},
                    'outputs': ['end_node']
                },
                {
                    'id': 'end_node',
                    'type': 'end',
                    'title': 'End Conversation',
                    'content': 'Thank you for using our service. Is there anything else I can help with?',
                    'position': {'x': 700, 'y': 200}
                }
            ],
            'edges': [
                {'from': 'start', 'to': 'intent_help', 'label': 'help intent'},
                {'from': 'start', 'to': 'intent_account', 'label': 'account intent'},
                {'from': 'intent_help', 'to': 'response_help', 'label': 'help response'},
                {'from': 'intent_account', 'to': 'end_node', 'label': 'end'},
                {'from': 'response_help', 'to': 'end_node', 'label': 'end'}
            ]
        }
        
        # Add sample workflows to available workflows
        self.workflows["Sample Greeting"] = greeting_workflow
        
        # Update workflow selector
        self.workflow_selector.addItems(self.workflows.keys())
        self.current_workflow = "Sample Greeting"
        
        # Load initial workflow
        self.load_selected_workflow()

    def save_workflow(self):
        """Save current workflow to file"""
        if not self.current_workflow:
            QMessageBox.warning(self, "No Workflow", "No workflow selected.")
            return
            
        # Get current data from editor
        self.workflows[self.current_workflow] = self.node_editor.save_to_dict()
        
        # Show file dialog
        filename, _ = QFileDialog.getSaveFileName(self, "Save Workflow", "", "JSON Files (*.json)")
        if not filename:
            return
            
        # Ensure it has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
            
        try:
            with open(filename, 'w') as f:
                json.dump(self.workflows[self.current_workflow], f, indent=2)
                
            self.statusBar().showMessage(f"Workflow saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error Saving", f"Error saving workflow: {e}")
            
    def load_workflow(self):
        """Load workflow from file"""
        filename, _ = QFileDialog.getOpenFileName(self, "Load Workflow", "", "JSON Files (*.json)")
        if not filename:
            return
            
        try:
            with open(filename, 'r') as f:
                workflow_data = json.load(f)
                
            # Generate name based on filename
            name = Path(filename).stem
            
            # Check for duplicate names
            if name in self.workflows:
                i = 1
                while f"{name} ({i})" in self.workflows:
                    i += 1
                name = f"{name} ({i})"
                
            # Add to workflows
            self.workflows[name] = workflow_data
            
            # Add to selector and select
            self.workflow_selector.addItem(name)
            self.workflow_selector.setCurrentText(name)
            
            self.statusBar().showMessage(f"Workflow loaded from {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error Loading", f"Error loading workflow: {e}")
                
    def load_selected_workflow(self):
        """Load workflow data into editor"""
        if not self.workflow_selector.currentText():
            return
            
        self.current_workflow = self.workflow_selector.currentText()
        workflow_data = self.workflows.get(self.current_workflow, {'nodes': [], 'edges': []})
        
        # Set workflow name in editor
        self.node_editor.workflow_name = self.current_workflow
        
        # Load data
        self.node_editor.load_from_dict(workflow_data)
        
        # Update status bar
        self.statusBar().showMessage(f"Loaded workflow: {self.current_workflow}")

    # Main function to run the application
def main():
    app = QApplication(sys.argv)
    window = ConversationalAgentIVR()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
