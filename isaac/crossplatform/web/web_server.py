"""
Web Server - HTTP server for web interface
"""


class WebServer:
    """
    Web server for Isaac web interface
    """

    def __init__(self, isaac_core, host: str = "0.0.0.0", port: int = 8000):
        try:
            from flask import Flask, render_template_string
            from flask_cors import CORS
        except ImportError:
            raise ImportError("Flask is required for web server functionality. Install with: pip install flask flask-cors")

        self.Flask = Flask
        self.render_template_string = render_template_string
        self.CORS = CORS

        self.app = Flask(__name__)
        CORS(self.app)

        self.isaac_core = isaac_core
        self.host = host
        self.port = port

        self._setup_routes()

    def _setup_routes(self):
        """Setup web routes"""

        @self.app.route("/")
        def index():
            """Main web interface"""
            return self.render_template_string(self._get_index_html())

        @self.app.route("/terminal")
        def terminal():
            """Terminal interface"""
            return self.render_template_string(self._get_terminal_html())

        @self.app.route("/workspace")
        def workspace():
            """Workspace explorer"""
            return self.render_template_string(self._get_workspace_html())

        @self.app.route("/static/<path:filename>")
        def static_files(filename):
            """Serve static files"""
            # TODO: Implement static file serving
            return ""

    def _get_index_html(self) -> str:
        """Get main interface HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Isaac - Web Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            color: white;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .container {
            flex: 1;
            display: flex;
            padding: 20px;
            gap: 20px;
            overflow: hidden;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            flex: 1;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
        }

        .card h2 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 15px;
        }

        .card p {
            color: #666;
            font-size: 1.1em;
            text-align: center;
            line-height: 1.6;
        }

        .icon {
            font-size: 4em;
            margin-bottom: 20px;
        }

        .footer {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 15px;
            color: white;
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Isaac Web Interface</h1>
        <p>Cross-Platform Development Environment</p>
    </div>

    <div class="container">
        <div class="card" onclick="location.href='/terminal'">
            <div class="icon">💻</div>
            <h2>Terminal</h2>
            <p>Access the full Isaac terminal with real-time command execution and output streaming</p>
        </div>

        <div class="card" onclick="location.href='/workspace'">
            <div class="icon">📁</div>
            <h2>Workspace</h2>
            <p>Browse and manage your workspace files with visual navigation and search</p>
        </div>

        <div class="card" onclick="alert('API Documentation coming soon!')">
            <div class="icon">🔌</div>
            <h2>API</h2>
            <p>Explore the RESTful API endpoints and integrate Isaac with your applications</p>
        </div>
    </div>

    <div class="footer">
        <p>Isaac v5.5.0 - Cross-Platform Excellence</p>
    </div>
</body>
</html>
"""

    def _get_terminal_html(self) -> str:
        """Get terminal interface HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Isaac Terminal</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Courier New', monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .terminal-header {
            background: #2d2d2d;
            padding: 10px 20px;
            border-bottom: 1px solid #3e3e3e;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .terminal-header h1 {
            font-size: 1.2em;
            color: #4ec9b0;
        }

        .back-btn {
            background: #0e639c;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-family: inherit;
        }

        .back-btn:hover {
            background: #1177bb;
        }

        .terminal-container {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }

        .terminal-output {
            white-space: pre-wrap;
            word-wrap: break-word;
            margin-bottom: 20px;
            min-height: 300px;
        }

        .terminal-input-container {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .prompt {
            color: #4ec9b0;
            font-weight: bold;
        }

        .terminal-input {
            flex: 1;
            background: transparent;
            border: none;
            color: #d4d4d4;
            font-family: 'Courier New', monospace;
            font-size: 1em;
            outline: none;
        }

        .output-line {
            margin: 5px 0;
        }

        .command {
            color: #569cd6;
        }

        .error {
            color: #f48771;
        }

        .success {
            color: #4ec9b0;
        }
    </style>
</head>
<body>
    <div class="terminal-header">
        <h1>Isaac Terminal</h1>
        <button class="back-btn" onclick="location.href='/'">Back to Home</button>
    </div>

    <div class="terminal-container">
        <div class="terminal-output" id="output">
            <div class="output-line success">Isaac Terminal v5.5.0</div>
            <div class="output-line">Type 'help' for available commands</div>
            <div class="output-line">Connected to workspace: <span class="command">/workspace</span></div>
            <div class="output-line">---</div>
        </div>

        <div class="terminal-input-container">
            <span class="prompt">isaac&gt;</span>
            <input type="text" class="terminal-input" id="commandInput" autofocus>
        </div>
    </div>

    <script>
        const output = document.getElementById('output');
        const commandInput = document.getElementById('commandInput');

        // WebSocket connection (to be implemented)
        let ws = null;

        function connectWebSocket() {
            // TODO: Connect to WebSocket for real-time communication
            const wsUrl = 'ws://' + window.location.host + '/ws/terminal';
            console.log('WebSocket connection would be established to:', wsUrl);
        }

        function addOutput(text, className = '') {
            const line = document.createElement('div');
            line.className = 'output-line ' + className;
            line.textContent = text;
            output.appendChild(line);
            output.scrollTop = output.scrollHeight;
        }

        function executeCommand(command) {
            if (!command.trim()) return;

            // Display command
            addOutput('isaac> ' + command, 'command');

            // TODO: Send command via WebSocket or REST API
            // For now, just mock some responses
            if (command === 'help') {
                addOutput('Available commands:', 'success');
                addOutput('  help     - Show this help message');
                addOutput('  workspace - Show workspace information');
                addOutput('  bubbles  - List saved bubbles');
                addOutput('  clear    - Clear terminal');
            } else if (command === 'clear') {
                output.innerHTML = '';
            } else if (command === 'workspace') {
                addOutput('Workspace: /workspace', 'success');
                addOutput('Status: Active');
                addOutput('Files: 42');
            } else if (command === 'bubbles') {
                addOutput('Saved bubbles:', 'success');
                addOutput('  1. my-project-bubble (2024-01-15)');
                addOutput('  2. dev-environment (2024-01-10)');
            } else {
                addOutput('Command not found: ' + command, 'error');
                addOutput('Type "help" for available commands');
            }

            commandInput.value = '';
        }

        commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                executeCommand(commandInput.value);
            }
        });

        // Initialize
        connectWebSocket();
    </script>
</body>
</html>
"""

    def _get_workspace_html(self) -> str:
        """Get workspace explorer HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Isaac Workspace</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: #667eea;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            font-size: 1.5em;
        }

        .back-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-family: inherit;
        }

        .back-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .container {
            flex: 1;
            display: flex;
            overflow: hidden;
        }

        .sidebar {
            width: 250px;
            background: white;
            border-right: 1px solid #ddd;
            overflow-y: auto;
        }

        .file-tree {
            padding: 10px;
        }

        .file-item {
            padding: 8px;
            cursor: pointer;
            border-radius: 4px;
            margin: 2px 0;
        }

        .file-item:hover {
            background: #f0f0f0;
        }

        .file-item.selected {
            background: #667eea;
            color: white;
        }

        .content {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }

        .file-preview {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        .file-preview h2 {
            color: #667eea;
            margin-bottom: 15px;
        }

        .file-preview pre {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Workspace Explorer</h1>
        <button class="back-btn" onclick="location.href='/'">Back to Home</button>
    </div>

    <div class="container">
        <div class="sidebar">
            <div class="file-tree" id="fileTree">
                <div class="file-item" onclick="selectFile('README.md')">📄 README.md</div>
                <div class="file-item" onclick="selectFile('package.json')">📄 package.json</div>
                <div class="file-item" onclick="selectFile('src/main.py')">📄 src/main.py</div>
                <div class="file-item" onclick="selectFile('tests/test.py')">📄 tests/test.py</div>
            </div>
        </div>

        <div class="content">
            <div class="file-preview">
                <h2>Welcome to Workspace Explorer</h2>
                <p>Select a file from the sidebar to view its contents.</p>
                <p>File operations coming soon:</p>
                <ul>
                    <li>Browse directory structure</li>
                    <li>Search files</li>
                    <li>View file contents</li>
                    <li>Edit files</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        function selectFile(filename) {
            // Remove previous selection
            document.querySelectorAll('.file-item').forEach(item => {
                item.classList.remove('selected');
            });

            // Add selection to clicked item
            event.target.classList.add('selected');

            // TODO: Load file content via API
            console.log('Selected file:', filename);
        }
    </script>
</body>
</html>
"""

    def run(self, debug: bool = False):
        """Run the web server"""
        print(f"Starting Isaac Web Interface at http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug)

    def get_app(self):
        """Get Flask app instance"""
        return self.app
