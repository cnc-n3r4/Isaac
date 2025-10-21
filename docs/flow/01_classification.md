# ======================================================
# 📄 DOC: Command Classification
# PURPOSE
#   Decide the initial route for any input:
#     • Local (/ask, /help, …)
#     • Direct exec (`isaac <cmd>`) — bypass validation
#     • Regular (no prefix) with tier (1..N)
# OUTCOME
#   Produce a side-effect-free classification object for downstream modules.
# ======================================================

# ASCII FLOW (CLASSIFY ONLY)
# ┌──────────────────────────────┐
# │          User input          │
# └───────────────┬──────────────┘
#                 │
#     ┌───────────▼───────────┐
#     │  Parse + Classify:    │
#     │  local? direct? tier? │
#     └───────┬─────┬─────────┘
#             │     │
#   Local     │     │   Direct exec
#  (/ask…)    │     │   (`isaac <cmd>`)
#    │        │     │
#    ▼        │     ▼
#  Local      │  Direct
#  Route      │  Route
#             │
#             ▼
#         Regular Route
#         (no prefix)
#         → Tier 1..N

# CONTRACT (I/O)
# INPUT:
#   - raw_user_input (string)
#   - local command patterns (/ask, /help, etc.)
#   - tiering rules or heuristic (deterministic)
# OUTPUT:
#   - classification:
#       kind: local | direct | regular
#       tier: null | int
#       normalized_command: string

# INVARIANTS
#   - Pure function: no execution, no logging here.
#   - Same input + history window ⇒ same tier.
#   - normalization (quoting/whitespace) is consistent.

# HANDOFF
#   - Pass classification to Execution & Logging module.
