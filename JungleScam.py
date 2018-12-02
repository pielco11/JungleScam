from colorama import init
init()
from colorama import Fore, Back, Style

print (Fore.YELLOW + """
888888                            888           .d8888b.
    "88b                            888          d88P  Y88b
     888                            888          Y88b.
     888 888  888 88888b.   .d88b.  888  .d88b.   "Y888b.    .d8888b  8888b.  88888b.d88b.
     888 888  888 888 "88b d88P"88b 888 d8P  Y8b     "Y88b. d88P"        "88b 888 "888 "88b
     888 888  888 888  888 888  888 888 88888888       "888 888      .d888888 888  888  888
     88P Y88b 888 888  888 Y88b 888 888 Y8b.     Y88b  d88P Y88b.    888  888 888  888  888
     888  "Y88888 888  888  "Y88888 888  "Y8888   "Y8888P"   "Y8888P "Y888888 888  888  888
   .d88P                        888
 .d88P"                    Y8b d88P
888P"                       "Y88P"
""")
print (Fore.CYAN + 'An Amazon OSINT scraper for potential scam accounts')
print (Fore.YELLOW + 'By @jakecreps & @noneprivacy')
print (Fore.CYAN + 'Insert the URL for your search results')
url = input()
print ('How many pages do you want to scan?')
pages = input()
print ('What do you want to call the csv?')
csv = input()
