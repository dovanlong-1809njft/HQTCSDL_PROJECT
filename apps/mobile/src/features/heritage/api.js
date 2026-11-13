import { API_BASE_URL } from '../../core/api';

// Host injects the current token; never persist another copy of authentication.
// TV3 core adapter exposes GET/POST/PUT only, so TV4 keeps PATCH/DELETE local.
export function createHeritageApi({ getAccessToken, baseUrl = API_BASE_URL }) {
  async function request(resource, { method = 'GET', familyId, id, body, params = {} } = {}) {
    const url = new URL(`${baseUrl}/heritage/${resource}${id ? `/${id}` : ''}`);
    Object.entries({ family_id: familyId, ...params }).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value));
    });
    const token = await getAccessToken();
    const response = await fetch(url.toString(), { method,
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: body ? JSON.stringify(body) : undefined });
    if (response.status === 204) return null;
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(typeof data.detail === 'string' ? data.detail : 'Dữ liệu chưa hợp lệ.');
      error.status = response.status;
      throw error;
    }
    return data;
  }
  return {
    families: () => request('families'),
    list: (resource, familyId, params) => request(resource, { familyId, params }),
    get: (resource, familyId, id) => request(resource, { familyId, id }),
    create: (resource, familyId, body) => request(resource, { method: 'POST', familyId, body }),
    update: (resource, familyId, id, body) => request(resource, { method: 'PATCH', familyId, id, body }),
    remove: (resource, familyId, row) => request(resource, { method: 'DELETE', familyId, id: row.id, params: { expected_version: row.version_token } }),
  };
}
