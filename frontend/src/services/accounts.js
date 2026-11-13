import apiClient from './api';

export async function accountRequest(path, method = 'GET', data) {
  const response = await apiClient.request({
    url: '/api/v1' + path,
    method,
    data,
    headers: data instanceof FormData
      ? { 'Content-Type': 'multipart/form-data', 'X-Pratiko-Import': '1' }
      : undefined,
    withCredentials: true,
  });
  return response.data;
}
