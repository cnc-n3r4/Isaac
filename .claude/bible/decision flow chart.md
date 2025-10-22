                         ┌──────────────────────────────┐
                         │          User input          │
                         └───────────────┬──────────────┘
                                         │
                             ┌───────────▼───────────┐
                             │  Classify command:    │
                             │  local? direct? tier? │
                             └───────┬─────┬─────────┘
                                     │     │
                         Local       │     │  Direct exec: `isaac <cmd>`
                    (/ask, /help,…)  │     │
                               ┌─────▼───┐ │
                      ┌───────►│ Execute │ │
                      │        │  local  │ │
                      │        └─────┬───┘ │
                      │              │     │
                      │    ┌─────────▼─────▼─────────┐
                      │    │  LOG append (chron.)    │
                      │    │  event=local_exec       │
                      │    └─────────┬───────────────┘
                      │              │
                      │              ▼
                      │        ┌──────────┐
                      │        │   Done   │
                      │        └──────────┘
                      │
                      │                 ┌─────────────────────────────────┐
                      │                 │ Direct execution: `isaac <cmd>` │
                      │                 │   ► bypass validation           │
                      │                 └───────────┬─────────────────────┘
                      │                             │
                      │                     ┌───────▼───────┐
                      │                     │  Execute now  │
                      │                     └───────┬───────┘
                      │                             │
                      │                ┌────────────▼────────────┐
                      │                │ LOG append (chron.)     │
                      │                │ event=exec_start/result │
                      │                └────────────┬────────────┘
                      │                             │
                      │                             ▼
                      │                       ┌──────────┐
                      │                       │   Done   │
                      │                       └──────────┘
                      │
                      │           Regular (no prefix) Tier 1-2
                      │           ┌──────────▼───────────┐
                      └──────────►│   AI Validation      │
                                  │ (history → analysis  │
                                  │  → JSON decision)    │
                                  └──────────┬───────────┘
                                             │
                         ┌───────────────────▼──────────────────┐
                         │ LOG append (chron.) event=validation │
                         └───────────────────┬──────────────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │  SAFE or NEEDS    │
                                   │  explicit confirm?│
                                   └─────────┬─────────┘
                                             │
                                 Yes (SAFE)  │  No / Needs confirm
                                             │
                                   ┌─────────▼─────────┐
                                   │   Execute cmd     │
                                   └─────────┬─────────┘
                                             │
                          ┌──────────────────▼──────────────────┐
                          │ LOG app (chron.) exec_start/result  │
                          └──────────────────┬──────────────────┘
                                             │
                                             ▼
                                        ┌─────────┐
                                        │  Done   │
                                        └─────────┘

If Needs Confirm:
    ┌──────────────────────────────────────────────────────────┐
    │ Prompt user → receive Yes/No → LOG append (confirmation) │
    └───────┬──────────────────────────────────────────────────┘
            │Yes                                     │No
            ▼                                        ▼
      Execute cmd                              Cancel operation
            │                                        │
   LOG exec_start/result                    LOG cancel_reason
            ▼                                        ▼
          Done                                     Done


User            Isaac Orchestrator          AI Validator              Executor            Chronological Log
│                     │                           │                      │                       │
│ type cmd            │                           │                      │                       │
├────────────────────►│ classify(local/direct/tier)                      │                       │
│                     │─────────────────────────────────────────────────►│                       │
│                     │ if local: run local                              │                       │
│                     │─────────────────────────────────────────────────►│                       │
│                     │                                                  │◄──────────────────────┤ append(event=local_exec, …)
│                     │                                                  │                       │
│ Direct exec:        │ execute immediately (no validation)              │                       │
│ `isaac <cmd>`       │─────────────────────────────────────────────────►│                       │
│                     │                                                  │◄──────────────────────┤ append(exec_start/result, …)
│                     │                                                  │                       │
│ Tier 1-2 (no prefix)│ fetch history → ask AI                           │                       │
│                     │───────────────────────────────►│ analyze         │                       │
│                     │                                │───────────JSON──┤                       │
│                     │◄───────────────────────────────┘                 │◄──────────────────────┤ append(validation_decision, …)
│                     │ if SAFE → execute                                │                       │
│                     │─────────────────────────────────────────────────►│                       │
│                     │                                                  │◄──────────────────────┤ append(exec_start/result, …)
│ Tier 3+             │ fetch history → ask AI                           │                       │
│                     │───────────────────────────────►│ analyze         │                       │
│                     │                                │───────────JSON──┤                       │
│                     │◄───────────────────────────────┘                 │◄──────────────────────┤ append(validation_decision, …)
│                     │ if SAFE → execute                                │                       │
│                     │─────────────────────────────────────────────────►│                       │
│                     │                                                  │◄──────────────────────┤ append(exec_start/result, …)
│ Needs confirm       │ prompt user (Yes/No)                             │                       │
│ confirm? ─────────► │                                                  │◄──────────────────────┤ append(user_confirmation, …)
│ Yes → execute       │─────────────────────────────────────────────────►│                       │
│ No  → cancel        │                                                  │◄──────────────────────┤ append(cancel_reason, …)
│                     │                                                  │                       │


Swimlane:

User            Isaac Orchestrator          AI Validator              Executor           Chronological Log
│                     │                           │                      │                      │
│ type cmd            │                           │                      │                      │
├────────────────────►│ classify(local/direct/tier)                      │                      │
│                     │─────────────────────────────────────────────────►│                      │
│                     │ if local: run local                              │                      │
│                     │─────────────────────────────────────────────────►│                      │
│                     │                                                  │◄─────────────────────┤ append(event=local_exec, …)
│                     │                                                  │                      │
│ Direct exec:        │ execute immediately (no validation)              │                      │
│ `isaac <cmd>`       │─────────────────────────────────────────────────►│                      │
│                     │                                                  │◄─────────────────────┤ append(exec_start/result, …)
│                     │                                                  │                      │
│ Tier 1-2 (no prefix)│ fetch history → ask AI                           │                      │
│                     │───────────────────────────────►│ analyze         │                      │
│                     │                                │───────────JSON──┤                      │
│                     │◄───────────────────────────────┘                 │◄─────────────────────┤ append(validation_decision, …)
│                     │ if SAFE → execute                                │                      │
│                     │─────────────────────────────────────────────────►│                      │
│                     │                                                  │◄─────────────────────┤ append(exec_start/result, …)
│ Tier 3+             │ fetch history → ask AI                           │                      │
│                     │───────────────────────────────►│ analyze         │                      │
│                     │                                │───────────JSON──┤                      │
│                     │◄───────────────────────────────┘                 │◄─────────────────────┤ append(validation_decision, …)
│                     │ if SAFE → execute                                │                      │
│                     │─────────────────────────────────────────────────►│                      │
│                     │                                                  │◄─────────────────────┤ append(exec_start/result, …)
│ Needs confirm       │ prompt user (Yes/No)                             │                      │
│ confirm? ─────────► │                                                  │◄─────────────────────┤ append(user_confirmation, …)
│ Yes → execute       │─────────────────────────────────────────────────►│                      │
│ No  → cancel        │                                                  │◄─────────────────────┤ append(cancel_reason, …)
│                     │                                                  │                      │