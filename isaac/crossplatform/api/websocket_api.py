"""
WebSocket API - Real-time bidirectional communication
"""

import asyncio
import json
from typing import Dict, Any, Set, Callable
import uuid
from datetime import datetime


class WebSocketAPI:
    """
    WebSocket server for real-time communication
    """

    def __init__(self, isaac_core):
        self.isaac_core = isaac_core
        self.connections: Dict[str, Any] = {}
        self.subscriptions: Dict[str, Set[str]] = {}
        self.message_handlers: Dict[str, Callable] = {}

        self._setup_handlers()

    def _setup_handlers(self):
        """Setup message handlers"""
        self.message_handlers = {
            'ping': self._handle_ping,
            'subscribe': self._handle_subscribe,
            'unsubscribe': self._handle_unsubscribe,
            'execute': self._handle_execute,
            'query': self._handle_query,
            'get_context': self._handle_get_context
        }

    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        connection_id = str(uuid.uuid4())

        self.connections[connection_id] = {
            'id': connection_id,
            'websocket': websocket,
            'path': path,
            'connected_at': datetime.utcnow().isoformat(),
            'subscriptions': set()
        }

        try:
            # Send welcome message
            await self._send_message(connection_id, {
                'type': 'connected',
                'connection_id': connection_id,
                'server_version': '5.5.0'
            })

            # Handle incoming messages
            async for message in websocket:
                await self._handle_message(connection_id, message)

        except Exception as e:
            print(f"Connection error: {e}")

        finally:
            # Cleanup
            if connection_id in self.connections:
                del self.connections[connection_id]

    async def _handle_message(self, connection_id: str, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            handler = self.message_handlers.get(message_type)

            if handler:
                response = await handler(connection_id, data)
                if response:
                    await self._send_message(connection_id, response)
            else:
                await self._send_error(
                    connection_id,
                    f"Unknown message type: {message_type}"
                )

        except json.JSONDecodeError:
            await self._send_error(connection_id, "Invalid JSON")
        except Exception as e:
            await self._send_error(connection_id, str(e))

    async def _handle_ping(self, connection_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping message"""
        return {
            'type': 'pong',
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _handle_subscribe(self, connection_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription request"""
        channel = data.get('channel')

        if not channel:
            return {'type': 'error', 'message': 'Channel required'}

        # Add to subscriptions
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()

        self.subscriptions[channel].add(connection_id)
        self.connections[connection_id]['subscriptions'].add(channel)

        return {
            'type': 'subscribed',
            'channel': channel
        }

    async def _handle_unsubscribe(self, connection_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unsubscribe request"""
        channel = data.get('channel')

        if channel in self.subscriptions:
            self.subscriptions[channel].discard(connection_id)

        if connection_id in self.connections:
            self.connections[connection_id]['subscriptions'].discard(channel)

        return {
            'type': 'unsubscribed',
            'channel': channel
        }

    async def _handle_execute(self, connection_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle command execution request"""
        command = data.get('command')
        data.get('workspace_id')

        if not command:
            return {'type': 'error', 'message': 'Command required'}

        # TODO: Execute command and stream output
        execution_id = str(uuid.uuid4())

        return {
            'type': 'execution_started',
            'execution_id': execution_id,
            'command': command
        }

    async def _handle_query(self, connection_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AI query"""
        query = data.get('query')

        if not query:
            return {'type': 'error', 'message': 'Query required'}

        # TODO: Process AI query
        return {
            'type': 'query_response',
            'response': 'AI response here'
        }

    async def _handle_get_context(self, connection_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle context retrieval"""
        data.get('workspace_id')

        # TODO: Get workspace context
        return {
            'type': 'context',
            'context': {}
        }

    async def _send_message(self, connection_id: str, message: Dict[str, Any]):
        """Send message to a connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            websocket = connection['websocket']

            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                print(f"Error sending message: {e}")

    async def _send_error(self, connection_id: str, error: str):
        """Send error message"""
        await self._send_message(connection_id, {
            'type': 'error',
            'message': error
        })

    async def broadcast(self, channel: str, message: Dict[str, Any]):
        """
        Broadcast message to all subscribers of a channel

        Args:
            channel: Channel name
            message: Message to broadcast
        """
        if channel in self.subscriptions:
            tasks = []

            for connection_id in self.subscriptions[channel]:
                tasks.append(self._send_message(connection_id, message))

            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection"""
        await self._send_message(connection_id, message)

    def get_connections(self) -> Dict[str, Any]:
        """Get all active connections"""
        return {
            conn_id: {
                'id': conn['id'],
                'connected_at': conn['connected_at'],
                'subscriptions': list(conn['subscriptions'])
            }
            for conn_id, conn in self.connections.items()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        return {
            'active_connections': len(self.connections),
            'channels': len(self.subscriptions),
            'total_subscriptions': sum(len(subs) for subs in self.subscriptions.values())
        }
