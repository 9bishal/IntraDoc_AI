import api from './api';

export async function uploadDocument({ file, department }) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('department', department);

  const response = await api.post('/api/documents/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function listDocuments() {
  const response = await api.get('/api/documents/');
  return response.data;
}
