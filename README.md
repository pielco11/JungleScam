![python](https://img.shields.io/badge/python-3.6-orange.svg) ![lxml](https://img.shields.io/badge/lxml-4.2.5-orange.svg) ![bs4](https://img.shields.io/badge/BeautifulSoup-4.6.3-orange.svg) ![aiohttp](https://img.shields.io/badge/aiohttp-3.4.4-orange.svg) ![pysocks](https://img.shields.io/badge/pysocks-1.6.8-orange.svg) ![tqdm](https://img.shields.io/badge/tqdm-4.23.4-orange.svg) ![certifi](https://img.shields.io/badge/certifi-2018.11.29-orange.svg)
# JungleScam

![img](https://i.imgur.com/M688WRn.png)

## External Dependencies

Tor is required to round-robin requests.

## How-to

Run `python3 junglescam.py` and follow the instructions.

## Round-Robin Setup

1. Be sure to have Tor installed;

2. Create the hash of your password;
![tor-hash](https://i.imgur.com/hNZDIg0.png)

3. Copy&Paste at the end of the `torrc` file, the location depends by your system;
![tor-setup](https://i.imgur.com/g66Oi7J.png)

4. Edit `junglescam.py` accordingly to your setup;
![junglescam-setup](https://i.imgur.com/LL2hI4L.png)

- `torControlPW` is the password that you hashed;
- `torPort` is the port where Tor is binding;
- `torControlPort` is the port that you use to connect to Tor and control it.

If you will use Tor Browser, change `torPort` to **9150** and `torControlPort` to **9151**. Note: in that case the location of the `torrc` file will be different.

5. Let `junglescam.py` run for a while, you will see a few `[+] new Tor identity`

2018 - All rights reserved - Francesco Poldi & Jake Creps
