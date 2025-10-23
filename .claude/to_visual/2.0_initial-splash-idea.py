import time
import sys
import os
import pyfiglet
from colorama import Fore, Style

# Clear screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Typing effect with blinking underscore
def typing_effect(text, delay=0.1, cursor_delay=0.5):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    # Blinking underscore
    for _ in range(3): # Blink 3 times
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(cursor_delay)
               
    #sys.stdout.write('_') # Final underscore

# Main splash
clear_screen()

# Type "would you like to play"
typing_effect("would you like to play")
time.sleep(1) # Pause with blinking (already in typing)

# Add "._" with pause
sys.stdout.write('.')
sys.stdout.flush()
time.sleep(.03)
typing_effect("") # Just for blinking pause

# Add ".._" with "a game?"
sys.stdout.write('.')
sys.stdout.flush()
time.sleep(1)
typing_effect("a game?")
time.sleep(1) # Pause couple seconds

# Blank screen
clear_screen()

# "nah!!" in middle
lines = os.get_terminal_size().lines // 2 - 1
for _ in range(lines):
    print()
print("nah!!".center(os.get_terminal_size().columns))
sys.stdout.flush()
time.sleep(1)

# Clear and scroll down "isaac"
clear_screen()
ascii_art = pyfiglet.figlet_format("Isaac", font="big").splitlines()
for line in ascii_art:
    print(line.center(os.get_terminal_size().columns))
    sys.stdout.flush()
    time.sleep(0.05)
   
# After scrolling "isaac"
acronym = f"{Fore.LIGHTGREEN_EX}I{Fore.RESET}ntelligent {Fore.LIGHTGREEN_EX}S{Fore.RESET}ystem {Fore.LIGHTGREEN_EX}A{Fore.RESET}gent {Fore.LIGHTGREEN_EX}A{Fore.RESET}nd {Fore.LIGHTGREEN_EX}C{Fore.RESET}ontrol"
print(acronym.center(os.get_terminal_size().columns))
print("Type 'isaac --help' for assistance".center(os.get_terminal_size().columns))
sys.stdout.flush()
time.sleep(2) # Pause

# System prompt (simple input)
input("> ")

# Hold
input("Press Enter to exit...")