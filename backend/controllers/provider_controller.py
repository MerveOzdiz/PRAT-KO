from flask import Blueprint, jsonify, request, current_app
from services.market_provider_service import MarketProviderService
from services.market_service import MarketService
from services.published_price_service import published_owner_prices
from services.google_maps_service import PlacesUnavailable
from .market_controller import coordinates

provider_bp = Blueprint('provider_bp', __name__)

@provider_bp.route('/api/v1/market-search', methods=['GET'])
def unified_market_search():
    query = request.args.get('query', '').strip()
    category = request.args.get('category', '').strip() or None
    sort_by = request.args.get('sort_by', 'price')
    coords = coordinates()
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        radius = float(request.args.get('radius_km', 3))
    except ValueError:
        return jsonify(error='Geçersiz arama parametresi.'), 400
    if (coords is None or not (query or category) or len(query) > 120
            or len(category or '') > 120 or not 1 <= page <= 10000
            or sort_by not in ('price', 'distance') or not 1 <= page_size <= 100 or radius not in (0.5, 1, 1.5, 2, 3)):
        return jsonify(error='Geçersiz arama parametresi.'), 400

    owner_prices = published_owner_prices(query, category, coords, radius)
    try:
        nearby_branches = MarketService.get_sorted_nearby_markets(
            *coords, current_app.config.get('GOOGLE_MAPS_API_KEY')
        )
    except PlacesUnavailable:
        if not owner_prices:
            return jsonify(error='Market keşfi hizmetine ulaşılamadı.', code='PLACES_UNAVAILABLE'), 503
        nearby_branches = []
    nearby_branches = [branch for branch in nearby_branches if branch['distance_km'] <= radius]

    search_response = MarketProviderService.search_all_providers(
        search_term=query,
        nearby_branches=nearby_branches,
        category_filter=category,
        page=page,
        page_size=page_size,
        owner_prices=owner_prices,
        sort_by=sort_by,
    )

    return jsonify({
        "total_results": search_response['total'],
        "page": search_response['page'],
        "page_size": search_response['page_size'],
        "total_pages": search_response['total_pages'],
        "query": query,
        "category": category,
        "results": search_response['results']
    })

@provider_bp.route('/api/v1/categories', methods=['GET'])
def get_categories():
    categories = [
        {"id": "sut-urunleri", "name": "Süt & Süt Ürünleri", "icon": "🥛"},
        {"id": "temel-gida", "name": "Temel Gıda", "icon": "🌾"},
        {"id": "kahvaltilik", "name": "Kahvaltılık", "icon": "🧀"},
        {"id": "icecek", "name": "İçecek", "icon": "🥤"},
        {"id": "atistirmalik", "name": "Atıştırmalık", "icon": "🍫"},
        {"id": "meyve-sebze", "name": "Meyve & Sebze", "icon": "🍎"},
        {"id": "et-tavuk-balik", "name": "Et, Tavuk & Balık", "icon": "🥩"},
        {"id": "temizlik", "name": "Temizlik", "icon": "🧹"},
        {"id": "kisisel-bakim", "name": "Kişisel Bakım", "icon": "🧴"},
        {"id": "bebek", "name": "Bebek", "icon": "👶"},
        {"id": "dondurulmus", "name": "Dondurulmuş Gıda", "icon": "🧊"},
        {"id": "ev-yasam", "name": "Ev & Yaşam", "icon": "🏠"}
    ]
    return jsonify({"categories": categories})
