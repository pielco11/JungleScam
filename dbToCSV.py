###### Tech-Dev stuff here
# DB TABLES STRUCTURE ::
# sellers (
#     id TEXT PRIMARY KEY NOT NULL,
#     name TEXT NOT NULL,
#     JL INTEGER,
#     feedback INTERGER
# );
# extras (
#     id TEXT NOT NULL,
#     contact INTEGER,
#     gmail INTEGER,
#     yahoo INTEGER,
#     paypal INTEGER,
#     FOREIGN KEY(id) REFERENCES sellers(id)
# );
##############################################à

import sqlite3
import csv

from tqdm import tqdm

# setup colored output
from colorama import init
init(autoreset=True)
from colorama import Fore, Back, Style
print(Fore.CYAN + 'What do you want to call the csv?')
filename = input() + ".csv"

print (Fore.YELLOW + """
██████╗ ██████╗     ████████╗ ██████╗      ██████╗███████╗██╗   ██╗
██╔══██╗██╔══██╗    ╚══██╔══╝██╔═══██╗    ██╔════╝██╔════╝██║   ██║
██║  ██║██████╔╝       ██║   ██║   ██║    ██║     ███████╗██║   ██║
██║  ██║██╔══██╗       ██║   ██║   ██║    ██║     ╚════██║╚██╗ ██╔╝
██████╔╝██████╔╝       ██║   ╚██████╔╝    ╚██████╗███████║ ╚████╔╝
╚═════╝ ╚═════╝        ╚═╝    ╚═════╝      ╚═════╝╚══════╝  ╚═══╝
""")
print(Fore.CYAN + 'An export util for JungleScam')
print(Fore.YELLOW + 'By @jakecreps & @noneprivacy')
dbFile = input(Fore.CYAN + '[<] Database filename: ')
csvFile = input(Fore.CYAN + '[<] CSV filename: ')

def initDB(db):
    dbConnector = sqlite3.connect(db)
    cursor = dbConnector.cursor()

    return dbConnector

def getInsertedSellers(dbConnector):
    cursor = dbConnector.cursor()
    cursor.execute('SELECT * FROM sellers')
    allRows = cursor.fetchall()
    with tqdm(total=len(allRows), desc='[<] Retrieving stored sellers') as cursorBar:
        for row in allRows:

            cursorBar.update(1)
    cursorBar.close()

writer.writerow({
    'id': sellerFull['id'],
    'name': str(name),
    'link': site + sellerLink,
    'just-launched': sellerFull['just-launched'],
    'feedback': sellerFull['feedback'],
    'desc': sellerFull['desc']
    })

dbConn = initDB(dbFile)
site = 'https://www.amazon.com'
with open(csvFile, 'w') as csv_file:
    fieldnames = ['id', 'name', 'link', 'just-launched', 'feedback', 'desc']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    getInsertedSellers(dbConn)
