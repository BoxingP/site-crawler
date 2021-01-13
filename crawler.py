import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession

from info import Info


def crawler(url, sku):
    sku_info = {}
    response = requests.get(url + sku)

    if response.status_code != 200:
        print(url + sku + " is not available.")
        return

    session = HTMLSession()
    response_with_js = session.get(url + sku)
    response_with_js.html.render()

    soup = BeautifulSoup(response.text, 'html.parser')
    soup_with_js = BeautifulSoup(response_with_js.html.html, 'html.parser')

    sku_info['product-id'] = sku
    sku_info['product-name'] = soup.title.string

    if not soup.find_all('script', text=re.compile('window.preloadData')):
        return

    script_text = soup.find_all('script', text=re.compile('window.preloadData'))[0].string
    pre_load_data = script_text.split("window.errors =", 1)[0].replace('window.preloadData =', '')
    pre_load_data = re.sub('],\n +},\n +"data"', ']},"data"', pre_load_data)
    pre_load_data = json.loads(pre_load_data)

    product_data = [x for x in pre_load_data['commerceBoxData']['products'] if x['isPrimarySku'] is True][0]
    sku_info['product-meta-description'] = product_data['metaDescription'].replace(u'\xa0', ' ')

    if 'longDescription' in product_data and product_data['longDescription'] != "":
        sku_info['product-detail-description'] = product_data['longDescription'].replace(u'\xa0', ' ')
    else:
        if 'productFeatures' in product_data and product_data['productFeatures'] != "":
            sku_info['product-detail-description'] = product_data['productFeatures'].replace(u'\xa0', ' ')
        else:
            sku_info['product-detail-description'] = ""

    images = []
    if 'images' in product_data:
        for image in product_data['images']:
            if re.match(r'^.+(-650.jpg)$', image['path']):
                images.append({'url': image['path']})
            else:
                images.append({'url': image['path'] + '-650.jpg'})
    sku_info['images'] = images

    documents = []
    for span in soup_with_js.select('div#pdp-documents span.document-detail'):
        document = {'title': span.find('a').contents[0], 'url': span.find('a')['href']}
        documents.append(document)

    sku_info['product-document'] = documents

    with open('./results/' + sku + '.json', 'w', encoding='utf-8') as file:
        json.dump(sku_info, file, ensure_ascii=False, indent=4)


START = datetime.utcnow()
site_url = Info().load_config("./url.json")['url']
sku_ids = Info().load_config("./sku.json")['sku']
for sku_id in sku_ids:
    crawler(site_url, sku_id)
END = datetime.utcnow()
print('Total time is %s s.' % round((END - START).total_seconds()))
