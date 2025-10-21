The Terminal window must be drawn out in Unicode Box Drawing Block / line-drawing glyphs
 U+2500 to U+257F
 



A minimum 80 charater width will be drawn with Unicode Box Drawing Block
12345678901234567890123456789012345678901234567890123456789012345678901234567890
         │         │         │         │         │         │         │         │
         │         │         │         │         │         │         │         │
         │         │         │         │         │         │         │         │



|<--- 35chars of space here --->|<-25chars of space here->|06char|06char|06char|
┌───────────────────────────────╥─────────────────────────╥──────╥──────╥──────┐
│ISAAC vX.Y.Z                   ║SID:xxxx                 ║ #cld ║ #AI  ║ #VPN │
│User: <name> @ <machine name>  ║Last: '<cmd>'            ║ #hst ║ #Log ║ Vl>2 │
│PWD: <cwd>                     ║IP ADDRESS               ║ #CPU ║ #Net ║ W:80 │
╞═══════════════════════════════╩═════════════════════════╩══════╩══════╩══════╡
│$> _                                                                          │
╞══════════════════════════════════════════════════════════════════════════════╡ 
│I> [OUTPUT]                                                                 ▲ │
│→→→[command output scrolls here …]                                          ░ │
│→→→(correct spacing must be maintained)                                     ░ │
│→→→(from left terminal edge)                                                ░ │
│→→→(for all output to maintain 'format')                                    ░ │
│→→→(If AIquery responses require multiple unknown quantity lines)           ░ │
│→→→(then logic must be buiult in to determine the correct amount of)        ░ │ 
│→→→(space needed to maintain a neat, professional look and style.)          ░ │ 
│ # ↕ # ↕ #  ONE REQUIRED SPACE BETWEEN COMMANDS AND AIQUERIES  # ↕ # ↕ #    ░ │ 
│I> [next theoretical more output from another command]                      ░ │ 
│ # ↕ # ↕ #  ONE REQUIRED SPACE BETWEEN COMMANDS AND AIQUERIES  # ↕ # ↕ #    ░ │
│I> [continuing theoretical outputS from more commands]                      ░ │ 
│                                                                            ░ │ 
│                                                                            ░ │ 
│                                                                            ░ │ 
│                                                                            ░ │ 
│                                                                            ░ │ 
│                                                                            ▼ │ 
└──────────────────────────────────────────────────────────────────────────────┘ 


## WHEN USER EXPANDS OR CONTRACTS WIDTH 

# As terminal window expands, only columns 1 and 2 will expand unrestriced
# the final 3 column must maintain a 8 character maximum length regardless of terminal window size
# As terminal window is expanded Unicaode box drawing character '─' and '═' will need to be added or subtracted to maintain a stable appearance upon resize.



|<---    expandable column  ---->     |<-   expandable column     ->|8charmax|8charmax|8charmax|
┌─────────────────────────────────────╥─────────────────────────────╥────────╥────────╥────────┐
│ISAAC vX.Y.Z                         ║SID:xxxx                     ║ #cloud ║ #AIsta ║ #VPNst │
│User: <name> @ <machine name>        ║Last: '<cmd>'                ║ #hist  ║ #Log   ║ Val>2  │
│PWD: <cwd>                           ║IP ADDRESS                   ║ #CPU % ║ #Net   ║ WW:80  │
╞═════════════════════════════════════╩═════════════════════════════╩════════╩════════╩════════╡
│$> _                                                                                          │
╞══════════════════════════════════════════════════════════════════════════════════════════════╡ 
│I> [OUTPUT]                                                                                 ▲ │
│I> … command output scrolls here …                                                          ░ │
│                                                                                            ░ │



# The terminal box must not be drawn under 80 chars wide or 25 chars in height


|<--- 35chars of space here --->|<-25chars of space here->|06char|06char|06char|
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
                                                                                   