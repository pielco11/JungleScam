import sys
import urllib3
import certifi
import re
import csv
import os
import random
import time
from json import loads

from urllib3.contrib.socks import SOCKSProxyManager
from bs4 import BeautifulSoup
from tqdm import tqdm
import asyncio
import aiohttp
import sqlite3

# setup colored output
from colorama import init
init(autoreset=True)
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
print(Fore.CYAN + 'An Amazon OSINT scraper for potential scam accounts')
print(Fore.YELLOW + 'By @jakecreps & @noneprivacy')
print(Fore.CYAN + 'Insert your keyword')
baseUrl = 'https://www.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=' + input()
print(Fore.CYAN + 'Which pages do you want to scan? (eg: 1-5)')
pages = input().split('-')
print(Fore.CYAN + 'Maximum Seller Feedback (%)')
threshold = input()
print(Fore.CYAN + 'What do you want to call the csv?')
filename = input() + ".csv"
print(Fore.CYAN + 'What do you want to call the database? (if it does not exist, a new one will be created)')
dbName = input() + ".db"
print(Fore.CYAN + 'Use Tor to round-robin requests? (Y/N)')
torSupport = input()
if torSupport.lower() == "y":
    torSupport = True
else:
    torSupport = False

_products_id = {}
_sellers_id = {}

roundRobin = 0

def initDB(db):
    dbConnector = sqlite3.connect(db)
    cursor = dbConnector.cursor()

    tableProducts = """
        CREATE TABLE IF NOT EXISTS
            products (
                id TEXT PRIMARY KEY NOT NULL
            );
        """
    cursor.execute(tableProducts)

    tableSellers = """
        CREATE TABLE IF NOT EXISTS
            sellers (
                id TEXT PRIMARY KEY NOT NULL,
                name TEXT NOT NULL,
                JL INTEGER,
                feedback INTERGER
            );
        """
    cursor.execute(tableSellers)

    tableDesc = """
        CREATE TABLE IF NOT EXISTS
            extras (
                id TEXT NOT NULL,
                contact INTEGER,
                gmail INTEGER,
                yahoo INTEGER,
                paypal INTEGER,
                FOREIGN KEY(id) REFERENCES sellers(id)
            );
        """
    cursor.execute(tableDesc)

    tableWhoSellsWhat = """
        CREATE TABLE IF NOT EXISTS
            wsw (
                product_id TEXT NOT NULL,
                seller_id TEXT NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(id),
                FOREIGN KEY(seller_id) REFERENCES sellers(id)
            );
        """
    cursor.execute(tableWhoSellsWhat)

    return dbConnector

dbConnector = initDB(dbName)

def insertProduct(productID):
    try:
        cursor = dbConnector.cursor()
        cursor.execute('INSERT INTO products VALUES(?)', (productID,))
        dbConnector.commit()
    except sqlite3.IntegrityError:
        pass

def insertSeller(productID, sellerInfo):
    try:
        cursor = dbConnector.cursor()
        cursor.execute('INSERT INTO sellers VALUES(?,?,?,?)', sellerInfo)
        cursor.execute('INSERT INTO wsw VALUES(?,?)', (productID, sellerInfo[0]))
        dbConnector.commit()
    except sqlite3.IntegrityError:
        pass

def insertExtra(sellerID, extras):
    _contact = ('contact' in extras)*1
    _gmail = ('gmail' in extras)*1
    _yahoo = ('yahoo' in extras)*1
    _paypal = ('paypal' in extras)*1
    _extras = (sellerID, _contact, _gmail, _yahoo, _paypal)
    try:
        cursor = dbConnector.cursor()
        cursor.execute('INSERT INTO extras VALUES(?,?,?,?,?)', _extras)
        dbConnector.commit()
    except sqlite3.IntegrityError:
        pass

def getInsertedSellers():
    cursor = dbConnector.cursor()
    cursor.execute('SELECT * FROM wsw')
    allRows = cursor.fetchall()
    with tqdm(total=len(allRows), desc='[<] Retrieving stored sellers') as cursorBar:
        for row in allRows:
            _sellers_id[row[0]][row[1]] = True
            cursorBar.update(1)
    cursorBar.close()

def randomUserAgent():
    _httpPool = urllib3.PoolManager( 10,
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where())
    url = "https://fake-useragent.herokuapp.com/browsers/0.1.8"
    r = _httpPool.request('GET', url).data.decode('utf-8')
    browsers = loads(r)['browsers']
    return random.choice(browsers[random.choice(list(browsers))])

http = urllib3.PoolManager( 10,
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where(),
    headers={'user-agent': randomUserAgent()})

proxy = SOCKSProxyManager('socks5://localhost:9050',
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where(),
    headers={'user-agent': randomUserAgent()})

def pageRequest(url):
    global roundRobin
    if roundRobin % 2:
        response = http.request('GET', url)
    else:
        if torSupport:
            response = proxy.request('GET', url)
        else:
            response = http.request('GET', url)
    roundRobin += 1
    return response.data

async def asyncRequest(url, randomUserAgent):
    timeout = aiohttp.ClientTimeout(total=60*3)
    ua = {'user-agent': randomUserAgent}
    async with aiohttp.ClientSession(headers=ua) as session:
        try:
            async with await session.get(url, timeout=timeout) as response:
                return await response.read()
        except aiohttp.client_exceptions.ClientConnectorError:
            print(Fore.RED + "\n[x] Error while fetching data from Amazon!")

def productIdsExtractor(soup):
    global _products_id
    for link in soup.find_all('a', href=re.compile('/dp/[\w]{2,20}/ref=sr_1_[\d]{1,3}')):
        l = link.get('href')
        _l = l.split('/')
        try:
            a = _products_id[_l[5]]
        except KeyError:
            _products_id.update({_l[5]: l})
    return _products_id

def sellerListExtractor(sellerListLink, sbar):
    divs = []
    i = 0
    while True:
        _htmlContent = pageRequest(sellerListLink)
        _soup = BeautifulSoup(_htmlContent, 'lxml')
        _t = _soup.find('title').text
        if _t == 'Sorry! Something went wrong!':
            sbar.write('[x] {}'.format(_t))
            return divs
        _divs = _soup.find_all('div', attrs = {'class': 'a-row a-spacing-mini olpOffer'})
        for _d in _divs:
            divs.append(_d)
        sellerListLink = _soup.find('li', attrs = {'class': 'a-last'})
        if not sellerListLink:
            break
        sellerListLink = site + sellerListLink.find('a')['href']
        i += 1
    return divs


def sellerIdExtractor(link, sbar):
    try:
        _seller_id = link.split("seller=")[1]
        return _seller_id
    except:
        sbar.write('[x] got a redirection to another website')
        return False

def sellerFeedbackExtractor(soup):
    _out_of = soup.find_all('span', attrs = {'class': 'a-color-success'})
    if _out_of:
        try:
            _feedback = list(_out_of)[len(_out_of) - 1].text
            return _feedback
        except:
            print(Fore.RED + "\n[x] Error while getting feedback from seller" +
                 ", please check manually the next result")
    return '-1'

def sellerDescExtractor(soup):
    about = soup.find('span', id='about-seller-text')
    if about:
        _text = about.text
        _whatToFind = ['contact', 'gmail', 'yahoo', 'paypal']
        _about = ""
        for w in _whatToFind:
            if w in _text:
                _about += w + ','
        _about[:len(_about)-1]
        return _about
    return ''

def sellerJustLaunched(soup):
    JL_bool = soup.find('span', id='feedback-no-rating')
    if JL_bool:
        return 'True'
    return ''

def extractSellerInfo(link, itemID, sbar):
    sellerID = sellerIdExtractor(link, sbar)
    if sellerID:
        try:
            _sID = _sellers_id[sellerID][itemID]
            return {}
        except KeyError:
            _sellers_id[sellerID] = {itemID: True}
            url = site + link
            _htmlContent = pageRequest(url)
            _soup = BeautifulSoup(_htmlContent, 'lxml')
            JL_bool = sellerJustLaunched(_soup)
            sellerFull = {
                'id': sellerID,
                'feedback': '',
                'desc': '',
                'just-launched': JL_bool
            }
            if not JL_bool:
                sellerFull['feedback'] = sellerFeedbackExtractor(_soup)
                if int(sellerFull['feedback']) > int(threshold):
                    return {}
            sellerFull['desc'] = sellerDescExtractor(_soup)
            return sellerFull
    return {}

async def fetchSellersFull(itemID, writer, sbar):
    insertProduct(itemID)
    checkUrl = f"https://www.amazon.com/gp/offer-listing/{itemID}/ref=dp_olp_new_center?ie=UTF8"
    divs = sellerListExtractor(checkUrl, sbar)
    for div in divs:
        _name = div.find('h3', attrs = {'class': 'olpSellerName'})
        name = _name.text.strip()
        if name:
            sellerLink = _name.find('a')['href']
            sellerFull = extractSellerInfo(sellerLink, itemID, sbar)
            if sellerFull:
                if not sellerFull['feedback'] == '-1':
                    sbar.write("<-> " + name + "\n |-> id: " + sellerFull['id']
                        + "\n |-> just-launched: " + sellerFull['just-launched']
                        + "\n |-> feedback: " + sellerFull['feedback']
                        + "\n --- desc: " + sellerFull['desc'])
                    writer.writerow({
                        'id': sellerFull['id'],
                        'name': str(name),
                        'link': site + sellerLink,
                        'just-launched': sellerFull['just-launched'],
                        'feedback': sellerFull['feedback'],
                        'desc': sellerFull['desc']
                        })
                    _t_JL = 0
                    if sellerFull['just-launched']:
                        _t_JL = 1
                    try:
                        _t_feedback = int(sellerFull['feedback'])
                    except ValueError:
                        _t_feedback = -2
                    _sellerFull = (sellerFull['id'], str(name), _t_JL, _t_feedback)
                    insertSeller(itemID, _sellerFull)
                    insertExtra(sellerFull['id'], sellerFull['desc'])
        sbar.update(1)

site = "https://" + baseUrl.split('/')[2]

mode = "w"
tasks = []
loop = asyncio.get_event_loop()

fPage = int(pages[0])
lPage = int(pages[1])

if os.path.exists(filename):
    mode = "a"
with open(filename, mode=mode) as csv_file:
    fieldnames = ['id', 'name', 'link', 'just-launched', 'feedback', 'desc']
    global writer
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    if mode == "w":
        writer.writeheader()
    _tqdm_desc = "[<] Extracting ids from pages"
    with tqdm(total=lPage, desc=_tqdm_desc) as pbar:
        getInsertedSellers()
        loop = asyncio.get_event_loop()
        for i in range(lPage):
            htmlContent = pageRequest(baseUrl)
            soup = BeautifulSoup(htmlContent, 'lxml')
            if soup.find('title').text == 'Robot Check':
                pbar.write('[x] Captcha found, wait a while before retrying or change the IP!')
            else:
                nextPage = soup.find('a', attrs = {'class': 'pagnNext'})['href']
                baseUrl = site + nextPage
                if i >= fPage:
                    IDs = productIdsExtractor(soup)
                    if not len(IDs):
                        pbar.write("[x] Amazon is blocking your requests, please change IP")
                        exit()
                    for key in IDs:
                        task = asyncio.ensure_future(fetchSellersFull(key, writer, pbar))
                        tasks.append(task)
                pbar.update(1)
        pbar.clear()
        pbar.set_description("[<] Extracting sellers info")
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
        dbConnector.close()
