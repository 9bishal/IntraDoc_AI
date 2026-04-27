import api from './api';

export async function queryRag({ query, department, history = [] }) {
  const response = await api.post('/api/chat/', { query, department, history });
  return response.data;
}
