import sys
import urllib3
import certifi
import re
import csv
import os
import random
from json import loads

from bs4 import BeautifulSoup
from tqdm import tqdm
import asyncio
import aiohttp

# setup colored output
from colorama import init
init(autoreset=True)
from colorama import Fore, Back, Style

IDs = {}
_ndivs = 0

#baseUrl = sys.argv[1]
#pages = sys.argv[2]
#filename = sys.argv[3]

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
print (Fore.CYAN + 'What do you want to call the csv?')
filename = input()

parallel = pages
_fast_check = {}

def pageRequest(url):
    response = http.request('GET', url)
    return response.data

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

async def extractSellerInfo(link):
    url = site + link
    _htmlContent = pageRequest(url)
    _soup = BeautifulSoup(_htmlContent, 'lxml')
    JL_bool = _soup.find('span', id='feedback-no-rating')
    if not JL_bool:
        JL_bool = ""
    return JL_bool

async def asyncRequest(url, randomUserAgent):
    timeout = aiohttp.ClientTimeout(total=60*3)
    ua = {'user-agent': randomUserAgent}
    async with aiohttp.ClientSession(headers=ua) as session:
        async with await session.get(url, timeout=timeout) as response:
            return await response.read()

async def fetchSellersList(itemID, writer, myid, randomUserAgent, sbar):
    global _ndivs
    global _total_sellers
    global _checked_sellers
    checkUrl = f"https://www.amazon.com/gp/offer-listing/{itemID}/ref=dp_olp_new_center?ie=UTF8"
    _htmlContent = await asyncRequest(checkUrl, randomUserAgent)
    _soup = BeautifulSoup(_htmlContent, 'lxml')
    divs = _soup.find_all('div', attrs = {'class': 'a-row a-spacing-mini olpOffer'})
    try:
        title = _soup.find('title').text.strip().strip("Amazon.com: Buying Choices: ")
    except AttributeError:
        title = str(_soup.find('title'))
    _checked_sellers = _total_sellers
    _total_sellers += len(divs)
    for div in divs:
        _name = div.find('h3', attrs = {'class': 'olpSellerName'})
        name = _name.text.strip()
        #price = div.find('span', attrs = {'class': 'olpOfferPrice'}).text.strip()
        #condition = str(div.find('span', attrs = {'class': 'olpCondition'}).text.strip()).replace("\n", "")
        if name:
            sellerLink = _name.find('a')['href']
            justLaunched = await extractSellerInfo(sellerLink)
            if justLaunched:
                # next line prints title of the object to sell
                # sbar.write("[+] -- {}".format(title))
                # next line prints the seller name
                # sbar.write(str(name))
                # next line prints the link to the seller page
                # sbar.write(site + sellerLink)
                # next line prints " seller name :: just launched"
                sbar.write(" -- " + name + " :: " + justLaunched.text.strip())
                writer.writerow({
                    'seller_name': str(name),
                    'seller_link': site + sellerLink
                    })
        sbar.update(1)

def idsExtractor(soup, pbar, i):
    global _fast_check
    pbar.write("[<] Extracting IDs from page: {}".format(i+1))
    for link in soup.find_all('a', href=re.compile('www.amazon.com/[\w-]{1,100}/dp/[\w]{2,20}/ref=sr_1_[\d]{1,3}')):
        l = link.get('href')
        _l = l.split('/')
        try:
            a = _fast_check[_l[5]]
        except KeyError:
            _fast_check.update({_l[5]: l})
    return _fast_check

site = "https://" + baseUrl.split('//')[1].split('/')[0]

mode = "w"
tasks = []
loop = asyncio.get_event_loop()

if os.path.exists(filename):
    mode = "a"
with open(filename, mode=mode) as csv_file:
    fieldnames = ['seller_name', 'seller_link']
    global writer
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    if mode == "w":
        writer.writeheader()
    with tqdm(total=int(pages), initial=1, desc="Iteraing over pages") as pbar:
        global _total_sellers
        global _checked_sellers
        _total_sellers = 0
        _checked_sellers = 0
        with tqdm(total=_total_sellers, initial=_checked_sellers, desc="Iteraing over sellers") as sbar:
            global it
            global pos
            it = 1
            pos = 0
            loop = asyncio.get_event_loop()
            for i in range(int(pages)):
                randomUA = randomUserAgent()
                htmlContent = pageRequest(baseUrl)
                soup = BeautifulSoup(htmlContent, 'lxml')
                IDs = idsExtractor(soup, pbar, i)
                if not len(IDs):
                    pbar.write("[x] Amazon is blocking your requests, please change IP")
                    exit()
                for key in IDs:
                    task = asyncio.ensure_future(fetchSellersList(key, writer, i, randomUA, sbar))
                    tasks.append(task)
                pageLink = soup.find_all('span', attrs = {'class': 'pagnLink'})
                if it > 1:
                     pos = 1
                ll = list(pageLink)[pos].find('a')['href']
                baseUrl = site + ll
                it += 1
                pbar.update(1)
            pbar.close()
            loop.run_until_complete(asyncio.wait(tasks))
            loop.close()
