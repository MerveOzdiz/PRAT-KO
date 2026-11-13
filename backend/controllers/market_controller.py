from flask import Blueprint, jsonify, request, current_app
from services.market_service import MarketService
from services.google_maps_service import GoogleMapsService, PlacesUnavailable

market_bp = Blueprint('market_bp', __name__)


def coordinates():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None


@market_bp.route('/api/nearby-markets', methods=['GET'])
def get_nearby_markets():
    coords = coordinates()
    if coords is None:
        return jsonify(error='Geçerli konum gerekli.'), 400
    try:
        return jsonify(MarketService.get_sorted_nearby_markets(
            *coords, current_app.config.get('GOOGLE_MAPS_API_KEY')
        ))
    except PlacesUnavailable:
        return jsonify(error='Market keşfi hizmetine ulaşılamadı.', code='PLACES_UNAVAILABLE'), 503


@market_bp.route('/api/reverse-geocode', methods=['GET'])
def reverse_geocode():
    coords = coordinates()
    if coords is None:
        return jsonify(error='Geçerli konum gerekli.'), 400
    return jsonify(address=GoogleMapsService.reverse_geocode(
        *coords, current_app.config.get('GOOGLE_MAPS_API_KEY')
    ))
