# Isaac Messaging & Key System

## The Vision: Multi-Channel Bot Platform

Isaac isn't just a terminal shell - it's a **multi-interface orchestration platform** accessible via:
- **Terminal** (interactive shell)
- **Telegram** (mobile remote control)
- **Webhooks** (external services)
- **Cron/Daemon** (scheduled tasks)
- **API** (programmatic access)

**All channels sync through cloud memory, all protected by key system.**

## Problem Statement

**User quote:** "this is why messaging matters. the !bang. I was tinkering with the idea of a using a telegram to interact with my cloud too. cause all i'd need then is a cron on isaac or a webhook thing.. and i can control isaac also thru a chat app."

**Security needs:**
- `isaac /start` requires key for interactive sessions
- `isaac /start -key cron-bot secret` for daemon mode (telegram webhook listener)
- `isaac /do-something` for one-shot commands (limited permissions)
- `isaac /start -key sarah password` for persona switching
- Rejection without valid key: "i dont do this shit for free" 😂

**Messaging routing:**
- `!isaac` routes to Isaac instance
- `!sarah` routes to Sarah persona
- `!deploy` routes to deploy-bot
- Cross-channel: Telegram → webhook → cloud → terminal (or vice versa)

## Phase 1: Key System Architecture

### Key Types

```python
# isaac/core/key_manager.py

class KeyManager:
    """Manage authentication keys for Isaac access"""
    
    KEY_TYPES = {
        "user": {
            "permissions": ["read", "write", "execute", "ai", "cloud"],
            "interactive": True,
            "description": "Full interactive user session"
        },
        "daemon": {
            "permissions": ["read", "write", "execute", "webhook"],
            "interactive": False,
            "description": "Background service for webhooks/cron"
        },
        "readonly": {
            "permissions": ["read", "cloud"],
            "interactive": True,
            "description": "View-only access (status, logs)"
        },
        "oneshot": {
            "permissions": ["read", "execute_safe"],
            "interactive": False,
            "description": "Single command execution (tier ≤2 only)"
        },
        "persona": {
            "permissions": ["read", "write", "execute", "ai", "persona_switch"],
            "interactive": True,
            "description": "Switch to different persona (Sarah, etc.)"
        }
    }
```

### Key Storage

**File:** `~/.isaac/keys.json` (encrypted)

```json
{
  "keys": [
    {
      "name": "me",
      "type": "user",
      "hash": "<bcrypt hash of 'superpassword'>",
      "created": "2025-10-01T10:00:00Z",
      "last_used": "2025-10-22T14:30:00Z",
      "expires": null
    },
    {
      "name": "sarah",
      "type": "persona",
      "hash": "<bcrypt hash of 'superduperdupersecretpassword'>",
      "persona": "sarah",
      "created": "2025-10-01T10:00:00Z",
      "last_used": "2025-10-22T09:15:00Z",
      "expires": null
    },
    {
      "name": "cron-bot",
      "type": "daemon",
      "hash": "<bcrypt hash of 'secret123'>",
      "created": "2025-10-15T12:00:00Z",
      "last_used": "2025-10-22T14:00:00Z",
      "expires": "2025-12-31T23:59:59Z"
    },
    {
      "name": "telegram-webhook",
      "type": "daemon",
      "hash": "<bcrypt hash of 'tg_webhook_secret'>",
      "webhook_url": "https://api.telegram.org/bot<token>/",
      "created": "2025-10-20T08:00:00Z",
      "expires": null
    }
  ],
  "rejection_messages": [
    "i dont do this shit for free",
    "get a key, pal",
    "nice try, no key = no service",
    "authentication required, buddy"
  ]
}
```

### Startup Modes

```bash
# 1. FULL INTERACTIVE (requires key)
C:\> isaac /start -key me superpassword
Authenticated as 'me' (user)
$> 

# 2. PERSONA SWITCH (requires persona key)
C:\> isaac /start -key sarah superduperdupersecretpassword
Sarah has been started.
Sarah> Coffee is brewing! anyone need me !sarah me, I got /task and shit to do ;)

# 3. DAEMON MODE (background, no prompt)
C:\> isaac /start -key cron-bot secret123 --daemon
Isaac daemon started (PID 12345)
Listening for: webhooks, telegram, scheduled tasks
Use 'isaac /stop' to terminate.

# 4. ONESHOT MODE (no key, limited)
C:\> isaac /do ls
<output>
C:\> isaac /do rm -rf /
Permission denied: tier 4 command requires key

# 5. REJECTED (no key for interactive)
C:\> isaac /start
Authentication required.
C:\> isaac /ask where is iceland?
i dont do this shit for free
C:\>
```

## Phase 2: Telegram Integration

### Architecture

```
User (Telegram) → Telegram Bot API → Webhook → Isaac Daemon → Cloud Memory ↔ Terminal Isaac
                                                     ↓
                                              Process Command
                                                     ↓
                                              Webhook Response → Telegram
```

### Telegram Bot Setup

**File:** `isaac/integrations/telegram_bot.py`

```python
"""
Telegram bot integration for remote Isaac control
Requires: python-telegram-bot library
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import asyncio

class IsaacTelegramBot:
    """Telegram interface for Isaac commands"""
    
    def __init__(self, token: str, isaac_key: str, cloud_client):
        self.token = token
        self.isaac_key = isaac_key
        self.cloud = cloud_client
        self.app = Application.builder().token(token).build()
        
        # Register handlers
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message"""
        await update.message.reply_text(
            "Isaac Telegram Interface\n\n"
            "Commands:\n"
            "  !isaac <cmd> - Run Isaac command\n"
            "  !ask <query> - Ask AI\n"
            "  !task list - List tasks\n"
            "  !status - Isaac status\n"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route !bang commands to Isaac"""
        text = update.message.text.strip()
        
        # Parse !bang routing
        if not text.startswith("!"):
            return
        
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            return
        
        bang = parts[0]  # e.g., "!isaac"
        command = parts[1]  # e.g., "!ask" or "/ask"
        args = parts[2] if len(parts) > 2 else ""
        
        # Route based on !bang
        if bang == "!isaac":
            result = await self.execute_isaac_command(command, args, update.effective_user.id)
            await update.message.reply_text(result)
        
        elif bang == "!sarah":
            result = await self.execute_persona_command("sarah", command, args)
            await update.message.reply_text(f"Sarah: {result}")
        
        elif bang == "!status":
            status = await self.get_isaac_status()
            await update.message.reply_text(status)
    
    async def execute_isaac_command(self, command: str, args: str, user_id: int) -> str:
        """Execute Isaac command via cloud API"""
        
        # Create command request
        request = {
            "source": "telegram",
            "user_id": user_id,
            "command": f"{command} {args}".strip(),
            "timestamp": datetime.now().isoformat(),
            "key": self.isaac_key
        }
        
        # Send to cloud queue
        self.cloud.enqueue_command(request)
        
        # Wait for response (poll cloud for result)
        result = await self.wait_for_result(request["timestamp"])
        return result
    
    async def wait_for_result(self, request_id: str, timeout: int = 30) -> str:
        """Poll cloud for command result"""
        for _ in range(timeout):
            result = self.cloud.get_command_result(request_id)
            if result:
                return result.get("output", "No output")
            await asyncio.sleep(1)
        return "⏱ Command timeout"
    
    def run(self):
        """Start bot"""
        self.app.run_polling()
```

### Isaac Daemon (Webhook Listener)

**File:** `isaac/integrations/daemon_mode.py`

```python
"""
Daemon mode for Isaac - processes webhook commands
Runs in background, polls cloud for commands
"""

import time
import json
from pathlib import Path
from isaac.core.command_router import CommandRouter
from isaac.core.session_manager import SessionManager
from isaac.api.cloud_client import CloudClient

class IsaacDaemon:
    """Background Isaac instance for webhook commands"""
    
    def __init__(self, key_name: str, key_password: str):
        self.key_name = key_name
        self.session = SessionManager()
        self.router = CommandRouter(self.session)
        self.cloud = CloudClient(self.session.config)
        
        # Verify key
        if not self._authenticate(key_name, key_password):
            raise ValueError(f"Invalid key: {key_name}")
    
    def run(self, poll_interval: int = 5):
        """Main daemon loop"""
        print(f"Isaac daemon started (key: {self.key_name})")
        print(f"Polling cloud every {poll_interval}s for commands...")
        
        try:
            while True:
                self._process_command_queue()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\nIsaac daemon stopped")
    
    def _process_command_queue(self):
        """Check cloud for pending commands"""
        queue = self.cloud.get_command_queue()
        
        for request in queue:
            # Verify request key matches daemon key
            if request.get("key") != self.key_name:
                continue
            
            command = request["command"]
            request_id = request["timestamp"]
            
            # Execute command
            result = self.router.route_command(command)
            
            # Send result back to cloud
            self.cloud.save_command_result(request_id, {
                "output": result.output,
                "success": result.success,
                "timestamp": datetime.now().isoformat()
            })
            
            # Remove from queue
            self.cloud.remove_from_queue(request_id)
    
    def _authenticate(self, key_name: str, key_password: str) -> bool:
        """Verify key credentials"""
        # Load keys.json, verify bcrypt hash
        pass
```

### Usage Examples

```bash
# 1. Start Isaac daemon for Telegram
C:\> isaac /start -key telegram-webhook tg_secret --daemon
Isaac daemon started (PID 12345)
Listening for commands from: Telegram
Poll interval: 5 seconds

# Meanwhile, in Telegram app:
You: !isaac !ask what's the weather?
Isaac: <AI response about weather>

You: !isaac !projio send -pro my-app | !mine cast
Isaac: ✅ Project sent to Collections (27 files)

You: !isaac !task list
Isaac: 
1. [PENDING] Deploy v2.0 (created 2h ago)
2. [DONE] Fix authentication bug

You: !isaac !task run 1
Isaac: ⚙️ Task started: Deploy v2.0
(continues in background, notifies when done)
```

## Phase 3: !Bang Routing System

### Bang Prefix Registry

**File:** `isaac/core/bang_router.py`

```python
"""
!bang routing system for multi-channel messaging
Routes messages to appropriate bot/persona/service
"""

class BangRouter:
    """Route !bang prefixed messages to handlers"""
    
    ROUTES = {
        "!isaac": "isaac_core",
        "!sarah": "persona_sarah",
        "!daniel": "persona_daniel",
        "!deploy": "bot_deploy",
        "!test": "bot_test",
        "!docs": "bot_docs",
        "!status": "system_status",
        "!help": "help_system"
    }
    
    def route(self, message: str, context: dict) -> dict:
        """Route message to appropriate handler
        
        Args:
            message: Full message text (e.g., "!isaac !ask what's up?")
            context: Source info (telegram user, terminal session, etc.)
        
        Returns:
            Response dict with output and metadata
        """
        parts = message.strip().split(maxsplit=1)
        if not parts or not parts[0].startswith("!"):
            return {"error": "Not a bang command"}
        
        bang = parts[0]
        remaining = parts[1] if len(parts) > 1 else ""
        
        handler = self.ROUTES.get(bang)
        if not handler:
            return {"error": f"Unknown bang: {bang}"}
        
        # Route to handler
        if handler == "isaac_core":
            return self._route_isaac(remaining, context)
        elif handler.startswith("persona_"):
            persona_name = handler.split("_")[1]
            return self._route_persona(persona_name, remaining, context)
        elif handler.startswith("bot_"):
            bot_name = handler.split("_")[1]
            return self._route_bot(bot_name, remaining, context)
        elif handler == "system_status":
            return self._get_status(context)
    
    def _route_isaac(self, command: str, context: dict) -> dict:
        """Route to Isaac command handler"""
        # Execute via CommandRouter
        pass
    
    def _route_persona(self, persona: str, command: str, context: dict) -> dict:
        """Route to persona instance (Sarah, etc.)"""
        # Switch context to persona, execute command
        pass
    
    def _route_bot(self, bot: str, command: str, context: dict) -> dict:
        """Route to specialized bot"""
        # Forward to bot via workspace/token system
        pass
```

### Cross-Channel Message Flow

```
Telegram:
  User: !isaac !ask where is waldo?
  ↓
  Telegram Bot receives message
  ↓
  Enqueues to cloud: {source: "telegram", command: "/ask where is waldo?", key: "telegram-webhook"}
  ↓
  Isaac Daemon polls cloud (every 5s)
  ↓
  Executes: /ask where is waldo?
  ↓
  Result to cloud: {output: "iceland", success: true}
  ↓
  Telegram Bot polls for result
  ↓
  Replies: iceland

Terminal (meanwhile):
  $> /task list
  # Sees same cloud state as Telegram
  # All synced via cloud memory
```

## Phase 4: Humor & Personality

### Rejection Messages (No Key)

```python
# isaac/core/key_manager.py

REJECTION_MESSAGES = [
    "i dont do this shit for free",
    "get a key, pal",
    "nice try, no key = no service",
    "authentication required, buddy",
    "lo siento, pally-o. get a key!",
    "you think I work for free? cute.",
    "key first, questions later"
]

def get_rejection_message() -> str:
    """Random rejection message when no key provided"""
    import random
    return random.choice(REJECTION_MESSAGES)
```

### Invalid Command Messages (Humor Upgrade)

**OLD:**
```
$> funny guy haha
my-name-is-isaac,-use-it
```

**NEW:**
```
$> funny guy haha
'funny' is not a command. 
use /ask or /a to make a query, /help for tips
(or were you just being chatty? I like chatty.)

$> do the thing
'do' is not a command.
Did you mean /do? Or /task? Or just tell me what you want?

$> blarg
'blarg' is not a command.
...but I respect the energy.
```

### Persona Personalities

**Isaac (default):**
- Dry humor, practical, "get shit done" vibe
- Rejections: "i dont do this shit for free"
- Errors: "nice try, but..."

**Sarah (persona):**
- Cheerful, encouraging, design-focused
- Startup: "Coffee is brewing! anyone need me !sarah me, I got /task and shit to do ;)"
- Errors: "Oops! That didn't work. Let me help you..."

**Daniel (future persona):**
- Technical, debugging-focused, detail-oriented
- Startup: "Debug mode engaged. Show me what's broken."

## Implementation Phases

**Phase 1 (Foundation):** Key system, authentication (2-3 days)
- Implement KeyManager class
- Add `-key` flag to /start command
- Create keys.json schema
- Implement rejection messages

**Phase 2 (Daemon Mode):** Background Isaac for webhooks (3-4 days)
- Implement IsaacDaemon class
- Cloud command queue (command_queue.json)
- Polling logic
- Command execution + result return

**Phase 3 (Telegram Bot):** Telegram integration (4-5 days)
- Setup python-telegram-bot
- Implement IsaacTelegramBot class
- !bang routing in Telegram messages
- Test end-to-end: Telegram → Cloud → Daemon → Response

**Phase 4 (Bang Router):** Multi-channel routing (2-3 days)
- Implement BangRouter class
- Register handlers (!isaac, !sarah, !deploy, etc.)
- Cross-channel message coordination

**Phase 5 (Personas):** Sarah/Daniel switching (3-4 days)
- Persona key authentication
- Startup messages and prompts
- Personality customization
- Persona-specific command sets

**Total estimate:** 3-4 weeks

## Success Criteria

- [ ] `/start -key me password` authenticates interactive session
- [ ] `/start -key daemon secret --daemon` runs background Isaac
- [ ] `/ask` without key prints rejection message (humor!)
- [ ] Invalid commands show helpful + humorous messages
- [ ] Telegram bot receives `!isaac !ask` commands
- [ ] Daemon processes Telegram commands, responds
- [ ] All channels sync via cloud memory
- [ ] `/start -key sarah password` switches to Sarah persona
- [ ] Sarah has different personality/responses
- [ ] !bang routing works across Telegram/Terminal

---

**Priority:** HIGH (security foundation for multi-channel access)
**Complexity:** MEDIUM-HIGH (new concepts but clear path)
**Estimated Time:** 3-4 weeks

**Next Steps:**
1. Implement KeyManager and keys.json schema
2. Add `-key` flag to `/start` command
3. Test authentication + rejection messages
4. Implement cloud command queue (command_queue.json on PHP API)
5. Build IsaacDaemon polling loop
6. Setup Telegram bot token, test !bang routing
7. End-to-end test: Control Isaac from Telegram!

---

**The Vision:**
You're in bed, scrolling Telegram. Remember you need to check task status.

You: `!isaac !task list`
Isaac: `1. [DONE] Fix bug, 2. [PENDING] Deploy`

You: `!isaac !task run 2`
Isaac: `⚙️ Deploying...`
(2 minutes later)
Isaac: `✅ Deployment complete! https://my-app.com live`

You never left bed. Isaac handled it. That's the dream. 🚀</content>
<parameter name="filePath">c:\Projects\Isaac-1\.claude\to_implement\messaging_and_key_system.md