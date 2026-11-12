// Gọi API phân hệ Cộng đồng (domains/community).
import { api } from '../../core/api';

export const fetchNewsfeed = (familyId, page = 1, pageSize = 20) =>
  api.get('/community/posts', { family_id: familyId, page, page_size: pageSize });

export const fetchComments = (postId) =>
  api.get(`/community/posts/${postId}/comments`);

export const createPost = (familyId, content, media = []) =>
  api.post('/community/posts', { family_id: familyId, content, media });

export const addComment = (postId, content) =>
  api.post(`/community/posts/${postId}/comments`, { content });

// type = null để gỡ cảm xúc
export const setReaction = (postId, type) =>
  api.put(`/community/posts/${postId}/reactions`, { type });

export const reportContent = (targetId, targetType, reason) =>
  api.post('/community/reports', {
    target_id: targetId,
    target_type: targetType,
    reason,
  });
