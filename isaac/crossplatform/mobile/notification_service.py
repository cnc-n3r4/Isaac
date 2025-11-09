"""
Notification Service - Push notifications for mobile devices
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class NotificationService:
    """
    Manages push notifications for mobile devices
    """

    def __init__(self):
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.notifications: List[Dict[str, Any]] = []
        self.notification_queue = asyncio.Queue()

    def register_device(
        self,
        device_token: str,
        platform: str,
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a mobile device for notifications

        Args:
            device_token: Platform-specific device token
            platform: 'ios' or 'android'
            user_id: User identifier
            preferences: Notification preferences

        Returns:
            Device ID
        """
        device_id = f"{platform}_{device_token[:16]}"

        self.devices[device_id] = {
            'id': device_id,
            'token': device_token,
            'platform': platform,
            'user_id': user_id,
            'preferences': preferences or {},
            'registered_at': datetime.utcnow().isoformat(),
            'active': True
        }

        return device_id

    def unregister_device(self, device_id: str) -> bool:
        """Unregister a device"""
        if device_id in self.devices:
            del self.devices[device_id]
            return True

        return False

    async def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Send notification to user's devices

        Args:
            user_id: User identifier
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Optional additional data
        """
        # Find user's devices
        user_devices = [
            device for device in self.devices.values()
            if device['user_id'] == user_id and device['active']
        ]

        notification = {
            'id': f"notif_{len(self.notifications)}",
            'type': notification_type,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': datetime.utcnow().isoformat(),
            'delivered_to': []
        }

        # Queue notifications for each device
        for device in user_devices:
            # Check if user wants this notification type
            if self._should_send(device, notification_type):
                await self.notification_queue.put({
                    'device': device,
                    'notification': notification
                })

        self.notifications.append(notification)

        # Process queue
        asyncio.create_task(self._process_notification_queue())

    def _should_send(self, device: Dict[str, Any], notification_type: str) -> bool:
        """Check if notification should be sent based on preferences"""
        preferences = device.get('preferences', {})

        # Check if this notification type is enabled
        if notification_type in preferences:
            return preferences[notification_type]

        # Default to sending
        return True

    async def _process_notification_queue(self):
        """Process notification queue"""
        while not self.notification_queue.empty():
            try:
                item = await self.notification_queue.get()
                await self._send_to_device(
                    item['device'],
                    item['notification']
                )
            except Exception as e:
                print(f"Error sending notification: {e}")

    async def _send_to_device(
        self,
        device: Dict[str, Any],
        notification: Dict[str, Any]
    ):
        """
        Send notification to specific device

        Args:
            device: Device information
            notification: Notification data
        """
        platform = device['platform']

        if platform == 'ios':
            await self._send_apns(device, notification)
        elif platform == 'android':
            await self._send_fcm(device, notification)

        # Track delivery
        notification['delivered_to'].append(device['id'])

    async def _send_apns(
        self,
        device: Dict[str, Any],
        notification: Dict[str, Any]
    ):
        """
        Send notification via Apple Push Notification Service

        Args:
            device: Device information
            notification: Notification data
        """
        # TODO: Implement APNS integration
        # For now, simulate sending
        await asyncio.sleep(0.1)

        print(f"[APNS] Sent to {device['id']}: {notification['title']}")

    async def _send_fcm(
        self,
        device: Dict[str, Any],
        notification: Dict[str, Any]
    ):
        """
        Send notification via Firebase Cloud Messaging

        Args:
            device: Device information
            notification: Notification data
        """
        # TODO: Implement FCM integration
        # For now, simulate sending
        await asyncio.sleep(0.1)

        print(f"[FCM] Sent to {device['id']}: {notification['title']}")

    def get_notifications(
        self,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for user

        Args:
            user_id: User identifier
            limit: Maximum number of notifications
            unread_only: Only return unread notifications

        Returns:
            List of notifications
        """
        # TODO: Filter by user_id and read status
        return self.notifications[-limit:]

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        for notif in self.notifications:
            if notif['id'] == notification_id:
                notif['read'] = True
                return True

        return False

    def update_preferences(
        self,
        device_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update notification preferences for device"""
        device = self.devices.get(device_id)

        if device:
            device['preferences'].update(preferences)
            return True

        return False

    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device information"""
        return self.devices.get(device_id)

    def list_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """List devices for user"""
        return [
            {
                'id': device['id'],
                'platform': device['platform'],
                'registered_at': device['registered_at'],
                'active': device['active']
            }
            for device in self.devices.values()
            if device['user_id'] == user_id
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        return {
            'total_devices': len(self.devices),
            'active_devices': sum(1 for d in self.devices.values() if d['active']),
            'total_notifications': len(self.notifications),
            'ios_devices': sum(1 for d in self.devices.values() if d['platform'] == 'ios'),
            'android_devices': sum(1 for d in self.devices.values() if d['platform'] == 'android')
        }
