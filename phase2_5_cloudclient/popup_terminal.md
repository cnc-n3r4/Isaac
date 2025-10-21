
Concept Overview:
Essentially create a "parent-child" relationship between two CLI windows:
- PARENT: Your original terminal/shell (e.g., PowerShell on Win, Bash on Linux).
- CHILD: A new, independent window spawned from the parent (another shell instance).
  - It's like forking an app: separate process, but you can "phone home" via remoting to send commands/results.
- Goal: Run stuff in the child for isolation (e.g., long-running task without cluttering parent), but control/monitor it from parent.
- Key Twist: Without remoting, they're fire-and-forget (no input/control link). With remoting (PS Remoting/SSH), you bridge them—input from parent executes in child, output flows back (visible in parent live, or echoed in child).

Expanded Flow Sketch (Generic: Works for Win/Linux; swap tools as needed):

                          +-------------------------------------+
                          |            MY GOAL:                 |
                          |  Juggle 2+ CLI sessions in separate |
                          |  windows, but control one from the  |
                          |  other remotely (like SSH to self). |
                          |                                     |
                          |  Why? Isolation + Monitoring w/o    |
                          |  manual switching. E.g., run a      |
                          |  script in child, watch/log from    |
                          |  parent.                            |
                          +-------------------------------------+
                                       |
                                       v
    +-------------------+     LAUNCH     +-------------------+
    |   PARENT WINDOW   |   (Spawn New)  |   CHILD WINDOW    |
    |                   |  ------------> |                   |
    |  (Active/Focused) |                 |  (New/Idle)       |
    |                   |                 |                   |
    |  $ start powershell|                 |  PS> _            |  <-- Starts empty/inherits dir
    |     (Win)         |                 |                   |
    |  $ gnome-terminal |                 |  $ _              |  <-- Bash prompt ready
    |     (Linux)       |                 |                   |
    |                   |                 |                   |
    |  [You type here]  |                 |  [Shows output if |
    |                   |                 |   interactive]    |
    +-------------------+                 +-------------------+
                                       |
                                       |  SETUP BRIDGE (One-Time)
                                       |  - Win: Enable-PSRemoting
                                       |  - Linux: sudo apt install openssh-server; systemctl start ssh
                                       v
    +-------------------+     REMOTE LINK (Control Flow)    +-------------------+
    |   PARENT WINDOW   |  <---------->  |   CHILD WINDOW    |
    |                   |                 |                   |
    |  INPUT: You type  |                 |  EXEC: Runs cmds  |
    |  cmds here...     |  (SSH/PSRemoting) |  in its session  |
    |                   |                 |                   |
    |  OUTPUT: See live |                 |  ECHO: May show   |
    |  results here     |  <------------- |  same output      |
    |  (hijacked I/O)   |                 |  (if not silenced)|
    |                   |                 +-------------------+
    |  Examples:        |                           ^
    |  - Win: Enter-PSSession localhost  |           |
    |    (types in parent, runs in child)|           |  NON-INTERACTIVE (Fire & Get Results)
    |  - Linux: ssh localhost             |           |  - Parent: ssh localhost "ls -la"
    |    (same hijack)                    |           |    --> Results BACK to parent
    |  - Or: Invoke-Command (send w/o     |           |  - Child: Just executes quietly
    |    hijack; results return to parent)|           |
    +-------------------+                 +-----------+
                                       |
                                       v
                          +-------------------------------------+
                          |         LIMITS & ALTERNATIVES:      |
                          |  - Input: Not "click & type" in     |
                          |    child; it's remote (type in      |
                          |    parent, see in parent).          |
                          |  - Visibility: Full in parent;      |
                          |    partial/mirrored in child.       |
                          |                                     |
                          |  Better for "one window"? Use:      |
                          |  - Win: Windows Terminal (split     |
                          |    panes/tabs w/ Ctrl+Shift+5)      |
                          |  - Linux: tmux (Ctrl+B % to split;  |
                          |    switch w/ arrows). No remoting   |
                          |    needed—shared process!           |
                          +-------------------------------------+
