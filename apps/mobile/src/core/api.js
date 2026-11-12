// Lớp gọi API dùng chung cho app mobile (TV3).
// Khung ứng dụng mobile do TV2 khởi tạo; file này chỉ lo phần gọi API.

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL || 'http://10.0.2.2:8000/api';

let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

async function request(path, { method = 'GET', body, params } = {}) {
  const url = new URL(API_BASE_URL + path);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }

  const response = await fetch(url.toString(), {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let detail = `Lỗi ${response.status}`;
    try {
      const data = await response.json();
      if (data && data.detail) detail = data.detail;
    } catch {
      // giữ thông báo mặc định nếu server không trả JSON
    }
    throw new Error(detail);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  get: (path, params) => request(path, { params }),
  post: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
};
