import sys
import urllib3
import certifi
import re

from bs4 import BeautifulSoup

IDs = {}
baseUrl = sys.argv[1]
pages = sys.argv[2]
site = "https://" + baseUrl.split('//')[1].split('/')[0]
http = urllib3.PoolManager( 10,
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where(),
    headers={'user-agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:63.0) Gecko/20100101 Firefox/63.0'})

def simpleRequest(url):
    response = http.request('GET', url)
    return response.data

def fetchSellersList(itemID):
    checkUrl = f"https://www.amazon.com/gp/offer-listing/{itemID}/ref=dp_olp_new_center?ie=UTF8"
    _htmlContent = simpleRequest(checkUrl)
    _soup = BeautifulSoup(_htmlContent, 'lxml')
    divs = _soup.find_all('div', attrs = {'class': 'a-row a-spacing-mini olpOffer'})
    try:
        title = _soup.find('title').text.strip().strip("Amazon.com: Buying Choices: ")
    except AttributeError:
        title = str(_soup.find('title'))
    print("[+] -- {}".format(title))
    for div in divs:
        name = div.find('h3', attrs = {'class': 'olpSellerName'}).text.strip()
        price = div.find('span', attrs = {'class': 'olpOfferPrice'}).text.strip()
        condition = str(div.find('span', attrs = {'class': 'olpCondition'}).text.strip()).replace("\n", "")
        if not name:
            name = "Amazon"
        print(" -- " + name + " :: " + price + " :: " + condition)

def idsExtractor(soup):
    _fast_check = {}
    print("[<<<] Extracting IDs")
    for link in soup.find_all('a', href=re.compile('www.amazon.com/[\w-]{1,100}/dp/[\w]{2,20}/ref=sr_1_[\d]{1,3}')):
        l = link.get('href')
        _l = l.split('/')
        try:
            a = _fast_check[_l[5]]
        except KeyError:
            _fast_check.update({_l[5]: l})
    print("[>>>] IDs extracted = {}".format(len(_fast_check)))
    return _fast_check

it = 1
pos = 0
for i in range(int(pages)):
    htmlContent = simpleRequest(baseUrl)
    soup = BeautifulSoup(htmlContent, 'lxml')
    IDs = idsExtractor(soup)
    for key in IDs:
        fetchSellersList(key)
    pageLink = soup.find_all('span', attrs = {'class': 'pagnLink'})
    if it > 1:
        pos = 1
    ll = list(pageLink)[pos].find('a')['href']
    baseUrl = site + ll
    print(baseUrl)
    it += 1
