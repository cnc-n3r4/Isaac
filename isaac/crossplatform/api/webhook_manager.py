"""
Webhook Manager - Manage webhooks for event notifications
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import hashlib
import hmac


class WebhookManager:
    """
    Manages webhook subscriptions and event delivery
    """

    def __init__(self):
        self.webhooks: Dict[str, Dict[str, Any]] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.delivery_queue = asyncio.Queue()
        self.delivery_history: List[Dict[str, Any]] = []

    def register_webhook(
        self,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Register a new webhook

        Args:
            url: Webhook URL
            events: List of events to subscribe to
            secret: Optional secret for HMAC signature
            headers: Optional custom headers

        Returns:
            Webhook ID
        """
        webhook_id = hashlib.sha256(f"{url}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]

        self.webhooks[webhook_id] = {
            'id': webhook_id,
            'url': url,
            'events': events,
            'secret': secret,
            'headers': headers or {},
            'created_at': datetime.utcnow().isoformat(),
            'active': True,
            'delivery_count': 0,
            'last_delivery': None
        }

        return webhook_id

    def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook"""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            return True

        return False

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all registered webhooks"""
        return [
            {
                'id': wh['id'],
                'url': wh['url'],
                'events': wh['events'],
                'active': wh['active'],
                'delivery_count': wh['delivery_count'],
                'last_delivery': wh['last_delivery']
            }
            for wh in self.webhooks.values()
        ]

    async def trigger_event(self, event_type: str, data: Dict[str, Any]):
        """
        Trigger an event to all subscribed webhooks

        Args:
            event_type: Type of event
            data: Event data
        """
        # Find all webhooks subscribed to this event
        subscribers = [
            wh for wh in self.webhooks.values()
            if event_type in wh['events'] and wh['active']
        ]

        # Queue deliveries
        for webhook in subscribers:
            payload = {
                'event': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }

            await self.delivery_queue.put({
                'webhook': webhook,
                'payload': payload
            })

        # Process deliveries asynchronously
        asyncio.create_task(self._process_delivery_queue())

    async def _process_delivery_queue(self):
        """Process webhook deliveries from queue"""
        while not self.delivery_queue.empty():
            try:
                item = await self.delivery_queue.get()
                await self._deliver_webhook(item['webhook'], item['payload'])
            except Exception as e:
                print(f"Error processing webhook delivery: {e}")

    async def _deliver_webhook(self, webhook: Dict[str, Any], payload: Dict[str, Any]):
        """
        Deliver webhook payload to URL

        Args:
            webhook: Webhook configuration
            payload: Event payload
        """
        delivery_id = hashlib.sha256(
            f"{webhook['id']}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        delivery = {
            'id': delivery_id,
            'webhook_id': webhook['id'],
            'url': webhook['url'],
            'payload': payload,
            'started_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }

        try:
            # Prepare request
            headers = {
                'Content-Type': 'application/json',
                'X-Isaac-Event': payload['event'],
                'X-Isaac-Delivery': delivery_id,
                **webhook['headers']
            }

            # Add HMAC signature if secret provided
            if webhook['secret']:
                signature = self._generate_signature(
                    json.dumps(payload),
                    webhook['secret']
                )
                headers['X-Isaac-Signature'] = signature

            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook['url'],
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    delivery['status_code'] = response.status
                    delivery['response'] = await response.text()

                    if 200 <= response.status < 300:
                        delivery['status'] = 'delivered'
                    else:
                        delivery['status'] = 'failed'

        except asyncio.TimeoutError:
            delivery['status'] = 'timeout'
            delivery['error'] = 'Request timeout'
        except Exception as e:
            delivery['status'] = 'error'
            delivery['error'] = str(e)

        delivery['completed_at'] = datetime.utcnow().isoformat()

        # Update webhook stats
        webhook['delivery_count'] += 1
        webhook['last_delivery'] = delivery['completed_at']

        # Store delivery history
        self.delivery_history.append(delivery)

        # Keep only last 1000 deliveries
        if len(self.delivery_history) > 1000:
            self.delivery_history = self.delivery_history[-1000:]

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"sha256={signature}"

    def get_webhook(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook details"""
        return self.webhooks.get(webhook_id)

    def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        active: Optional[bool] = None
    ) -> bool:
        """Update webhook configuration"""
        webhook = self.webhooks.get(webhook_id)

        if not webhook:
            return False

        if url is not None:
            webhook['url'] = url

        if events is not None:
            webhook['events'] = events

        if active is not None:
            webhook['active'] = active

        return True

    def get_delivery_history(
        self,
        webhook_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get delivery history

        Args:
            webhook_id: Optional webhook ID to filter
            limit: Maximum number of deliveries to return

        Returns:
            List of deliveries
        """
        if webhook_id:
            history = [
                d for d in self.delivery_history
                if d['webhook_id'] == webhook_id
            ]
        else:
            history = self.delivery_history

        return history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get webhook statistics"""
        total_deliveries = len(self.delivery_history)
        successful = sum(1 for d in self.delivery_history if d['status'] == 'delivered')
        failed = sum(1 for d in self.delivery_history if d['status'] == 'failed')

        return {
            'total_webhooks': len(self.webhooks),
            'active_webhooks': sum(1 for wh in self.webhooks.values() if wh['active']),
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful,
            'failed_deliveries': failed,
            'success_rate': (successful / total_deliveries * 100) if total_deliveries > 0 else 0
        }
