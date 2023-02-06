import re
import os
import json
import pathlib

import requests

from urllib.parse import quote
from bs4 import BeautifulSoup

lst = []
current_folder = os.path.dirname(pathlib.Path(__file__).resolve())


def url_for_parse(current_page):
    original = 'https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault?currentpage={}'
    site_with_page = original.format(current_page)

    request = requests.get(site_with_page)
    soup = BeautifulSoup(request.content, 'html.parser')
    items = soup.find('div', class_='ls-full-item')
    pk = items.get('id')

    a_tags = items.find_all('a', href=True)
    href = [item['href'] for item in a_tags if item['href'] != '#'][0]

    domain = request.cookies.list_domains()[1]
    www_url = quote(domain + href)
    https_url = www_url.replace('www.', 'https://')
    return {"url": https_url, "pk": pk}


def download_image(images, image_pk):
    target_folder = os.path.join(current_folder, 'data', image_pk)
    counter = 0
    for img in images:
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        image_name = image_pk + str(counter) + '.jpg'
        with open(os.path.join(target_folder, image_name), 'wb') as handler:
            handler.write(img)
            counter += 1


def save_content(data):
    target_folder = os.path.join(current_folder, 'data')
    if not os.path.exists(target_folder):
        os.makedirs(target_folder, exist_ok=True)
    with open(os.path.join(target_folder, 'data.json'), 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)


def scrap(site_data: dict, counter):
    global lst
    body = requests.get(site_data['url'])
    soup = BeautifulSoup(body.content, 'html.parser')
    item = soup.select_one('div', class_='detail-page')

    title = item.find('h1', class_='sc-ellipsis sc-font-xl').text
    dirty_price = item.find('h2', class_='sc-highlighter-4 sc-highlighter-xl sc-font-bold').text
    price = float(re.match(r'^(€)\s(\d+(.)\d+).+$', dirty_price).group(2))

    short_info = item.find_all('div', class_='itemval')
    data = {
        'pk': site_data['pk'],
        'href': site_data['url'],
        'title': title,
        'price': price,
    }
    for i in short_info:
        if re.match(r'^\d+\skm$', i.text):
            mileage = int(i.text[0:-3])
            data['mileage'] = mileage
        elif re.match(r'^\d+(.)\d+\skm$', i.text):
            data['mileage'] = float(i.text[0:-3])

    if 'mileage' not in data.keys():
        data['mileage'] = 0

    info = item.find_all('div', class_='sc-expandable-box')
    color_power_info = info[0]
    data_keys = color_power_info.find_all_next('div', class_='sc-font-bold')
    data_values = color_power_info.find_all_next('div', class_='')
    dict_info = dict(zip(data_keys, data_values))

    for i in list(dict_info.items()):
        if 'Farbe' in i[0].text:
            data['color'] = i[1].text

        if 'Leistung' in i[0].text:
            power = int(re.match(r'^(\d+\skW).+$', i[1].text).group(1)[0:-3])
            data['power'] = power

    description_info = info[2]
    description_title = description_info.findNext(
        'h3',
        class_='sc-font-l sc-font-bold sc-expandable-box__title'
    ).text
    description_content = description_info.findNext(
        'div',
        class_='short-description'
    ).text

    description = description_title + description_content
    data['description'] = description

    if 'color' not in data.keys():
        data['color'] = ''

    if 'power' not in data.keys():
        data['power'] = 0

    lst.append(data)
    if len(lst) == counter:
        save_content(lst)

    images = soup.find_all('div', class_='gallery-picture')
    result_images = []
    for i in images:
        result_images.append(requests.get(i.find('img').get('data-src')).content)

    download_image(result_images[:3], site_data['pk'])


def main():
    original = 'https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault'
    request = requests.get(original)
    soup = BeautifulSoup(request.content, 'html.parser')
    counter = len(soup.find_all('div', class_='sc-padding-bottom-m')) - 2
    for i in range(1, counter + 1):
        scrap(url_for_parse(i), counter)


if __name__ == '__main__':
    main()
