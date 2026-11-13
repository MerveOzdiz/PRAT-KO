import React, { useEffect, useRef } from 'react';

function MapView({ userLocation, markets }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);

  useEffect(() => {
    if (!mapContainerRef.current || !window.L) return;

    const { lat, lon } = userLocation ?? {};
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      mapInstanceRef.current?.remove();
      mapInstanceRef.current = null;
      markersRef.current = [];
      return;
    }

    // Initialize Leaflet map instance once
    if (!mapInstanceRef.current) {
      const map = window.L.map(mapContainerRef.current).setView([lat, lon], 14);

      window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map);

      mapInstanceRef.current = map;
    } else {
      mapInstanceRef.current.setView([lat, lon], 14);
    }

    const map = mapInstanceRef.current;

    // Clear previous markers
    markersRef.current.forEach(marker => map.removeLayer(marker));
    markersRef.current = [];

    // 1. Add User Location Marker
    const userIcon = window.L.divIcon({
      className: 'custom-user-marker',
      html: '<div style="background-color: #28a745; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 8px rgba(0,0,0,0.4);"></div>',
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });

    const userMarker = window.L.marker([lat, lon], { icon: userIcon })
      .addTo(map)
      .bindPopup('<b>Sizin Konumunuz</b>');

    markersRef.current.push(userMarker);

    // 2. Add Market Markers
    markets.forEach((market) => {
      const { latitude: mLat, longitude: mLon } = market;
      if (!Number.isFinite(mLat) || !Number.isFinite(mLon)) return;

      const marketIcon = window.L.divIcon({
        className: 'custom-market-marker',
        html: '<div style="background-color: #2b6cb0; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.3); border: 1px solid white;">🛒</div>',
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });

      const distMeters = (market.distance_km * 1000).toFixed(0);
      const popupContent = `
        <div style="font-family: sans-serif; font-size: 13px;">
          <strong style="color: #28a745;">${market.name}</strong><br/>
          <span style="color: #666;">${market.address || ''}</span><br/>
          <strong style="color: #333;">Mesafe: ~${distMeters}m</strong>
        </div>
      `;

      const markerInst = window.L.marker([mLat, mLon], { icon: marketIcon })
        .addTo(map)
        .bindPopup(popupContent);

      markersRef.current.push(markerInst);
    });

  }, [userLocation, markets]);

  return (
    <div style={{ width: '100%', height: '350px', borderRadius: '12px', overflow: 'hidden', marginBottom: '1.5rem', border: '1px solid #e2e8f0' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
}

export default MapView;
