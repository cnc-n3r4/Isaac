                                  ┌──────────────────────┐
                                  │      Telegram        │
                                  │   /list …, /add …    │
                                  │   !labpc ls …        │
                                  └─────────┬────────────┘
                                            │  (TLS)
                                            ▼
                 ┌───────────────────────────────────────────────────────┐
                 │                CLOUD RELAY / HUB                      │
                 │  (Auth, Routing, Webhooks, Histories, Search)        │
                 │                                                       │
                 │  ┌───────────────────────────┐   ┌──────────────────┐ │
     (global)    │  │  AI_CHAT_HISTORY (GLOBAL)│   │ CMD_HISTORY_DB   │ │ (per-terminal)
  APPEND + QUERY │  │  (merged across machines)│   │ (partitioned by   │ │  APPEND + QUERY
                 │  └───────────────▲──────────┘   │  terminal_id)    │ │
                 │                  │              └─────────▲─────────┘ │
                 │                  │                        │           │
                 │     ┌────────────┴────────────┐  ┌────────┴─────────┐ │
                 │     │   MERGED_QUERY_LAYER    │  │  LLM API PROXY   │ │
                 │     │ (/search across chat +  │  │  (provider)      │ │
                 │     │  commands with filters) │  └────────┬─────────┘ │
                 │     └────────────┬────────────┘           │           │
                 └──────────────────┼─────────────────────────┼───────────┘
                                    │                         │
                         (A) Terminal/Local path              │ (C) AI calls
                                    │                         │
   ┌──────────────────────────────┐  │                         │
   │  MACHINE: DESKTOP            │  │                         │
   │  ┌────────────────────────┐  │  │                         │
   │  │  LOCAL SHELL #1        │──┼──┼───► / or ! parsed       │
   │  └────────────────────────┘  │  │                         │
   │  ┌────────────────────────┐  │  │                         │
   │  │  LOCAL SHELL #2        │──┼──┘                         │
   │  └────────────────────────┘  │                            │
   │  ┌────────────────────────┐  │                            │
   │  │ ISAAC INTERPRETER      │◄─┘                            │
   │  │  if line startswith("/") → local meta command          │
   │  │  if line startswith("!") → route to target machine     │
   │  │  else → pass to OS shell or NLQ                        │
   │  └───────────┬────────────┘                               │
   │              │                                            │
   │     (exec local)                                          │
   │              ▼                                            │
   │  ┌────────────────────────┐                                │
   │  │  LOCAL EXECUTOR        │  stdout/stderr/artifacts ──────┼──────►
   │  └───────────┬────────────┘                                │
   │              │  (B) Append local command results           │
   │              └───────────────►  CLOUD: CMD_HISTORY_DB ◄────┘
   │                                   (partitioned by terminal_id)
   │
   └─────────────────────────────────────────────────────────────────────

                     (D) Remote routing via !bang
          ┌───────────────────────────────┐
          │  CLOUD ROUTER (target=labpc) │
          └───────────────┬──────────────┘
                          │  (poll/queue)
                          ▼
              ┌──────────────────────────────┐
              │ MACHINE: LABPC (isaacd)      │
              │  • polls jobs from CLOUD     │
              │  • verifies HMAC/TTL/allow   │
              │  • executes & returns        │
              └───────────┬──────────────────┘
                          │  results (stdout/files)
                          └──────► CLOUD: CMD_HISTORY_DB (terminal_id=labpc)

   (E) Telegram reverse exec:
   Telegram / ! → CLOUD webhook → route to target agent → execute → result back to Telegram
   (results also appended to CMD_HISTORY_DB; conversational replies to AI_CHAT_HISTORY when applicable)


   ────────────────────────────────────────────────────────────────────────────────
   SEARCH & CONTEXT FLOWS
   ────────────────────────────────────────────────────────────────────────────────
   • `/search "ffmpeg"` (from any shell or Telegram)
       └─► CLOUD: MERGED_QUERY_LAYER → queries AI_CHAT_HISTORY + CMD_HISTORY_DB
             - filters: kind=(chat|cmd|both), terminal_id=?, time range, text FTS
             - returns hits; optional inline pagination/buttons (Telegram)

   • NLQ (natural language query) from shell/Telegram
       └─► CLOUD collects GLOBAL chat context (AI_CHAT_HISTORY)
             └─► LLM API PROXY → PROVIDER → response
                   └─► append request/response to AI_CHAT_HISTORY (GLOBAL)

   • Per-terminal ↑/↓ history recall (local shells)
       └─► reads from CMD_HISTORY_DB filtered by terminal_id=that shell’s id

