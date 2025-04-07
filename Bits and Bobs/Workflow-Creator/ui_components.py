import os
import threading
import re
import tempfile
import wave
import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QComboBox, QLineEdit, QFrame, QTextEdit, 
                           QFormLayout, QScrollArea, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QPointF, QRectF, QDateTime
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QFont, QFontMetrics, QLinearGradient

import speech_recognition as sr

# Import from ollama_handler
from ollama_handler import HAS_OLLAMA, OllamaHandler

# Constants for appearance
DARK_BG = "#121212"
DARKER_BG = "#0A0A0A"
LIGHT_TEXT = "#F0F0F0"
ACCENT_BLUE = "#00AAFF"
ACCENT_RED = "#FF3366"
NODE_BG = "#1E1E1E"
CONNECTOR_COLOR = "#00FFFF"
GRID_COLOR = "#232323"
ACCENT_GREEN = "#00CC66"

# Optional: Check for TTS capabilities
try:
    from TTS.api import TTS
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    print("TTS not found. Voice output will be disabled.")

# Initialize models (lazy loading)
stt_recognizer = None
tts_engine = None

# Audio Visualizer component
class AudioVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.levels = [0.1] * 20
        self.setStyleSheet(f"background-color: {DARKER_BG};")
        
    def update_levels(self, levels):
        self.levels = levels
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        bar_width = width / (len(self.levels) * 2)
        
        # Create gradient from blue to red
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(ACCENT_RED))
        gradient.setColorAt(0.5, QColor(ACCENT_BLUE))
        gradient.setColorAt(1, QColor(CONNECTOR_COLOR))
        
        for i, level in enumerate(self.levels):
            # Calculate bar height based on level
            bar_height = height * level
            
            # Draw bar with rounded corners
            x = i * bar_width * 2 + bar_width / 2
            y = height - bar_height
            
            rect = QRectF(x, y, bar_width, bar_height)
            
            # Create path with rounded corners for bars
            path = QPainterPath()
            path.addRoundedRect(rect, 3, 3)
            
            painter.fillPath(path, gradient)
        
        # Add a subtle glow effect
        painter.setPen(QPen(QColor(ACCENT_BLUE), 1, Qt.PenStyle.SolidLine))
        for i, level in enumerate(self.levels):
            bar_height = height * level
            x = i * bar_width * 2 + bar_width / 2
            y = height - bar_height
            
            rect = QRectF(x, y, bar_width, bar_height)
            painter.drawRoundedRect(rect, 3, 3)

# Node Canvas for drawing workflow
class NodeCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setMinimumSize(800, 600)
        self.node_radius = 100
        self.connector_radius = 10
        self.grid_size = 20
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw grid
        self.draw_grid(painter)
        
        # Draw edges
        self.draw_edges(painter)
        
        # Draw nodes
        self.draw_nodes(painter)
        
        # Draw temporary edge if creating one
        if self.parent.creating_edge and self.parent.temp_edge_start:
            self.draw_temp_edge(painter)
            
    def draw_grid(self, painter):
        # Fill background
        painter.fillRect(self.rect(), QColor(DARKER_BG))
        
        # Draw grid lines
        painter.setPen(QPen(QColor(GRID_COLOR), 1, Qt.PenStyle.DotLine))
        
        # Vertical lines
        for x in range(0, self.width(), self.grid_size):
            painter.drawLine(x, 0, x, self.height())
            
        # Horizontal lines
        for y in range(0, self.height(), self.grid_size):
            painter.drawLine(0, y, self.width(), y)
            
    def draw_nodes(self, painter):
        for node in self.parent.nodes:
            # Get node position and convert to integers
            x = int(node['position']['x'])
            y = int(node['position']['y'])
            node_type = node.get('type', 'default')
            
            # Set colors based on node type
            if node_type == 'start':
                bg_color = QColor(ACCENT_GREEN)
                border_color = QColor("#FFFFFF")
            elif node_type == 'end':
                bg_color = QColor(ACCENT_RED)
                border_color = QColor("#FFFFFF")
            elif node_type == 'intent':
                bg_color = QColor(ACCENT_BLUE)
                border_color = QColor("#FFFFFF")
            else:
                bg_color = QColor(NODE_BG)
                border_color = QColor(CONNECTOR_COLOR)
                
            # Draw node shadow for depth effect
            is_selected = self.parent.selected_node and self.parent.selected_node['id'] == node['id']
            if is_selected:
                shadow_color = QColor(ACCENT_BLUE)
                shadow_color.setAlpha(100)
                painter.setBrush(QBrush(shadow_color))
                painter.setPen(Qt.PenStyle.NoPen)
                shadow_rect = QRectF(x + 5, y + 5, 200, 100)
                painter.drawRoundedRect(shadow_rect, 10, 10)
            
            # Draw node background with integer coordinates
            node_rect = QRectF(x, y, 200, 100)
            
            # Create gradient background
            gradient = QLinearGradient(x, y, x, y + 100)
            gradient.setColorAt(0, bg_color.lighter(110))
            gradient.setColorAt(1, bg_color)
            
            painter.setBrush(QBrush(gradient))
            pen_width = 2 if is_selected else 1
            painter.setPen(QPen(border_color, pen_width))
            painter.drawRoundedRect(node_rect, 10, 10)
            
            # Draw node title with integer coordinates
            title = node.get('title', node.get('id', 'Node'))
            painter.setPen(QColor(LIGHT_TEXT))
            painter.setFont(QFont('Arial', 10, QFont.Weight.Bold))
            title_rect = QRectF(x + 10, y + 5, 180, 30)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft, title)
            
            # Draw node content preview with integer coordinates
            content = node.get('content', '')
            if len(content) > 40:
                content = content[:37] + '...'
            painter.setFont(QFont('Arial', 8))
            content_rect = QRectF(x + 10, y + 40, 180, 30)
            painter.drawText(content_rect, Qt.AlignmentFlag.AlignLeft, content)
            
            # Draw connection points with integer coordinates
            painter.setBrush(QBrush(QColor(CONNECTOR_COLOR)))
            painter.setPen(QPen(QColor("#FFFFFF"), 1))
            
            # Input connector
            if node_type != 'start':
                painter.drawEllipse(QPointF(x, y + 50), self.connector_radius, self.connector_radius)
            
            # Output connectors
            outputs = node.get('outputs', [])
            output_count = len(outputs)
            
            if output_count > 0 and node_type != 'end':
                # Single output
                if output_count == 1:
                    painter.drawEllipse(QPointF(x + 200, y + 50), self.connector_radius, self.connector_radius)
                # Multiple outputs
                else:
                    for i, output in enumerate(outputs):
                        output_y = y + 30 + ((i + 1) * 100) // (output_count + 1)
                        painter.drawEllipse(QPointF(x + 200, output_y), self.connector_radius, self.connector_radius)
            
    def draw_edges(self, painter):
        for edge in self.parent.edges:
            # Find source and target nodes
            source_node = next((n for n in self.parent.nodes if n['id'] == edge['from']), None)
            target_node = next((n for n in self.parent.nodes if n['id'] == edge['to']), None)
            
            if not source_node or not target_node:
                continue
                
            # Get source and target positions
            source_x = source_node['position']['x'] + 200  # Right side of source
            source_y = source_node['position']['y'] + 50   # Middle of source
            
            target_x = target_node['position']['x']       # Left side of target
            target_y = target_node['position']['y'] + 50  # Middle of target
            
            # Handle multiple outputs from source
            outputs = source_node.get('outputs', [])
            if len(outputs) > 1:
                output_index = outputs.index(edge['to']) if edge['to'] in outputs else 0
                source_y = source_node['position']['y'] + 30 + ((output_index + 1) * 100) // (len(outputs) + 1)
            
            # Draw edge as bezier curve
            path = QPainterPath()
            path.moveTo(source_x, source_y)
            
            # Control points for bezier curve
            ctrl1_x = source_x + (target_x - source_x) * 0.4
            ctrl1_y = source_y
            ctrl2_x = target_x - (target_x - source_x) * 0.4
            ctrl2_y = target_y
            
            path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, target_x, target_y)
            
            # Draw edge with glow effect
            painter.setPen(QPen(QColor(CONNECTOR_COLOR), 2, Qt.PenStyle.SolidLine))
            painter.drawPath(path)
            
            # Draw arrow at end
            arrow_size = 10
            angle = np.arctan2(target_y - ctrl2_y, target_x - ctrl2_x)
            
            arrow_p1 = QPointF(target_x - arrow_size * np.cos(angle - np.pi/6),
                              target_y - arrow_size * np.sin(angle - np.pi/6))
            arrow_p2 = QPointF(target_x - arrow_size * np.cos(angle + np.pi/6),
                              target_y - arrow_size * np.sin(angle + np.pi/6))
            
            arrow_path = QPainterPath()
            arrow_path.moveTo(target_x, target_y)
            arrow_path.lineTo(arrow_p1)
            arrow_path.lineTo(arrow_p2)
            arrow_path.closeSubpath()
            
            painter.fillPath(arrow_path, QBrush(QColor(CONNECTOR_COLOR)))
            
            # Draw edge label
            if 'label' in edge:
                label_x = (source_x + target_x) / 2
                label_y = (source_y + target_y) / 2 - 15
                
                # Background for label
                text_metrics = QFontMetrics(QFont('Arial', 8))
                text_width = text_metrics.horizontalAdvance(edge['label'])
                text_height = text_metrics.height()
                
                label_rect = QRectF(label_x - text_width/2 - 5, label_y - text_height/2 - 5, 
                                   text_width + 10, text_height + 10)
                
                painter.setBrush(QBrush(QColor(NODE_BG)))
                painter.setPen(QPen(QColor(CONNECTOR_COLOR), 1))
                painter.drawRoundedRect(label_rect, 5, 5)
                
                # Draw label text
                painter.setPen(QColor(LIGHT_TEXT))
                painter.setFont(QFont('Arial', 8))
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, edge['label'])
    
    def draw_temp_edge(self, painter):
        if not self.parent.temp_edge_start or not self.parent.temp_edge_end:
            return
            
        source_x, source_y = self.parent.temp_edge_start
        target_x, target_y = self.parent.temp_edge_end
        
        # Draw temporary edge similar to normal edges but with dashed line
        path = QPainterPath()
        path.moveTo(source_x, source_y)
        
        # Control points for bezier curve
        ctrl1_x = source_x + (target_x - source_x) * 0.4
        ctrl1_y = source_y
        ctrl2_x = target_x - (target_x - source_x) * 0.4
        ctrl2_y = target_y
        
        path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, target_x, target_y)
        
        painter.setPen(QPen(QColor(CONNECTOR_COLOR), 2, Qt.PenStyle.DashLine))
        painter.drawPath(path)

    def mousePressEvent(self, event):
        # Check if clicked on a node
        for node in self.parent.nodes:
            x = node['position']['x']
            y = node['position']['y']
            
            node_rect = QRectF(x, y, 200, 100)
            if node_rect.contains(event.position()):
                self.parent.selected_node = node
                self.parent.dragging = True
                self.parent.drag_start = event.position()
                self.update()
                return
                
        # If creating edge, check if clicked on output connector
        if self.parent.creating_edge:
            for node in self.parent.nodes:
                x = node['position']['x']
                y = node['position']['y']
                
                # Skip end nodes as sources for edges
                if node.get('type') == 'end':
                    continue
                    
                outputs = node.get('outputs', [])
                
                # Single output
                if len(outputs) == 1:
                    output_point = QPointF(x + 200, y + 50)
                    if (output_point - event.position()).manhattanLength() < self.connector_radius * 2:
                        self.parent.temp_edge_start = (output_point.x(), output_point.y())
                        self.parent.temp_edge_end = (event.position().x(), event.position().y())
                        return
                
                # Multiple outputs
                else:
                    for i, output in enumerate(outputs):
                        output_y = y + 30 + ((i + 1) * 100) // (len(outputs) + 1)
                        output_point = QPointF(x + 200, output_y)
                        
                        if (output_point - event.position()).manhattanLength() < self.connector_radius * 2:
                            self.parent.temp_edge_start = (output_point.x(), output_point.y())
                            self.parent.temp_edge_end = (event.position().x(), event.position().y())
                            self.parent.temp_edge_output = output
                            return
        
        # Clear selection if clicked elsewhere
        self.parent.selected_node = None
        self.update()
        
    def mouseMoveEvent(self, event):
        if self.parent.dragging and self.parent.selected_node:
            # Calculate delta movement
            delta_x = event.position().x() - self.parent.drag_start.x()
            delta_y = event.position().y() - self.parent.drag_start.y()
            
            # Update node position
            self.parent.selected_node['position']['x'] += delta_x
            self.parent.selected_node['position']['y'] += delta_y
            
            # Update drag start point
            self.parent.drag_start = event.position()
            self.update()
            
        elif self.parent.creating_edge and self.parent.temp_edge_start:
            self.parent.temp_edge_end = (event.position().x(), event.position().y())
            self.update()
            
    def mouseReleaseEvent(self, event):
        self.parent.dragging = False
        
        # Handle edge creation
        if self.parent.creating_edge and self.parent.temp_edge_start:
            # Check if released on an input connector
            for node in self.parent.nodes:
                x = node['position']['x']
                y = node['position']['y']
                
                # Skip start nodes as targets for edges
                if node.get('type') == 'start':
                    continue
                    
                input_point = QPointF(x, y + 50)
                if (input_point - event.position()).manhattanLength() < self.connector_radius * 2:
                    # Find source node
                    for source_node in self.parent.nodes:
                        sx = source_node['position']['x']
                        sy = source_node['position']['y']
                        
                        outputs = source_node.get('outputs', [])
                        
                        if len(outputs) == 1:
                            output_point = QPointF(sx + 200, sy + 50)
                            if (output_point.x(), output_point.y()) == self.parent.temp_edge_start:
                                # Create new edge
                                self.parent.edges.append({
                                    'from': source_node['id'],
                                    'to': node['id'],
                                    'label': 'transition'
                                })
                                break
                        else:
                            for i, output in enumerate(outputs):
                                output_y = sy + 30 + ((i + 1) * 100) // (len(outputs) + 1)
                                output_point = QPointF(sx + 200, output_y)
                                
                                if (output_point.x(), output_point.y()) == self.parent.temp_edge_start:
                                    # Create new edge with the right output
                                    self.parent.edges.append({
                                        'from': source_node['id'],
                                        'to': node['id'],
                                        'label': 'transition',
                                        'output': self.parent.temp_edge_output
                                    })
                                    break
            
            # Reset temp edge
            self.parent.temp_edge_start = None
            self.parent.temp_edge_end = None
            self.parent.temp_edge_output = None
            self.parent.creating_edge = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()

# Conversation Panel for live interaction
from tts_handler import TTSHandler

class ConversationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.tts_handler = TTSHandler()
        self.current_node = None
        self.conversation_history = []
        self.entities = {}  # Extracted entities
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # Conversation log
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(f"background-color: {DARKER_BG}; border: 1px solid #333;")
        layout.addWidget(self.log_area, 3)
        
        # Input area
        input_frame = QFrame()
        input_frame.setFrameShape(QFrame.Shape.StyledPanel)
        input_frame.setStyleSheet(f"background-color: {DARKER_BG}; border: 1px solid #333;")
        input_layout = QHBoxLayout(input_frame)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        voice_button = QPushButton("🎤")
        voice_button.setFixedWidth(40)
        voice_button.clicked.connect(self.toggle_voice_input)
        input_layout.addWidget(voice_button)
        
        layout.addWidget(input_frame)
        
        # Control buttons
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        start_button = QPushButton("Start Conversation")
        start_button.setProperty("id", "greenButton")
        start_button.clicked.connect(self.start_conversation)
        control_layout.addWidget(start_button)
        
        reset_button = QPushButton("Reset")
        reset_button.setProperty("id", "redButton")
        reset_button.clicked.connect(self.reset_conversation)
        control_layout.addWidget(reset_button)
        
        layout.addWidget(control_frame)
        
    def log_message(self, message, is_user=False, is_system=False, is_error=False):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        
        if is_system:
            if is_error:
                color = ACCENT_RED
                prefix = "🔴 SYSTEM"
            else:
                color = ACCENT_GREEN
                prefix = "🟢 SYSTEM"
        elif is_user:
            color = ACCENT_BLUE
            prefix = "👤 YOU"
        else:
            color = CONNECTOR_COLOR
            prefix = "🤖 BOT"
            
            # Update audio visualizer text if parent has one
            if hasattr(self.parent, 'speech_text'):
                self.parent.speech_text.setText(message)
            
            # Start TTS if available
            if HAS_TTS:
                threading.Thread(target=self.speak_message, args=(message,)).start()
        
        html = f'<div style="margin: 5px 0"><span style="color: {color}; font-weight: bold;">[{timestamp}] {prefix}:</span> {message}</div>'
        self.log_area.insertHtml(html)
        
        # Scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def start_conversation(self):
        if not self.parent.current_workflow:
            self.log_message("No workflow selected. Please select or create a workflow first.", is_system=True, is_error=True)
            return
            
        if not self.parent.workflows.get(self.parent.current_workflow):
            self.log_message(f"Workflow '{self.parent.current_workflow}' not found.", is_system=True, is_error=True)
            return
            
        workflow_data = self.parent.workflows[self.parent.current_workflow]
        
        # Find the start node
        start_node = next((node for node in workflow_data.get('nodes', []) if node.get('type') == 'start'), None)
        
        if not start_node:
            self.log_message("No start node found in the workflow.", is_system=True, is_error=True)
            return
            
        # Reset conversation state
        self.reset_conversation()
        
        # Set current node and display its content
        self.current_node = start_node
        
        # Format content with any entity placeholders
        message = self.format_node_content(start_node.get('content', ''))
        self.log_message(message)
        
    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return
            
        self.log_message(message, is_user=True)
        self.input_field.clear()
        
        # Process user input
        self.process_user_input(message)
        
    def process_user_input(self, message):
        if not self.current_node:
            self.log_message("No active conversation. Please start a conversation first.", is_system=True)
            return
            
        workflow_data = self.parent.workflows.get(self.parent.current_workflow, {})
        
        # Store user input in conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Process based on current node type
        node_type = self.current_node.get('type')
        
        if node_type == 'intent':
            # Extract required entities
            required_entities = self.current_node.get('required_entities', [])
            
            if required_entities:
                # Use Ollama to extract entities if available
                if HAS_OLLAMA:
                    extracted = OllamaHandler.extract_entities_with_ollama(message, required_entities)
                    self.entities.update(extracted)
                else:
                    # Simple entity extraction using keywords
                    self.extract_entities_simple(message, required_entities)
                    
                # Check if all required entities are extracted
                missing_entities = [entity for entity in required_entities if entity not in self.entities]
                
                if missing_entities:
                    # Ask for missing entity
                    self.log_message(f"Could you please provide your {missing_entities[0]}?")
                    return
            
            # All entities extracted, proceed to next node
            self.proceed_to_next_node(message)
        elif node_type == 'start':
            # Start nodes typically determine branch based on content
            self.proceed_to_next_node(message)
        else:
            # For other node types, just proceed
            self.proceed_to_next_node(message)
            
    def extract_entities_simple(self, message, required_entities):
        # Very basic entity extraction
        for entity in required_entities:
            # Look for patterns like "entity: value" or "entity is value"
            patterns = [
                rf"{entity}:\s*(\w+)",
                rf"{entity} is (\w+)",
                rf"my {entity} is (\w+)",
                rf"(\w+) for {entity}"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    self.entities[entity] = match.group(1)
                    break
                    
    def proceed_to_next_node(self, message):
        if not self.current_node:
            return
            
        workflow_data = self.parent.workflows.get(self.parent.current_workflow, {})
        
        # Find possible transitions
        outputs = self.current_node.get('outputs', [])
        
        if not outputs:
            # End of conversation
            if self.current_node.get('type') == 'end':
                # Format content with any entity placeholders
                content = self.format_node_content(self.current_node.get('content', ''))
                self.log_message(content)
                
                # Reset conversation
                self.current_node = None
                self.log_message("Conversation ended.", is_system=True)
            return
            
        # Find next node based on intent classification
        if HAS_OLLAMA:
            next_node_id = OllamaHandler.classify_intent_with_ollama(message, outputs, workflow_data)
        else:
            # Simple keyword matching
            next_node_id = self.classify_intent_simple(message, outputs)
            
        if not next_node_id:
            # Use first output as default
            next_node_id = outputs[0]
            
        # Find the edge with transition label
        edge = None
        for e in workflow_data.get('edges', []):
            if e['from'] == self.current_node['id'] and e['to'] == next_node_id:
                edge = e
                break
                
        # Log transition if found
        if edge and 'label' in edge:
            self.log_message(f"Transition: {edge['label']}", is_system=True)
            
        # Find next node
        next_node = next((node for node in workflow_data.get('nodes', []) if node.get('id') == next_node_id), None)
        
        if next_node:
            self.current_node = next_node
            
            # Format content with any entity placeholders
            content = self.format_node_content(next_node.get('content', ''))
            self.log_message(content)
            
            # If end node, reset conversation
            if next_node.get('type') == 'end':
                self.current_node = None
        else:
            self.log_message(f"Node '{next_node_id}' not found in workflow.", is_system=True, is_error=True)
            
    def classify_intent_simple(self, message, outputs):
        workflow_data = self.parent.workflows.get(self.parent.current_workflow, {})
        
        # Get possible next nodes
        next_nodes = []
        for output in outputs:
            node = next((n for n in workflow_data.get('nodes', []) if n.get('id') == output), None)
            if node:
                next_nodes.append(node)
                
        if not next_nodes:
            return outputs[0] if outputs else None
            
        # Simple keyword matching
        max_score = -1
        best_node_id = None
        
        for node in next_nodes:
            score = 0
            content = node.get('content', '').lower()
            title = node.get('title', '').lower()
            
            # Check for keywords in user message
            keywords = (content + ' ' + title).split()
            for keyword in keywords:
                if len(keyword) > 3 and keyword.lower() in message.lower():
                    score += 1
                    
            if score > max_score:
                max_score = score
                best_node_id = node.get('id')
                
        return best_node_id if max_score > 0 else outputs[0]
        
    def format_node_content(self, content):
        # Replace entity placeholders with actual values
        for entity, value in self.entities.items():
            content = content.replace(f"{{{entity}}}", value)
            
        return content
        
    def toggle_voice_input(self):
        self.parent.is_listening = not self.parent.is_listening
        
        if self.parent.is_listening:
            self.log_message("Voice input activated. Speak now...", is_system=True)
            threading.Thread(target=self.listen_for_speech).start()
        else:
            self.log_message("Voice input deactivated.", is_system=True)
            
    def listen_for_speech(self):
        """Enhanced speech recognition with better noise handling and continuous listening"""
        global stt_recognizer
        
        # Initialize speech recognition if needed
        if not stt_recognizer:
            stt_recognizer = sr.Recognizer()
            # Improve noise handling
            stt_recognizer.dynamic_energy_threshold = True
            stt_recognizer.dynamic_energy_adjustment_damping = 0.15
            stt_recognizer.dynamic_energy_ratio = 1.5
            stt_recognizer.pause_threshold = 0.8  # Shorter pause detection
            stt_recognizer.non_speaking_duration = 0.5
            stt_recognizer.phrase_threshold = 0.3
            
        try:
            with sr.Microphone() as source:
                # Calibrate for ambient noise
                self.log_message("Adjusting for ambient noise...", is_system=True)
                stt_recognizer.adjust_for_ambient_noise(source, duration=1)
                
                self.log_message("Listening...", is_system=True)
                
                # Enhanced audio capture
                audio = stt_recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=10,
                    snowboy_configuration=None
                )
                
                # Process captured audio with improved error handling
                try:
                    # Use Google's enhanced model with improved settings
                    text = stt_recognizer.recognize_google(
                        audio,
                        language="en-US",
                        show_all=False,  # Set to True for multiple alternatives
                        with_confidence=True
                    )
                    
                    # Update audio visualization if available
                    if hasattr(self.parent, 'audio_visualizer'):
                        audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
                        chunk_size = len(audio_data) // 20
                        levels = []
                        
                        for i in range(20):
                            start = i * chunk_size
                            end = (i + 1) * chunk_size
                            chunk = audio_data[start:end]
                            rms = np.sqrt(np.mean(chunk**2))
                            level = min(1.0, rms / 32767 * 4)
                            levels.append(level)
                            
                        self.parent.audio_visualizer.update_levels(levels)
                    
                    if isinstance(text, tuple):  # Handle confidence scores
                        text, confidence = text
                        if confidence > 0.8:  # High confidence threshold
                            self.input_field.setText(text)
                            self.send_message()
                        else:
                            self.log_message(f"Low confidence ({confidence:.2f}). Please speak more clearly.", 
                                           is_system=True, 
                                           is_error=True)
                    else:
                        self.input_field.setText(text)
                        self.send_message()
                        
                except sr.UnknownValueError:
                    self.log_message("Could not understand audio. Please try again.", 
                                   is_system=True, 
                                   is_error=True)
                except sr.RequestError as e:
                    self.log_message(f"Error with speech recognition service: {e}", 
                                   is_system=True, 
                                   is_error=True)
                    
        except Exception as e:
            self.log_message(f"Error with voice input: {e}", 
                           is_system=True, 
                           is_error=True)
            
        finally:
            self.parent.is_listening = False
            
    def speak_message(self, message):
        """Generate speech using F5-TTS"""
        if self.tts_handler:
            self.tts_handler.speak(message)
            
    def split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences for better TTS handling"""
        # Add spaces around punctuation for consistent splitting
        text = " " + text + " "
        text = text.replace("\n", " ")
        
        # Handle abbreviations
        text = re.sub(r"(Mr|Mrs|Ms|Dr|i\.e)\.", r"\1<prd>", text)
        text = re.sub(r"\.\.\.", r"<prd><prd><prd>", text)
        
        # Split on punctuation
        sentences = re.split(r"(?<=\d\.)\s+|(?<=[.!?:])\s+", text)
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Ensure sentences aren't too long
        final_sentences = []
        for sentence in sentences:
            while len(sentence) > 250:
                split_index = sentence.rfind(' ', 0, 249)
                if split_index == -1:
                    split_index = 249
                final_sentences.append(sentence[:split_index].strip())
                sentence = sentence[split_index:].trip()
            final_sentences.append(sentence)
            
        return final_sentences
        
    def reset_conversation(self):
        self.current_node = None
        self.conversation_history = []
        self.entities = {}
        self.log_message("Conversation reset.", is_system=True)
