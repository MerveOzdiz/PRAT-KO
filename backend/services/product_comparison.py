import re
import unicodedata
from collections import defaultdict
from decimal import Decimal


def normalize(value):
    text = unicodedata.normalize('NFKD', str(value or '').casefold().replace('ı', 'i'))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return ' '.join(re.findall(r'[a-z0-9]+', text))


def gtin(value):
    code = str(value or '')
    if len(code) not in (8, 12, 13, 14) or not re.fullmatch(r'[0-9]+', code):
        return None
    checksum = sum(int(digit) * (3 if index % 2 == 0 else 1)
                   for index, digit in enumerate(reversed(code[:-1])))
    return code.zfill(14) if (checksum + int(code[-1])) % 10 == 0 else None


def name_identity(product):
    name = str(product['product_name'])
    pack = re.search(r'(?<!\w)(\d+(?:[.,]\d+)?)\s*(kg|gr|g|ml|lt|l|adet)\s*$', name, re.I)
    if not pack:
        return None
    amount = Decimal(pack[1].replace(',', '.'))
    unit = pack[2].lower()
    if unit in ('kg', 'l', 'lt'):
        amount *= 1000
    unit = {'kg': 'g', 'gr': 'g', 'l': 'ml', 'lt': 'ml'}.get(unit, unit)
    return normalize(name[:pack.start()]), amount, unit


def mark_cheapest(products):
    groups = defaultdict(list)
    for product in products:
        product['is_cheapest'] = False
        scope = product['price_scope']
        if (product['price_status'] != 'AVAILABLE' or product['is_mock']
                or not product['price'] or product['stock_status'] == 'OUT_OF_STOCK'
                or scope not in ('ONLINE', 'BRANCH')):
            continue
        if product['source'] == 'MARKET_OWNER':
            groups[(scope, product['currency'], ('owner_catalog', product['source_product_id']))].append(product)
            continue
        barcode = gtin(product['barcode'])
        named = name_identity(product)
        source_id = product['source_product_id']
        identity = ('gtin', barcode) if barcode else ('name', named) if named else None
        if identity is None and source_id:
            identity = ('sku', product['market_code'], source_id)
        if identity:
            groups[(scope, product['currency'], identity)].append(product)

    for offers in groups.values():
        sellers = {(offer['market_code'], offer['branch_id']) for offer in offers}
        if len(sellers) < 2:
            continue
        cheapest = min(offer['price'] for offer in offers)
        for offer in offers:
            offer['is_cheapest'] = offer['price'] == cheapest
