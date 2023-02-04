import asyncio

import aiohttp
import requests

from urllib.parse import quote
from bs4 import BeautifulSoup


def url_for_parse(current_page):
    original = 'https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault?currentpage={}'
    site_with_page = original.format(current_page)

    request = requests.get(site_with_page)
    soup = BeautifulSoup(request.content, 'html.parser')
    items = soup.find('div', class_='ls-full-item')
    # pk = items.get('id') todo for json

    a_tags = items.find_all('a', href=True)
    href = [item['href'] for item in a_tags if item['href'] != '#'][0]

    domain = request.cookies.list_domains()[1]
    www_url = quote(domain + href)
    https_url = www_url.replace('www.', 'https://')
    return https_url


async def scrap(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            body = await response.text()
            soup = BeautifulSoup(body, 'html.parser')
            item = soup.select_one('div', class_='detail-page')

            title = item.find('h1', class_='sc-ellipsis sc-font-xl').text
            price = item.find('h2', class_='sc-highlighter-4 sc-highlighter-xl sc-font-bold').text
            mileage = item.find_all('div', class_='itemval')[1].text

            info = item.find_all('div', class_='sc-expandable-box')[0]
            data_keys = info.find_all_next('div', class_='sc-font-bold')
            data_values = info.find_all_next('div', class_='')
            dict_info = dict(zip(data_keys, data_values))

            color_pairs = list(dict_info.items())[-10]
            power_pairs = list(dict_info.items())[-7]

            color = color_pairs[-1].text
            power = power_pairs[-1].text

asyncio.run(scrap(url_for_parse(1)))
