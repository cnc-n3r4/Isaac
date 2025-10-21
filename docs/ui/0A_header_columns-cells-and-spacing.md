                                                    
                                         +-------------------------------------+
                                         | content in these 3 columns that all |
                                         | start with a #hash tag can all have |
                                         | their STATUS represented by the     |
                                         | color of the TEXT that represents   |
                                         | its respective function. e.g. if AI |
                                         | is green/yellow/gray = on/check/off 
                                         +-------------------------------------+
                                                              |      |      | 
                                                              |      |      |
                                                              |      |      |
                                                              |      |      |
                                                              |      |      |    
                                                              |      |      |
                                                              v      v      v  
| column 1                      | column 2                |   3  |   4  |   5  
┌───────────────────────────────╥─────────────────────────╥──────╥──────╥──────┐
│ISAAC vX.Y.Z                   ║SID:xxxx                 ║ #cld ║ #AI  ║ #VPN │
│User: <name> @ <machine name>  ║Last: '<cmd>'            ║ #hst ║ #Log ║ Vl>2 │
│PWD: <cwd>                     ║IP ADDRESS               ║ #CPU ║ #Net ║ W:80 │
╞═══════════════════════════════╩═════════════════════════╩══════╩══════╩══════╡
│ > _ (CHANGE THIS LINE IS WHITE BACKGROUND WITH BLACK TEXT)                   │
╞══════════════════════════════════════════════════════════════════════════════╡ 
│ [OUTPUT]                                                                     │
│   … command output scrolls here …                                            │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

It should be like this                                                                
                                                                                      
Header Structure (3-line format):                                                     
                                                                                      
Line 1: ISAAC vX.Y.Z | SID:xxxx | #cloud | #AI | #VPN                                 
Column 1: ~34 chars (ISAAC version)                                                   
Column 2: ~28 chars (Session ID)                                                      
Column 3: ~18 chars (Color-coded status indicators)                                   
                                                                                      
Line 2: <name>@<machine> | Last: '<cmd>' | Hist:### | #log | <#Tier Value>            
Column 1: ~34 chars (Shows User @ machine info)                                       
Column 2: ~28 chars (last command)                                                    
Column 3: ~18 chars (history, log and Color-coded status of tier)                     
                                                                                      
Line 3: | PWD: <cwd> | IP: <ip> | #CPU% | #Net | Wrap:80                              
Column 1: ~34 chars (working directory)                                               
Column 2: ~28 chars (Ip address)                                                      
Column 3: ~18 chars ( Color-coded status indicators for CPU & Network , with wordwrap)




┌───────────────────────────────╥─────────────────────────╥──────╥──────╥──────┐
│ISAAC vX.Y.Z                   ║SID:xxxx                 ║ #cld ║ #AI  ║ #VPN │
│User: <name> @ <machine name>  ║Last: '<cmd>'            ║ #hst ║ #Log ║ Vl>2 │
│PWD: <cwd>                     ║IP ADDRESS               ║ #CPU ║ #Net ║ W:80 │
╞═══════════════════════════════╩═════════════════════════╩══════╩══════╩══════╡
      ( ^^ this header area dynamically updates as commands are execute ^^ )




╞═══════════════════════════════╩═════════════════════════╩══════╩══════╩══════╡
│$.> _ (CHANGE THIS LINE IS WHITE BACKGROUND WITH A BLOCK)                     │
╞══════════════════════════════════════════════════════════════════════════════╡ 
  ( ^^ this area is always the current prompt line ^^ )




╞══════════════════════════════════════════════════════════════════════════════╡ 
│ [OUTPUT]                                                                     │
│   … command output scrolls here …                                            │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘