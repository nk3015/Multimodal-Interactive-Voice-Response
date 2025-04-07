# Conversational Agents IVR System

A powerful node-based development environment for creating and testing conversational agents and IVR (Interactive Voice Response) workflows. This application allows you to visually design conversation flows, test them with speech recognition and text-to-speech capabilities, and analyze workflow performance.

![Screenshot of the IVR System](ivr_system_screenshot.png)

## Features

- **Visual Workflow Designer**: Create conversation flows with a node-based editor
- **Live Testing**: Test workflows with speech input/output or text
- **Node Types**:
  - **Start Nodes**: Entry points for conversations
  - **Intent Nodes**: Collect required information from users
  - **Response Nodes**: Provide information to users
  - **End Nodes**: Terminate conversations
- **Entity Extraction**: Automatically identify and extract entities from user messages
- **Speech Integration**: Text-to-speech and speech recognition capabilities
- **Pre-built Workflows**: Banking, Airport, and Inflight Service examples
- **Workflow Analysis**: Validate workflows for completeness and correctness

## Installation

### Prerequisites

- Python 3.8+
- PyQt6
- Optional: Ollama (for AI capabilities)
- Optional: Coqui TTS (for text-to-speech)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/conversational-agents-ivr-system.git
   cd conversational-agents-ivr-system
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Optional AI capabilities:
   - Install [Ollama](https://github.com/ollama/ollama) for AI-powered entity extraction and intent classification
   - Install TTS for voice capabilities:
     ```
     pip install TTS
     ```

## Running the Application

Start the application with:

```
python workflow_manager_final.py
```

## Usage Guide

### Creating a New Workflow

1. Click the "New" button in the sidebar
2. Enter a name for your workflow
3. Use the "Add Node" button to create nodes
4. Connect nodes by clicking "Add Connection" and selecting source and target nodes
5. Save your workflow using the "Save" button

### Node Types

- **Start Node**: First node in the workflow, begins the conversation
- **Intent Node**: Collects required information from the user
  - Add required entities in the node properties
- **Response Node**: Provides information to the user
- **End Node**: Terminates the conversation

### Entity Extraction

Intent nodes can extract entities (key information) from user messages:

1. When creating or editing an Intent node, add required entities
2. During conversations, the system will extract these entities from user messages
3. The system will prompt for missing entities before proceeding

### Testing Workflows

1. Switch to the "Live Conversation" tab
2. Click "Start Conversation" to begin
3. Type messages or use the microphone button for voice input
4. View the conversation flow in the log area

### Running Automated Tests

1. Switch to the "Workflow Testing" tab
2. Enter sample inputs and test entity values
3. Choose between "Step by Step" or "Full Conversation" testing
4. Click "Run Test" to execute the test
5. Analyze the results in the log area

### Workflow Analysis

1. Switch to the "Workflow Testing" tab
2. Click "Analyze Workflow"
3. Review the analysis results, including:
   - Node type breakdown
   - Path analysis
   - Missing connections
   - Required entities

## Pre-built Workflows

The system comes with three pre-built workflows:

### Banking Flow

A conversation flow for banking interactions:
- Balance inquiries
- Money transfers
- Card issue resolution

### Airport Flow

A conversation flow for airport check-in:
- ID verification
- Baggage check
- Seat selection
- Boarding pass issuance

### Inflight Service Flow

A conversation flow for inflight services:
- Beverage service
- Meal service
- Special assistance
- Landing preparation

## File Structure

```
conversational-agents-ivr-system/
├── workflow_manager_final.py    # Main application entry point
├── ollama_handler.py            # AI integration with Ollama
├── ui_components.py             # UI components and widgets
├── requirements.txt             # Python dependencies
└── workflows/                   # Saved workflows
    ├── banking_flow.json
    ├── airport_flow.json
    └── inflight_flow.json
```

## Customizing the System

### Adding New Node Types

1. Extend the NodeDialog class in ui_components.py
2. Add any special properties for your node type
3. Update the node rendering in NodeCanvas.draw_nodes

### Custom Entity Extraction

To implement a custom entity extraction method:
1. Create a new method in ollama_handler.py
2. Add your extraction logic
3. Return a dictionary of extracted entities

### Styling and Appearance

Customize the appearance by modifying the constants in ui_components.py:
- DARK_BG
- ACCENT_BLUE
- ACCENT_RED
- CONNECTOR_COLOR
- etc.

## Troubleshooting

### Speech Recognition Issues

If you encounter problems with speech recognition:
1. Check that your microphone is working
2. Ensure you have internet access (for Google Speech Recognition)
3. Try adjusting the microphone volume

### AI Integration Issues

If Ollama integration isn't working:
1. Ensure Ollama is installed and running (`ollama serve`)
2. Check that a model is available (`ollama list`)
3. If needed, pull a model: `ollama pull llama3`

### UI Problems

If the UI appears incorrectly:
1. Ensure PyQt6 is installed correctly
2. Try running with a different window size
3. Check for any error messages in the console

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyQt6 for the UI framework
- Ollama for the AI capabilities
- Coqui TTS for text-to-speech functionality
