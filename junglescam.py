import sys
import urllib3
import certifi
import re
import csv
import os

from bs4 import BeautifulSoup
from tqdm import tqdm

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


site = "https://" + baseUrl.split('//')[1].split('/')[0]
http = urllib3.PoolManager( 10,
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where(),
    headers={'user-agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:63.0) Gecko/20100101 Firefox/63.0'})

def extractSellerInfo(link):
    url = site + link
    _htmlContent = simpleRequest(url)
    _soup = BeautifulSoup(_htmlContent, 'lxml')
    JL_bool = _soup.find('span', id='feedback-no-rating')
    if not JL_bool:
        JL_bool = ""
    return JL_bool


def simpleRequest(url):
    response = http.request('GET', url)
    return response.data

def fetchSellersList(itemID, writer):
    global _ndivs
    checkUrl = f"https://www.amazon.com/gp/offer-listing/{itemID}/ref=dp_olp_new_center?ie=UTF8"
    _htmlContent = simpleRequest(checkUrl)
    _soup = BeautifulSoup(_htmlContent, 'lxml')
    divs = _soup.find_all('div', attrs = {'class': 'a-row a-spacing-mini olpOffer'})
    try:
        title = _soup.find('title').text.strip().strip("Amazon.com: Buying Choices: ")
    except AttributeError:
        title = str(_soup.find('title'))
    __ndivs = _ndivs
    _ndivs += len(divs)
    with tqdm(total=_ndivs, initial=_ndivs - len(divs), desc="Iteraing over sellers") as sbar:
        for div in divs:
            _name = div.find('h3', attrs = {'class': 'olpSellerName'})
            name = _name.text.strip()
            #price = div.find('span', attrs = {'class': 'olpOfferPrice'}).text.strip()
            #condition = str(div.find('span', attrs = {'class': 'olpCondition'}).text.strip()).replace("\n", "")
            if name:
                sellerLink = _name.find('a')['href']
                justLaunched = extractSellerInfo(sellerLink)
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

def idsExtractor(soup, pbar):
    _fast_check = {}
    pbar.write("[<<<] Extracting IDs")
    for link in soup.find_all('a', href=re.compile('www.amazon.com/[\w-]{1,100}/dp/[\w]{2,20}/ref=sr_1_[\d]{1,3}')):
        l = link.get('href')
        _l = l.split('/')
        try:
            a = _fast_check[_l[5]]
        except KeyError:
            _fast_check.update({_l[5]: l})
    pbar.write("[>>>] IDs extracted = {}".format(len(_fast_check)))
    return _fast_check

it = 1
pos = 0
mode = "w"

if os.path.exists(filename):
    mode = "a"
with open(filename, mode=mode) as csv_file:
    fieldnames = ['seller_name', 'seller_link']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    if mode == "w":
        writer.writeheader()
    with tqdm(total=int(pages), desc="Iteraing over pages") as pbar:
        for i in range(int(pages)):
            htmlContent = simpleRequest(baseUrl)
            soup = BeautifulSoup(htmlContent, 'lxml')
            IDs = idsExtractor(soup, pbar)
            for key in IDs:
                fetchSellersList(key, writer)
                pageLink = soup.find_all('span', attrs = {'class': 'pagnLink'})
                if it > 1:
                    pos = 1
                ll = list(pageLink)[pos].find('a')['href']
                baseUrl = site + ll
                it += 1
            pbar.update(1)
        pbar.close()
