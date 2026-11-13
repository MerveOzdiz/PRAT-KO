import axios from 'axios';

const loopbackHost = window.location.hostname === '127.0.0.1' ? '127.0.0.1' : 'localhost';
const API_BASE_URL = import.meta.env.REACT_APP_API_URL || (import.meta.env.DEV ? '' : `http://${loopbackHost}:5000`);

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const getReverseGeocode = async (latitude, longitude) => {
  const response = await apiClient.get('/api/reverse-geocode', {
    params: { lat: latitude, lon: longitude }
  });
  return response.data;
};

export const getNearbyMarkets = async (latitude, longitude) => {
  const response = await apiClient.get('/api/nearby-markets', {
    params: { lat: latitude, lon: longitude }
  });
  return response.data;
};

export const getCategories = async () => {
  const response = await apiClient.get('/api/categories');
  return response.data;
};

export const searchProducts = async (query, categoryId) => {
  const response = await apiClient.get('/api/product-search', {
    params: { query, category_id: categoryId }
  });
  return response.data;
};

export const searchUnifiedMarkets = async (query, latitude, longitude, radius, page, category, signal, sortBy) => {
  const response = await apiClient.get('/api/v1/market-search', {
    params: { query, lat: latitude, lon: longitude, radius_km: radius, page, category, sort_by: sortBy }, signal, timeout: 30000
  });
  return response.data;
};

export function marketRequestError(failure, fallback) {
  if (failure.response?.data?.code === 'PLACES_UNAVAILABLE') {
    return 'Google Places şu anda market bilgisi sağlayamıyor. Daha sonra tekrar deneyin.';
  }
  if (!failure.response || failure.response.status >= 500) {
    return 'Pratiko sunucusuna ulaşılamadı veya sunucu yanıt veremedi. Tekrar deneyin.';
  }
  return fallback;
}

export default apiClient;
