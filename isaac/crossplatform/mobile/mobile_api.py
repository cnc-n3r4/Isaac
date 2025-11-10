"""
Mobile API - RESTful API for mobile companion apps
"""


class MobileAPI:
    """
    Mobile-optimized API for iOS and Android companion apps
    """

    def __init__(self, isaac_core, host: str = "0.0.0.0", port: int = 8081):
        try:
            from flask import Flask, jsonify, request
            from flask_cors import CORS
        except ImportError:
            raise ImportError("Flask is required for mobile API functionality. Install with: pip install flask flask-cors")

        self.Flask = Flask
        self.jsonify = jsonify
        self.request = request
        self.CORS = CORS

        self.app = Flask(__name__)
        CORS(self.app)

        self.isaac_core = isaac_core
        self.host = host
        self.port = port

        self._setup_routes()

    def _setup_routes(self):
        """Setup mobile API routes"""

        # Health and version
        @self.app.route("/mobile/v1/health", methods=["GET"])
        def health():
            """Health check endpoint"""
            return self.jsonify({"status": "healthy", "version": "5.5.0", "platform": "mobile"})

        # Device registration
        @self.app.route("/mobile/v1/devices", methods=["POST"])
        def register_device():
            """Register a mobile device"""
            data = self.request.json
            device_token = data.get("device_token")
            platform = data.get("platform")  # 'ios' or 'android'

            if not device_token or not platform:
                return self.jsonify({"error": "device_token and platform required"}), 400

            # TODO: Store device registration
            return self.jsonify({"device_id": "new-device-id", "registered": True}), 201

        @self.app.route("/mobile/v1/devices/<device_id>", methods=["DELETE"])
        def unregister_device(device_id):
            """Unregister a mobile device"""
            # TODO: Remove device registration
            return self.jsonify({"success": True})

        # Instance monitoring
        @self.app.route("/mobile/v1/instances", methods=["GET"])
        def list_instances():
            """List Isaac instances"""
            # TODO: Get list of Isaac instances user has access to
            return self.jsonify(
                {
                    "instances": [
                        {
                            "id": "instance-1",
                            "name": "Work Laptop",
                            "status": "active",
                            "last_seen": "2024-01-15T10:30:00Z",
                        }
                    ]
                }
            )

        @self.app.route("/mobile/v1/instances/<instance_id>/status", methods=["GET"])
        def get_instance_status(instance_id):
            """Get status of an Isaac instance"""
            # TODO: Get real-time instance status
            return self.jsonify(
                {
                    "instance_id": instance_id,
                    "status": "active",
                    "workspace": "/home/user/project",
                    "active_sessions": 2,
                    "cpu_usage": 45.2,
                    "memory_usage": 1234567890,
                }
            )

        # Quick commands
        @self.app.route("/mobile/v1/instances/<instance_id>/commands", methods=["POST"])
        def execute_quick_command(instance_id):
            """Execute a quick command"""
            data = self.request.json
            command = data.get("command")

            if not command:
                return self.jsonify({"error": "command required"}), 400

            # TODO: Execute command on instance
            return self.jsonify(
                {"execution_id": "exec-id", "status": "running", "instance_id": instance_id}
            )

        @self.app.route("/mobile/v1/executions/<execution_id>", methods=["GET"])
        def get_execution_status(execution_id):
            """Get execution status"""
            # TODO: Get execution status
            return self.jsonify(
                {
                    "execution_id": execution_id,
                    "status": "completed",
                    "output": "Command output here",
                    "exit_code": 0,
                }
            )

        # Workspace context
        @self.app.route("/mobile/v1/instances/<instance_id>/context", methods=["GET"])
        def get_context(instance_id):
            """Get workspace context"""
            # TODO: Get workspace context
            return self.jsonify(
                {
                    "instance_id": instance_id,
                    "workspace": "/home/user/project",
                    "recent_files": ["src/main.py", "README.md"],
                    "git_branch": "main",
                    "git_status": "clean",
                }
            )

        @self.app.route("/mobile/v1/instances/<instance_id>/search", methods=["POST"])
        def search_context(instance_id):
            """Search workspace context"""
            data = self.request.json
            query = data.get("query")

            if not query:
                return self.jsonify({"error": "query required"}), 400

            # TODO: Search workspace context
            return self.jsonify(
                {"results": [{"file": "src/main.py", "line": 42, "content": "def main():"}]}
            )

        # Recent activity
        @self.app.route("/mobile/v1/instances/<instance_id>/activity", methods=["GET"])
        def get_recent_activity(instance_id):
            """Get recent activity"""
            limit = self.request.args.get("limit", 10, type=int)

            # TODO: Get recent activity
            return self.jsonify(
                {
                    "activities": [
                        {
                            "type": "command",
                            "description": "Executed: git status",
                            "timestamp": "2024-01-15T10:30:00Z",
                        }
                    ]
                }
            )

        # Notifications
        @self.app.route("/mobile/v1/notifications", methods=["GET"])
        def get_notifications():
            """Get notifications for user"""
            # TODO: Get notifications
            return self.jsonify(
                {
                    "notifications": [
                        {
                            "id": "notif-1",
                            "type": "suggestion",
                            "title": "Optimization Suggestion",
                            "message": "Consider using a virtual environment",
                            "timestamp": "2024-01-15T10:30:00Z",
                            "read": False,
                        }
                    ]
                }
            )

        @self.app.route("/mobile/v1/notifications/<notification_id>/read", methods=["POST"])
        def mark_notification_read(notification_id):
            """Mark notification as read"""
            # TODO: Mark as read
            return self.jsonify({"success": True})

        # Bubbles (workspace snapshots)
        @self.app.route("/mobile/v1/bubbles", methods=["GET"])
        def list_bubbles():
            """List saved bubbles"""
            # TODO: Get bubbles
            return self.jsonify(
                {
                    "bubbles": [
                        {
                            "id": "bubble-1",
                            "name": "my-project",
                            "created_at": "2024-01-15T10:30:00Z",
                            "size": 1234567,
                        }
                    ]
                }
            )

        @self.app.route("/mobile/v1/bubbles/<bubble_id>", methods=["GET"])
        def get_bubble_info(bubble_id):
            """Get bubble information"""
            # TODO: Get bubble details
            return self.jsonify(
                {
                    "id": bubble_id,
                    "name": "my-project",
                    "workspace_path": "/home/user/project",
                    "created_at": "2024-01-15T10:30:00Z",
                    "platform": "linux",
                    "size": 1234567,
                }
            )

        # Files (read-only access for mobile)
        @self.app.route("/mobile/v1/instances/<instance_id>/files", methods=["GET"])
        def list_files(instance_id):
            """List files in workspace"""
            path = self.request.args.get("path", "")

            # TODO: List files
            return self.jsonify(
                {
                    "path": path,
                    "files": [
                        {"name": "src", "type": "directory"},
                        {"name": "README.md", "type": "file", "size": 1234},
                    ],
                }
            )

        @self.app.route(
            "/mobile/v1/instances/<instance_id>/files/<path:file_path>", methods=["GET"]
        )
        def get_file_content(instance_id, file_path):
            """Get file content (limited size for mobile)"""
            max_size = self.request.args.get("max_size", 10000, type=int)

            # TODO: Get file content
            return self.jsonify(
                {
                    "path": file_path,
                    "content": "File content here...",
                    "truncated": False,
                    "size": 123,
                }
            )

        # Analytics summary
        @self.app.route("/mobile/v1/instances/<instance_id>/analytics", methods=["GET"])
        def get_analytics_summary(instance_id):
            """Get analytics summary (mobile-optimized)"""
            # TODO: Get analytics
            return self.jsonify(
                {
                    "commands_today": 42,
                    "productivity_score": 85,
                    "top_commands": [
                        {"command": "git status", "count": 10},
                        {"command": "npm test", "count": 8},
                    ],
                }
            )

    def run(self, debug: bool = False):
        """Run the mobile API server"""
        print(f"Starting Isaac Mobile API at http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug)

    def get_app(self):
        """Get Flask app instance"""
        return self.app
