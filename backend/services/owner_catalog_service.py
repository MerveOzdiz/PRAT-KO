import re
import unicodedata
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text


FIELDS = ('name', 'brand', 'quantity', 'unit', 'category_id', 'price', 'currency', 'price_scope', 'valid_until')
UNITS = {'g': ('g', 1), 'kg': ('g', 1000), 'ml': ('ml', 1), 'l': ('ml', 1000), 'adet': ('adet', 1)}
TURKEY_TIME = timezone(timedelta(hours=3))


def decimal_value(value, label, decimals, digits):
    if type(value) not in (str, int, float):
        raise ValueError(f'{label} geçerli bir sayı olmalı.')
    raw = str(value).strip()
    if not re.fullmatch(rf'[0-9]{{1,{digits}}}(?:[.,][0-9]{{1,{decimals}}})?', raw):
        raise ValueError(f'{label} geçerli bir sayı olmalı ve en çok {decimals} ondalık basamak içermeli.')
    number = Decimal(raw.replace(',', '.'))
    if number <= 0:
        raise ValueError(f'{label} sıfırdan büyük olmalı.')
    return number


def product_text(value, label):
    if not isinstance(value, str) or len(value) > 100 or not value.strip():
        raise ValueError(f'{label} 1–100 karakter olmalı.')
    return ' '.join(unicodedata.normalize('NFKC', value).split())


def enum_value(value, values, label):
    if not isinstance(value, str) or value.strip().upper() not in values:
        raise ValueError(f'{label} geçersiz.')
    return value.strip().upper()


def expiry(value, today):
    if isinstance(value, datetime) and value.time() == time.min:
        value = value.date()
    if type(value) is date:
        result = value
    elif isinstance(value, str) and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value.strip()):
        try:
            result = date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError('Geçerlilik tarihi geçersiz.') from exc
    else:
        raise ValueError('Geçerlilik tarihini YYYY-AA-GG biçiminde girin.')
    if result < today:
        raise ValueError('Geçerlilik tarihi geçmiş olamaz.')
    return result.isoformat()


def validate_submission(data, categories, today):
    name = product_text(data.get('name'), 'Ürün adı')
    brand = product_text(data.get('brand'), 'Marka')
    quantity = decimal_value(data.get('quantity'), 'Miktar', 3, 8)
    raw_unit = data.get('unit')
    if not isinstance(raw_unit, str) or raw_unit.strip().lower() not in UNITS:
        raise ValueError('Birim g, kg, ml, l veya adet olmalı.')
    unit, multiplier = UNITS[raw_unit.strip().lower()]
    quantity = format((quantity * multiplier).normalize(), 'f')
    if unit == 'adet' and '.' in quantity:
        raise ValueError('Adet tam sayı olmalı.')
    category = data.get('category_id')
    if type(category) not in (str, int) or not re.fullmatch(r'[0-9]{1,10}', str(category).strip()):
        raise ValueError('Kategori kimliği geçersiz.')
    category = int(category)
    if category not in categories:
        raise ValueError('Kategori bulunamadı.')
    price = decimal_value(data.get('price'), 'Fiyat', 2, 9)
    return {
        'name': name, 'brand': brand, 'quantity': quantity, 'unit': unit, 'category_id': category,
        'price_minor': int(price * 100),
        'currency': enum_value(data.get('currency'), ('TRY', 'EUR', 'USD'), 'Para birimi'),
        'price_scope': enum_value(data.get('price_scope'), ('BRANCH', 'ONLINE', 'CAMPAIGN'), 'Fiyat türü'),
        'valid_until': expiry(data.get('valid_until'), today),
    }


def product_key(data):
    return (data['name'].casefold(), data['brand'].casefold(), data['quantity'], data['unit'])


def validate_rows(connection, rows):
    categories = set(connection.execute(text('SELECT id FROM category')).scalars())
    product_categories = {}
    today = datetime.now(TURKEY_TIME).date()
    valid, invalid, seen = [], [], set()
    for row_number, data, parse_error in rows:
        try:
            if parse_error:
                raise ValueError(parse_error)
            submission = validate_submission(data, categories, today)
            product = product_key(submission)
            if product not in product_categories:
                product_categories[product] = connection.exec_driver_sql("""
                    SELECT category_id FROM catalog_product
                    WHERE name_key = ? AND brand_key = ? AND quantity = ? AND unit = ?
                """, product).scalar_one_or_none()
            if product_categories[product] not in (None, submission['category_id']):
                raise ValueError('Bu ürün farklı bir kategoriyle kayıtlı.')
            offer = (*product, submission['price_scope'], submission['currency'], submission['valid_until'])
            if offer in seen:
                raise ValueError('Aynı ürün, fiyat türü, para birimi ve tarih dosyada tekrar ediyor.')
            seen.add(offer)
            product_categories[product] = submission['category_id']
            valid.append({'row': row_number, 'data': submission})
        except ValueError as exc:
            invalid.append({'row': row_number, 'error': str(exc)})
    return {'valid_rows': valid, 'invalid_rows': invalid}


def save_pending(connection, branch_id, user_id, validated, import_id=None):
    name_key, brand_key, _, _ = product_key(validated)
    product = {**validated, 'name_key': name_key, 'brand_key': brand_key}
    connection.execute(text("""
        INSERT INTO catalog_product (name, brand, quantity, unit, category_id, name_key, brand_key)
        VALUES (:name, :brand, :quantity, :unit, :category_id, :name_key, :brand_key)
        ON CONFLICT(name_key, brand_key, quantity, unit) DO NOTHING
    """), product)
    product_id = connection.execute(text("""
        SELECT id FROM catalog_product
        WHERE name_key = :name_key AND brand_key = :brand_key AND quantity = :quantity AND unit = :unit
    """), product).scalar_one()
    submission_id = connection.execute(text("""
        INSERT INTO price_submission
            (catalog_product_id, branch_id, submitted_by, import_batch_id,
             price_minor, currency, price_scope, valid_until)
        VALUES (:product_id, :branch_id, :user_id, :import_id,
                :price_minor, :currency, :price_scope, :valid_until)
    """), {**validated, 'product_id': product_id, 'branch_id': branch_id,
           'user_id': user_id, 'import_id': import_id}).lastrowid
    return {'id': submission_id, 'catalog_product_id': product_id, 'status': 'PENDING'}
