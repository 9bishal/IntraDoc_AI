import api from './api';

export async function queryRag({ query, department }) {
  const response = await api.post('/api/chat/', { query, department });
  return response.data;
}
