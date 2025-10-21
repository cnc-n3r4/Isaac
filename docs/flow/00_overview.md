# ======================================================
# 🧭 ISAAC COMMAND ORCHESTRATION — END-TO-END FLOW
# PURPOSE
#   Provide a unified map of how Isaac processes user input,
#   routes execution, validates risk, and maintains a full
#   chronological audit log.
# ======================================================

# HIGH-LEVEL SWIMLANE
# ┌────────────────────────────────────────────────────────────────────────────┐
# │ USER              │ ORCHESTRATOR       │ VALIDATOR │ EXECUTOR │ CHRONO-LOG │
# ├───────────────────┼────────────────────┼────────────┼──────────┼────────────┤
# │ type command      │ classify(local/    │            │          │            │
# │──────────────────►│ direct/regular)    │            │          │            │
# │                   │                    │            │          │            │
# │ Local (/ask,help) │───────────────────►│            │ execute  │ append(local_exec)│
# │                   │                    │            │          │            │
# │ Direct (`isaac`)  │ execute now        │            │─────────►│ append(exec_start/result)│
# │                   │                    │            │          │            │
# │ Regular Tier≤2    │ execute now        │            │─────────►│ append(exec_start/result)│
# │                   │                    │            │          │            │
# │ Regular Tier≥3    │ ask AI validator   │───────────►│ analyze  │            │
# │                   │◄───────────────────┤ decision   │          │ append(validation_decision)│
# │                   │ SAFE→execute       │            │─────────►│ append(exec_start/result)│
# │                   │ NEEDS_CONFIRM→ask  │            │          │ append(user_confirmation)│
# │ confirm?          │──────────────►Yes/No            │          │ append(cancel_reason if No)│
# │                   │                    │            │          │            │
# │ Done              │                    │            │          │            │
# └────────────────────────────────────────────────────────────────────────────┘

# ======================================================
# MODULE MAP
# 1) Command Classification
#    - Pure function: parse + decide (local | direct | regular).
#    - Determines tier if regular.
#
# 2) Execution & Logging
#    - Routes execution per classification.
#    - Auto-executes Tier ≤2 and direct commands.
#    - Defers Tier ≥3 to Validation.
#    - Appends all chronological log entries.
#
# 3) AI Validation
#    - Evaluates Tier ≥3 commands against history/policy.
#    - Emits JSON decision: SAFE | NEEDS_CONFIRM | DENY.
#    - Pure analysis: no side effects.
#
# 4) User Confirmation
#    - Handles NEEDS_CONFIRM decisions.
#    - Prompts user, logs choice, and either executes or cancels.
#
# 5) Chronological Logger
#    - Append-only, time-ordered record of all events.
#    - Single source of truth for audits and replay.
# ======================================================

# CROSS-MODULE INVARIANTS
#   • Every path emits at least one log entry.
#   • Tier ≤2 never calls validator; Tier ≥3 always does.
#   • NEEDS_CONFIRM requires explicit Yes before action.
#   • Logs are append-only and schema-stable.
#   • Classification & Validation are pure (no side effects).
#   • Execution is effectful; Logging is append-only.
# ======================================================

# PROMPT USAGE (FOR GITHUB COPILOT)
#   Paste this entire overview at the top of a new source file,
#   or open it side-by-side as Copilot context.
#
#   Then add the relevant module header (01–04) below it.
#
#   Example:
#       # include: /docs/flow/00_overview.md
#       # include: /docs/flow/02_execution_logging.md
#       # IMPLEMENTATION STARTS BELOW
#
#   Copilot will infer orchestration flow, logging discipline,
#   and tier behavior from these ASCII and rule blocks.
# ======================================================
