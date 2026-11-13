import re

from services.product_comparison import normalize


# Catalogs without a taxonomy are classified by product type. Specific types
# come before ingredient names, so pepper pickles are not fresh vegetables.
FRESH = 'meyve ve sebze'
MEAT = 'et tavuk ve balik'
DAIRY = 'sut urunleri ve kahvaltilik'
PANTRY = 'temel gida'
DRINKS = 'icecek'
SNACKS = 'atistirmalik ve tatli'
CARE = 'temizlik ve kisisel bakim urunleri'

RULES = [
    (CARE, 'sac bakim', r'sampuan'),
    (CARE, 'dus banyo ve sabun', r'sabun'),
    (CARE, 'parfum deodorant kolonya ve kokular', r'deodorant|kolonya(?:si)?|parfum(?:u)?'),
    (CARE, 'camasir temizlik urunleri', r'(?:toz|camasir) deterjan'),
    (CARE, 'islak mendil', r'islak (?:mendil|havlu)'),
    (CARE, 'kagit havlu', r'kagit havlu'),
    (CARE, 'kagit pecete ve mendil', r'pecete|mendil'),
    (CARE, '', r'deterjan'),
    (PANTRY, 'tursu', r'tursu(?:su|lari)?'),
    (PANTRY, 'salca', r'salca(?:si|lari)?'),
    (SNACKS, 'cips', r'cips(?:i|leri)?'),
    (SNACKS, 'gofret', r'gofret'),
    (SNACKS, 'biskuvi ve kraker', r'biskuvi|kraker'),
    (SNACKS, 'kek', r'kek'),
    (SNACKS, 'sakiz ve sekerleme', r'sakiz|lolipop|sekerleme|yumusak seker'),
    (SNACKS, 'kuruyemis ve kuru meyve', r'kuruyemis|kuru meyve'),
    (SNACKS, 'dondurmalar', r'dondurma'),
    (SNACKS, 'cikolata', r'cikolata'),
    (DRINKS, 'meyve suyu', r'(?:meyve|elma|portakal|visne|seftali) suyu'),
    (DRINKS, 'maden suyu', r'maden suyu'),
    (DRINKS, 'gazli icecekler', r'gazoz|kola'),
    (DRINKS, 'gazsiz icecekler', r'limonata'),
    (DRINKS, 'ayran ve kefir', r'ayran|kefir'),
    (PANTRY, 'pasta malzemeleri', r'surup|surubu'),
    (DRINKS, 'kahve', r'kahve(?:si)?'),
    (DRINKS, 'cay ve bitki caylari', r'cay(?:i)?'),
    (DRINKS, 'su', r'(?:dogal |kaynak |icme )?su'),
    (MEAT, 'deniz urunleri', r'ton baligi|somon'),
    (MEAT, 'sarkuteri', r'sucuk|salam|sosis'),
    (MEAT, 'beyaz et', r'tavuk|hindi'),
    (MEAT, 'kirmizi et', r'dana|kuzu|kofte|kiyma'),
    (DAIRY, 'bal ve recel', r'bal|recel(?:i)?'),
    (DAIRY, 'tereyagi ve margarin', r'tereyagi|margarin'),
    (DAIRY, 'peynir', r'peynir(?:i)?'),
    (DAIRY, 'yogurt', r'yogurt'),
    (DAIRY, 'yumurta', r'yumurta'),
    (DAIRY, 'zeytin', r'zeytin'),
    (DAIRY, 'kaymak ve krema', r'kaymak|krema'),
    (DAIRY, 'helva tahin ve pekmez', r'helva|tahin|pekmez'),
    (DAIRY, 'sut', r'sut'),
    (PANTRY, 'bakliyat', r'nohut|mercimek|fasuly?e|bulgur|pirinc'),
    (PANTRY, 'manti makarna ve eriste', r'manti|makarna|eriste'),
    (PANTRY, 'sivi yaglar', r'aycicek yag(?:i)?|zeytinyag(?:i)?'),
    (PANTRY, 'un ve irmik', r'un|irmik'),
    (PANTRY, 'seker ve tatlandiricilar', r'seker'),
    (PANTRY, 'tuz baharat ve harclar', r'tuz'),
    (FRESH, 'meyve', r'elma|armut|muz|portakal|mandalina|limon'),
    (FRESH, 'sebze', r'domates|salatalik|patates|sogan|biber|havuc'),
]
RULES = [(parent, child, re.compile(r'\b(?:' + pattern + r')\b')) for parent, child, pattern in RULES]


def matches_category(product, category):
    label = normalize(category)
    if not label:
        return False
    supplied = tuple(normalize(product.get(field)) for field in ('category_name', 'subcategory_name'))
    if any(supplied):
        return label in supplied

    name = normalize(product.get('product_name'))
    brand = normalize(product.get('brand'))
    if brand and name.startswith(brand + ' '):
        name = name[len(brand) + 1:]
    for parent, child, pattern in RULES:
        if pattern.search(name):
            return label in (parent, child)
    return False
