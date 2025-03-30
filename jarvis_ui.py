import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QTextEdit, QLineEdit,
                           QLabel, QDialog, QMessageBox, QFrame,
                           QGraphicsDropShadowEffect, QProgressBar)
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QThread, QPoint
from PyQt5.QtGui import QColor, QIcon, QPixmap, QFont, QPalette, QLinearGradient, QGradient, QPainter, QBrush, QTextCursor, QFontDatabase
import qdarkstyle
import uuid # For generating unique thread IDs
from jarvis import graph,run_agent_interaction
from tools.web_search import search_on_web_tool

# --- Futuristic Styling ---
# Attempt to load a modern font
QFontDatabase.addApplicationFont(":/fonts/Roboto-Regular.ttf") # Example if using resources
MODERN_FONT = "Roboto" # Try "Roboto", "Open Sans", or "Orbitron" if installed
FALLBACK_FONT = "Segoe UI" # Or "Arial", "Calibri"

# Define color palette (example)
COLOR_BACKGROUND = "#0D1B2A" # Very dark blue
COLOR_BACKGROUND_LIGHTER = "#1B263B" # Slightly lighter dark blue
COLOR_BACKGROUND_INPUT = "#25304D" # Darker input field
COLOR_TEXT = "#E0E1DD"      # Light grey/off-white text
COLOR_ACCENT = "#40CFFF"     # Bright cyan/blue accent
COLOR_ACCENT_HOVER = "#60DFFF"
COLOR_ACCENT_PRESSED = "#20AFFF"
COLOR_BORDER = "#415A77"     # Muted blue/grey border
COLOR_SCROLLBAR = "#415A77"
COLOR_SCROLLBAR_HANDLE = "#778DA9"

FUTURISTIC_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLOR_BACKGROUND};
}}

QWidget {{
    color: {COLOR_TEXT};
    font-family: '{MODERN_FONT}', '{FALLBACK_FONT}', sans-serif; /* Specify font */
    font-size: 10pt;
}}

QTextEdit {{
    background-color: {COLOR_BACKGROUND_LIGHTER};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 12px;
    font-size: 11pt; /* Slightly larger font for readability */
}}

QLineEdit {{
    background-color: {COLOR_BACKGROUND_INPUT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 18px; /* More rounded */
    padding: 0 15px; /* More padding */
    font-size: 10pt;
    min-height: 36px; /* Ensure height */
    color: {COLOR_TEXT};
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_ACCENT};
}}

QPushButton {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_BACKGROUND}; /* Dark text on bright button */
    border: none;
    border-radius: 18px; /* Match line edit */
    padding: 0 18px;
    min-height: 36px; /* Match line edit */
    font-weight: bold;
    font-size: 10pt;
}}

QPushButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton:pressed {{
    background-color: {COLOR_ACCENT_PRESSED};
}}

QPushButton:disabled {{
    background-color: #555; /* Keep disabled style simple */
    color: #999;
}}

/* Scroll Bar Styling */
QScrollBar:vertical {{
    border: none;
    background: {COLOR_BACKGROUND_LIGHTER};
    width: 10px; /* Slimmer scrollbar */
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_SCROLLBAR_HANDLE};
    min-height: 20px;
    border-radius: 5px; /* Rounded handle */
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
    height: 0px; /* Hide arrows */
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{ /* Basic horizontal styling */
    border: none;
    background: {COLOR_BACKGROUND_LIGHTER};
    height: 10px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:horizontal {{
    background: {COLOR_SCROLLBAR_HANDLE};
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
    width: 0px;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

QLabel#titleLabel {{ /* Style for a potential title */
    font-size: 16pt;
    font-weight: bold;
    color: {COLOR_ACCENT};
    padding-bottom: 10px;
}}
"""
# --- End Styling ---

# Worker thread for running the agent interaction
class AgentWorker(QThread):
    responseReady = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)

    def __init__(self, user_input, thread_id, graph_obj):
        super().__init__()
        self.user_input = user_input
        self.thread_id = thread_id
        self.graph = graph_obj
      

    def run(self):
        try:
            print(f"[Thread {self.thread_id}] Running agent for input: {self.user_input}")
            response = run_agent_interaction(
                self.user_input,
                self.thread_id,
                self.graph
                
            )
            print(f"[Thread {self.thread_id}] Agent response: {response}")
            self.responseReady.emit(response or "Agent returned an empty response.")
        except Exception as e:
            error_message = f"An error occurred in the agent thread: {e}"
            print(error_message)
            import traceback
            traceback.print_exc() # Print full traceback to console
            self.errorOccurred.emit(error_message)

# Main UI Window
class JarvisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S Interface")
        self.setGeometry(100, 100, 700, 800)
        self.thread_id = f"ui-session-{uuid.uuid4()}"
        print(f"Starting new conversation thread: {self.thread_id}")

        self.initUI()

    def initUI(self):
        # Central Widget and Layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Conversation Display Area
        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        main_layout.addWidget(self.conversation_display, 1)

        # Input Area Layout
        input_layout = QHBoxLayout()
        input_layout.setSpacing(15)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter command or query...")
        self.input_field.returnPressed.connect(self.sendMessage)
        input_layout.addWidget(self.input_field, 1)

        self.send_button = QPushButton("SEND")
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.clicked.connect(self.sendMessage)
        input_layout.addWidget(self.send_button)

        main_layout.addLayout(input_layout)

        # Apply Futuristic Stylesheet
        self.setStyleSheet(FUTURISTIC_STYLESHEET)

        # Worker thread instance (reused)
        self.worker = None

        # Initial welcome message
        self.appendMessage("JARVIS", "System online. How may I assist you?")

    def appendMessage(self, sender, message):
        if not message:
            return

        # Replace newlines with HTML line breaks *before* the f-string
        processed_message = message.replace('\n', '<br>')

        formatted_message = f"""
            <div style='margin-bottom: 12px; border-left: 3px solid {COLOR_ACCENT}; padding-left: 10px;'>
                <span style='font-weight: bold; color: {COLOR_ACCENT};'>{sender}:</span>
                <div style='color: {COLOR_TEXT}; margin-top: 4px;'>{processed_message}</div>
            </div>
        """
        self.conversation_display.append(formatted_message)
        self.conversation_display.moveCursor(QTextCursor.End)

    def sendMessage(self):
        user_text = self.input_field.text().strip()
        if not user_text:
            return

        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Busy", "Processing previous request. Please wait.")
            return

        self.appendMessage("User", user_text)
        self.input_field.clear()
        self.setInteractionEnabled(False) # Disable input while processing

        # Start worker thread
        self.worker = AgentWorker(user_text, self.thread_id, graph)
        self.worker.responseReady.connect(self.handleAgentResponse)
        self.worker.errorOccurred.connect(self.handleAgentError)
        self.worker.finished.connect(self.onWorkerFinished) # Re-enable input on finish
        self.worker.start()

    def handleAgentResponse(self, response):
        self.appendMessage("JARVIS", response)

    def handleAgentError(self, error_message):
        self.appendMessage("System Error", f"An error occurred: {error_message}")
        # Optionally show a pop-up as well
        # QMessageBox.critical(self, "Agent Error", error_message)

    def onWorkerFinished(self):
        self.setInteractionEnabled(True) # Re-enable input
        print("[UI] Worker thread finished.")

    def setInteractionEnabled(self, enabled):
        self.input_field.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        self.input_field.setPlaceholderText("Enter command or query..." if enabled else "JARVIS is processing...")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Ensure fonts look okay
    # QApplication.setStyle("Fusion")
    window = JarvisWindow()
    window.show()
    sys.exit(app.exec_())
