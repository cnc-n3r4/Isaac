┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ USER            │ ORCHESTRATOR         │ VALIDATOR           │ EXECUTOR   │ CHRONO-LOG │  UI  │
├─────────────────┼──────────────────────┼─────────────────────┼────────────┼────────────┼──────┤
│ type command    │ classify(local/      │                     │            │            │      │
│───────────────► │ direct/regular,tier) │                     │            │            │      │
│                 │                      │                     │            │            │      │
│                 │ emit classification  │                     │            │            │      │
│                 │───────────────┬──────│                     │            │            │      │
│                 │               │      │                     │            │            │      │
│                 │               │      │                     │            │            │      │
│                 │               ▼      │                     │            │            │      │
│                 │ [Tier≤2 or Direct]?  │                     │            │            │      │
│                 │ Yes ─────────►       │                     │            │            │      │
│                 │                      │                     │ exec_start │            │      │
│                 │                      │                     │───────────►│ append     │      │
│                 │                      │                     │ exec_result│            │      │
│                 │                      │                     │───────────►│ append     │      │
│                 │                      │                     │            │            │      │
│                 │ No (Tier≥3) ─────────┼──────────► analyze  │            │            │      │
│                 │                      │ decision JSON       │            │            │      │
│                 │◄─────────────────────┤ SAFE/CONFIRM/DEN Y  │            │ append(dec)│      │
│                 │ if SAFE → execute    │                     │ exec_*     │────────────┤      │
│                 │ if CONFIRM → prompt  │                     │──────────► │ append     │      │
│                 │ if DENY → stop       │                     │            │            │      │
│                 │                      │                     │            │            │      │
│ confirm? Yes ──►│ execute              │                     │ exec_*     │ append     │      │
│ confirm? No  ──►│ cancel               │                     │ —          │ append(cancel)    │
│                 │                      │                     │            │            │      │
│ Done            │                      │                     │            │            │      │
└───────────────────────────────────────────────────────────────────────────────────────────────┘

HEADER UPDATE HOOKS (UI):
• H0: On classification emitted  → update “Mode”, “Tier”, “Last: '<cmd>'”
• H1: On validation_start/decision→ update #AI status + decision badge (SAFE/CONFIRM/DENY)
• H2: On exec_start               → pulse Mode:<EXEC>, bump Hist count
• H3: On exec_result              → update #CPU/#Net snapshot, turn Mode idle, refresh Last:'<cmd>'
• H4: On user_confirmation        → flash confirm result (Yes/No) in #Log/#AI cell
• H5: On cancel/deny              → show short reason tag in status cluster
• H6: On prompt focus change      → draw the white/blocked prompt line





┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER CELLS                 | SOURCE OF TRUTH                              │
├──────────────────────────────┼──────────────────────────────────────────────┤
│ ISAAC vX.Y.Z                 | build/version config                         │
│ SID:xxxx                     | session manager                              │
│ Mode:<EXEC/IDLE/CONFIRM>     | orchestrator state machine (H0/H1/H2/H3)     │
│ User:<name>@<machine>        | environment/session                          │
│ Last:'<cmd>'                 | last executed/attempted cmd (H0/H3)          │
│ Hist:### / #Log              | chronological log count (append-only)        │
│ PWD:<cwd>                    | process working dir                          │
│ IP:<address>                 | network snapshot (periodic or per exec)      │
│ #cld/#AI/#VPN/#hst/#CPU/#Net | status adapters (green=on, yellow=check,     │
│                              | gray=off; updated on H1,H2,H3 or timer)      │
│ Vl>2 (Tier label)            | classification decision (H0)                 │
│ Wrap:80                      | renderer setting                             │
└─────────────────────────────────────────────────────────────────────────────┘






┌─────────────────────────────────────────────┐
│ EVENT                                       │
├─────────────────────────────────────────────┤
│ 1) New input detected                       │
│    → classify → set Tier/Mode               │
│    → H0: render header (Last, Tier, Mode)   │
│                                             │
│ 2) If Tier≥3 → validation_start             │
│    → H1: #AI=busy, Mode:CONFIRM? (pending)  │
│                                             │
│ 3) Decision: SAFE                           │
│    → exec_start                             │
│    → H2: Mode:EXEC, Hist+1, #CPU/#Net snap  │
│    → exec_result                            │
│    → H3: Mode:IDLE, Last:'<cmd>'            │
│                                             │
│ 4) Decision: NEEDS_CONFIRM                  │
│    → H1: tag “CONFIRM” in #AI cell          │
│    → prompt user; on Yes → go to (3)        │
│    → on No → cancel → H5                    │
│                                             │
│ 5) Decision: DENY                           │
│    → log deny → H5 with reason              │
│                                             │
│ 6) Prompt focus change / idle tick          │
│    → H6: draw white/blocked prompt line     │
│    → optional periodic #CPU/#Net refresh    │
└─────────────────────────────────────────────┘




Line 1: ISAAC vX.Y.Z | SID:xxxx     | [#cloud][#AI][#VPN]
Line 2: <user>@<machine> | Last:'x' | Hist:### [#log] [Tier]
Line 3: PWD:<cwd> | IP:<ip>         | [#CPU][#Net] Wrap:80

Column widths: ~34 | ~28 | ~18  (fixed-fit to frame)
Prompt line: white background + block cursor (always current)
Output area: scroll region beneath the header + prompt line







Line 1: ISAAC vX.Y.Z | SID:xxxx     | [#cloud][#AI][#VPN]
Line 2: <user>@<machine> | Last:'x' | Hist:### [#log] [Tier]
Line 3: PWD:<cwd> | IP:<ip>         | [#CPU][#Net] Wrap:80

Column widths: ~34 | ~28 | ~18  (fixed-fit to frame)
Prompt line: white background + block cursor (always current)
Output area: scroll region beneath the header + prompt line
