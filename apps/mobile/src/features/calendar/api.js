// Gọi API phân hệ Sự kiện (domains/events).
import { api } from '../../core/api';

export const fetchMonthlyEvents = (familyId, year, month) =>
  api.get('/events', { family_id: familyId, year, month });

export const fetchEvent = (eventId) => api.get(`/events/${eventId}`);

export const createEvent = (familyId, title, eventDate, location) =>
  api.post('/events', {
    family_id: familyId,
    title,
    event_date: eventDate,
    location,
  });

export const setRsvp = (eventId, memberId, rsvpStatus) =>
  api.put(`/events/${eventId}/rsvp`, { member_id: memberId, rsvp_status: rsvpStatus });

export const fetchGallery = (eventId) => api.get(`/events/${eventId}/gallery`);

export const addGalleryItem = (eventId, mediaUrl) =>
  api.post(`/events/${eventId}/gallery`, { media_url: mediaUrl });

export const createReminder = (eventId, reminderTime) =>
  api.post(`/events/${eventId}/reminders`, { reminder_time: reminderTime });
