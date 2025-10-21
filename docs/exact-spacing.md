# The Terminal window must be drawn out in Unicode Box Drawing Block / line-drawing glyphs
#  U+2500 to U+257F



┌───────────(TOTAL 80 CHAR FRAME MINIMUM, 58+22=80)───────┬────────────────────┐
│                                                                              │

┌───────────────────────────────╥─────────────────────────╥──────╥──────╥──────┐
│ISAAC vX.Y.Z                   ║SID:xxxx                 ║ #cld ║ #AI  ║ #VPN │
│User: <name> @ <machine name>  ║Last: '<cmd>'            ║ #hst ║ #Log ║ Vl>2 │
│PWD: <cwd>                     ║IP ADDRESS               ║ #CPU ║ #Net ║ W:80 │
╞═══════════════════════════════╩═════════════════════════╩══════╩══════╩══════╡
│$> _                                                                          │
╞══════════════════════════════════════════════════════════════════════════════╡
│I> [OUTPUT]                                                                 ▲ │
│──►[command output scrolls here …]                                          ░ │
│──►(correct spacing must be maintained)                                     ░ │
│──►(from left terminal edge)                                                ░ │
│──►(for all output to maintain 'format')                                    ░ │
│──►(If AIquery responses require multiple unknown quantity lines)           ░ │
│──►(then logic must be built in to determine the correct amount of)         ░ │
│──►(space needed to maintain a neat, professional look and style.)          ░ │
│  ↕ ↕ ONE REQUIRED SPACE BETWEEN FULL COMMANDS AND AIQUERIES REPLIES ↕  ↕   ░ │
│I> [next theoretical more output from another command]                      ░ │
│  ↕ ↕ ONE REQUIRED SPACE BETWEEN FULL COMMANDS AND AIQUERIES REPLIES ↕  ↕   ░ │
│I> [continuing theoretical outputs from more commands]                      ░ │
│                                                                            ░ │
│                                                                            ░ │
│                                                                            ░ │
│                                                                            ░ │
│                                                                            ░ │
│                                                                            ▼ │
└──────────────────────────────────────────────────────────────────────────────┘


## WHEN USER EXPANDS OR CONTRACTS WIDTH

# As terminal window expands, only columns 1 and 2 will expand unrestricted
# the final 3 column must maintain a 8 character maximum length regardless of terminal window size
# As terminal window is expanded Unicode box drawing character '─' and '═' will need to be added or subtracted to maintain a stable appearance upon resize.





# MINIMUM STATUS COLUMNS EXAMPLE



                                                      (minimum width of status area)

┌───────────(TOTAL 80 CHAR FRAME MINIMUM, 58+22=80)────────────────────────────┐
│                                                          #22 MIN WIDE FRAME# │
│                                                         │◄──20Chars─inside──►│
│                                                         │                    │
│◄──(AT MINIMUM FRAME WIDTH ALLOWS 57 MAX INSIDE CHARS)──►│                    │
│                                                         │06char│06char│06char│
│                                                         │◄─max►│◄ins─►│◄only►│
│◄─31chars of expandable area──►│◄──25 chars expandable──►│      │      │      │

┌───────────────────────────────╥─────────────────────────╥──────╥──────╥──────┐
│ISAAC vX.Y.Z                   ║SID:xxxx                 ║ #cld ║ #AI  ║ #VPN │
│User: <name> @ <machine name>  ║Last: '<cmd>'            ║ #his ║ #Log ║ Val>2│
│PWD: <cwd>                     ║IP ADDRESS               ║ #CPU ║ #Net ║ WW:80│
╞═══════════════════════════════╩═════════════════════════╩══════╩══════╩══════╡
│$> _                                                                          │
╞══════════════════════════════════════════════════════════════════════════════╡
│I> [OUTPUT]                                                                 ▲ │
│I> … command output scrolls here …                                          ░ │





                                                                    ┌──(28 WIDEFRAME EXAMPLE)──┐
                                                                    │                          │
                                                                    │◄─26 Chars inside width ─►│
│◄─────────────────(expandable multiple column area)───────────────►│                          │
│                                                                   │8 char  │8 char  │8 char  │
│                                                                   │◄width ►│◄exampl►│◄only──►│
│◄───────expandable column───────────►│◄────expandable column──────►│        │        │        │

┌─────────────────────────────────────╥─────────────────────────────╥────────╥────────╥────────┐
│ISAAC vX.Y.Z                         ║SID:xxxx                     ║ #cloud ║ #AIsta ║ #VPNst │
│User: <name> @ <machine name>        ║Last: '<cmd>'                ║ #hist  ║ #Log   ║ Val>2  │
│PWD: <cwd>                           ║IP ADDRESS                   ║ #CPU % ║ #Net   ║ WW:80  │
╞═════════════════════════════════════╩═════════════════════════════╩════════╩════════╩════════╡
♦$> _                                                                                          │
╞══════════════════════════════════════════════════════════════════════════════════════════════╡
│I> [OUTPUT]                                                                                 ▲ │
│I> … command output scrolls here …                                                          ░ │
│                                                                                            ░ │




# MAXIMUM STATUS COLUMNS EXAMPLE
₦
                                                                                  (maximum width of status area)

                                                                                        ### IMPORTANT ###
                                                                                ┌─(MAINTAIN STRICT 34 MAX WIDTH)─┐
                                                                                │                                │
                                                                                │◄─────32─Chars─Maximum─inside──►│
│◄─────────────────exapandable─double─column─area──────────────────────────────►│                                │
│                                                                               │                                │
│                                                                               │10char ax │10char max│10char max│
│                                                                               │◄ MAXIMUM►│◄ MAXIMUM►│◄ MAXIMUM►│
│◄─────────expandable column────────────── ►|◄─────────expandable column───────►│          │          │          │

┌───────────────────────────────────────────╥───────────────────────────────────╥──────────╥──────────╥──────────┐
│ISAAC vX.Y.Z                               ║SID:xxxx                           ║  #cloud  ║   #AI    ║  #VPN    │
│User: <name> @ <machine name>              ║Last: '<cmd>'                      ║  #hist   ║   #Log   ║ Val>2.5  │
│PWD: <cwd>                                 ║IP ADDRESS                         ║  #CPU %  ║   #Net   ║ Wrap:80  │
╞═══════════════════════════════════════════╩═══════════════════════════════════╩══════════╩══════════╩══════════╡
│$> _                                                                                                            │
╞════════════════════════════════════════════════════════════════════════════════════════════════════════════════╡
│I> [OUTPUT]                                                                                                   ▲ │
│I> … command output scrolls here …                                                                            ░ │




## MINIMUM TERMINAL WINDOW HEIGHT




┌───────────           (TOTAL 80 CHAR FRAME MINIMUM)  ────┬────────────────────┐
│                                                         │                    │
│                                                         │                    │

┌───────────────────────────────╥─────────────────────────╥──────╥──────╥──────┐1  ▲
│ISAAC vX.Y.Z                   ║SID:xxxx                 ║ #cld ║ #AI  ║ #VPN │2  │
│User: <name> @ <machine name>  ║Last: '<cmd>'            ║ #hst ║ #Log ║ Vl>2 │3  │
│PWD: <cwd>                     ║IP ADDRESS               ║ #CPU ║ #Net ║ W:80 │4  │
╞═══════════════════════════════╩═════════════════════════╩══════╩══════╩══════╡5  │
│$> _                                                                          │6  │
╞══════════════════════════════════════════════════════════════════════════════╡7  │
│I> [OUTPUT]                                                                 ▲ │8  │
│...[command output scrolls here …]                                          ░ │9  │
│                                                                            ░ │0  │
│                                                                            ░ │1  │
│                                                                            ░ │2  │
│                                                                            ░ │3  │◄────[OUTPUT 25 CHAR MIN HEIGHT]
│                                                                            ░ │4  │
│                                          [OUTPUT MUST BE SCROLLABLE]─────► ░ │5  │
│                                                                            ░ │6  │
│                                                                            ░ │7  │
│                                                                            ░ │8  │
│                                                                            ░ │9  │
│                                                                            ░ │0  │
│                                                                            ░ │1  │
│                                                                            ░ │2  │
│                                                                            ░ │3  │
│                                                                            ▼ │4  │
└──────────────────────────────────────────────────────────────────────────────┘5  ▼
