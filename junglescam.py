import sys
import urllib3
import certifi
import re
import csv
import os
import random
import time
from json import loads

from bs4 import BeautifulSoup
from tqdm import tqdm
import asyncio
import aiohttp

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
print (Fore.CYAN + 'An Amazon OSINT scraper for potential scam accounts')
print (Fore.YELLOW + 'By @jakecreps & @noneprivacy')
print (Fore.CYAN + 'Insert your URL')
baseUrl = input()
print (Fore.CYAN + 'How many pages do you want to scan?')
pages = input()
print (Fore.CYAN + 'Maximum Seller Feedback (%)')
threshold = input()
print (Fore.CYAN + 'What do you want to call the csv?')
filename = input() + ".csv"

_products_id = {}
_sellers_id = {}


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

def pageRequest(url):
    response = http.request('GET', url)
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
    for link in soup.find_all('a', href=re.compile('www.amazon.com/[\w-]{1,100}/dp/[\w]{2,20}/ref=sr_1_[\d]{1,3}')):
        l = link.get('href')
        _l = l.split('/')
        try:
            a = _products_id[_l[5]]
        except KeyError:
            _products_id.update({_l[5]: l})
    return _products_id

def sellerIdExtractor(link):
    _seller_id = link.split("seller=")[1]
    return _seller_id

def sellerFeedbackExtractor(soup):
    _out_of = soup.find_all('span', attrs = {'class': 'a-color-success'})
    if _out_of:
        try:
            _feedback = list(_out_of)[len(_out_of) - 1].text
        except:
            print(Fore.RED + "\n[x] Error while getting feedback from seller" +
                 ", please check manually the next result")
        return _feedback
    return str(0)

def sellerDescExtractor(soup):
    about = soup.find('span', id='about-seller-text')
    if about:
        _text = about.text
        _whatToFind = ['contact', 'gmail', 'yahoo', 'paypal']
        _about = ""
        for w in _whatToFind:
            if w in _text:
                _about += w + ","
        _about[:len(_about)-1]
        return _about
    return ""

def sellerJustLaunched(soup):
    JL_bool = soup.find('span', id='feedback-no-rating')
    if JL_bool:
        return "True"
    return ""

def sellerListingsFetcher(id):
    _url = 'https://www.amazon.com/s?me={}'.format(id)
    _htmlContent =  pageRequest(_url)
    _soup = BeautifulSoup(_htmlContent, 'lxml')
    resultsCount = _soup.find('span', attrs = {'id': 's-result-count'})
    if resultsCount:
        try:
            _results = re.search(' [\d]{1,7} ', resultsCount.text).group(0).strip()
        except AttributeError:
            print("\n[x] Amazon is blocking your requests, please change IP")
            _results = "not-found"
        return _results
    #f = open(id+'.html', "w")
    #f.write(str(_response))
    #f.close()
    print("\n[x] Amazon is blocking your requests, please change IP")
    return "not-found"

def extractSellerInfo(link):
    url = site + link
    _htmlContent = pageRequest(url)
    _soup = BeautifulSoup(_htmlContent, 'lxml')
    JL_bool = sellerJustLaunched(_soup)
    sellerID = sellerIdExtractor(link)
    sellerFull = {
        'id': sellerID,
        'feedback': '',
        'desc': '',
        'listings': '',
        'just-launched': JL_bool
    }
    try:
        _sID = _sellers_id[sellerID]
        return {}
    except KeyError:
        _sellers_id[sellerID] = True
        if not JL_bool:
            sellerFull['feedback'] = sellerFeedbackExtractor(_soup)
            if int(sellerFull['feedback']) > int(threshold):
                return {}
        sellerFull['desc'] = sellerDescExtractor(_soup)
        sellerFull['listings'] = sellerListingsFetcher(sellerID)
        return sellerFull

async def fetchSellersList(itemID, writer, myid, randomUserAgent, sbar):
    checkUrl = f"https://www.amazon.com/gp/offer-listing/{itemID}/ref=dp_olp_new_center?ie=UTF8"
    _htmlContent = pageRequest(checkUrl)
    _soup = BeautifulSoup(_htmlContent, 'lxml')
    divs = _soup.find_all('div', attrs = {'class': 'a-row a-spacing-mini olpOffer'})
    try:
        title = _soup.find('title').text.strip().strip("Amazon.com: Buying Choices: ")
    except AttributeError:
        title = str(_soup.find('title'))
    for div in divs:
        _name = div.find('h3', attrs = {'class': 'olpSellerName'})
        name = _name.text.strip()
        if name:
            sellerLink = _name.find('a')['href']
            sellerFull = extractSellerInfo(sellerLink)
            if sellerFull:
                sbar.write("<-> " + name + "\n |-> id: " + sellerFull['id']
                    + "\n |-> just-launched: " + sellerFull['just-launched']
                    + "\n |-> feedback: " + sellerFull['feedback']
                    + "\n |-> desc: " + sellerFull['desc']
                    + "\n --- listings: " + sellerFull['listings'])
                writer.writerow({
                    'id': sellerFull['id'],
                    'name': str(name),
                    'link': site + sellerLink,
                    'just-launched': sellerFull['just-launched'],
                    'feedback': sellerFull['feedback'],
                    'listings': sellerFull['listings'],
                    'desc': sellerFull['desc']
                    })
        sbar.update(1)

site = "https://" + baseUrl.split('/')[2]

mode = "w"
tasks = []
loop = asyncio.get_event_loop()

if os.path.exists(filename):
    mode = "a"
with open(filename, mode=mode) as csv_file:
    fieldnames = ['id', 'name', 'link', 'just-launched', 'feedback', 'listings', 'desc']
    global writer
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    if mode == "w":
        writer.writeheader()
    _tqdm_total = int(pages)
    _tqdm_init = 0
    _tqdm_desc = "[<] Extracting ids from pages"
    with tqdm(total=_tqdm_total, initial=_tqdm_init, desc=_tqdm_desc) as pbar:
        it = 1
        pos = 0
        loop = asyncio.get_event_loop()
        for i in range(int(pages)):
            randomUA = randomUserAgent()
            htmlContent = pageRequest(baseUrl)
            soup = BeautifulSoup(htmlContent, 'lxml')
            IDs = productIdsExtractor(soup)
            if not len(IDs):
                pbar.write("[x] Amazon is blocking your requests, please change IP")
                exit()
            for key in IDs:
                task = asyncio.ensure_future(fetchSellersList(key, writer, i, randomUA, pbar))
                tasks.append(task)
            pageLink = soup.find_all('span', attrs = {'class': 'pagnLink'})
            if it > 1:
                 pos = 1
            ll = list(pageLink)[pos].find('a')['href']
            baseUrl = site + ll
            it += 1
            pbar.update(1)
        pbar.clear()
        pbar.set_description("[<] Extracting sellers info")
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
