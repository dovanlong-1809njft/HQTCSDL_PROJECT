import React, { useEffect, useState } from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { createReminder, fetchGallery, setRsvp } from './api';

const RSVP_OPTIONS = ['Going', 'Maybe', 'Declined'];
const RSVP_LABEL = { Going: 'Tham dự', Maybe: 'Có thể', Declined: 'Bận' };

export default function EventDetail({ event, memberId, onBack }) {
  const [gallery, setGallery] = useState([]);
  const [myRsvp, setMyRsvp] = useState(null);
  const [goingCount, setGoingCount] = useState(event.going_count);
  const [reminderAt, setReminderAt] = useState('');
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchGallery(event.event_id).then(setGallery).catch((err) => setError(err.message));
  }, [event.event_id]);

  async function handleRsvp(status) {
    try {
      const result = await setRsvp(event.event_id, memberId, status);
      setMyRsvp(status);
      setGoingCount(result.going_count);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleReminder() {
    // Nhập dạng ISO, ví dụ 2026-11-20T18:30:00
    if (!reminderAt.trim()) return;
    try {
      await createReminder(event.event_id, reminderAt.trim());
      setReminderAt('');
      setMessage('Đã đặt nhắc nhở. Worker nền sẽ gửi khi tới giờ.');
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <ScrollView style={styles.screen}>
      <TouchableOpacity onPress={onBack}>
        <Text style={styles.back}>‹ Quay lại lịch</Text>
      </TouchableOpacity>

      <Text style={styles.title}>{event.title}</Text>
      <Text style={styles.meta}>
        {new Date(event.event_date).toLocaleString('vi-VN')}
        {event.location ? ` · ${event.location}` : ''}
      </Text>
      <Text style={styles.meta}>{goingCount} người tham dự</Text>

      <Text style={styles.section}>Bạn có tham dự không?</Text>
      <View style={styles.rsvpRow}>
        {RSVP_OPTIONS.map((status) => (
          <TouchableOpacity
            key={status}
            style={[styles.rsvpButton, myRsvp === status && styles.rsvpButtonActive]}
            onPress={() => handleRsvp(status)}
          >
            <Text style={[styles.rsvpText, myRsvp === status && styles.rsvpTextActive]}>
              {RSVP_LABEL[status]}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.section}>Thư viện ảnh</Text>
      {gallery.length === 0 ? (
        <Text style={styles.empty}>Chưa có ảnh nào.</Text>
      ) : (
        <View style={styles.galleryGrid}>
          {gallery.map((item) => (
            <Image key={item.id} source={{ uri: item.media_url }} style={styles.photo} />
          ))}
        </View>
      )}

      <Text style={styles.section}>Đặt nhắc nhở</Text>
      <View style={styles.reminderRow}>
        <TextInput
          style={styles.input}
          placeholder="2026-11-20T18:30:00"
          value={reminderAt}
          onChangeText={setReminderAt}
          autoCapitalize="none"
        />
        <TouchableOpacity style={styles.primaryButton} onPress={handleReminder}>
          <Text style={styles.primaryButtonText}>Đặt</Text>
        </TouchableOpacity>
      </View>

      {message && <Text style={styles.message}>{message}</Text>}
      {error && <Text style={styles.error}>{error}</Text>}
      <View style={styles.bottomSpace} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#fff', padding: 16 },
  back: { color: '#1565c0', fontSize: 15, marginBottom: 12 },
  title: { fontSize: 20, fontWeight: '700' },
  meta: { color: '#777', marginTop: 4 },
  section: { fontSize: 15, fontWeight: '600', marginTop: 22, marginBottom: 10 },
  rsvpRow: { flexDirection: 'row', gap: 10 },
  rsvpButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ccc',
  },
  rsvpButtonActive: { backgroundColor: '#1565c0', borderColor: '#1565c0' },
  rsvpText: { color: '#444' },
  rsvpTextActive: { color: '#fff', fontWeight: '600' },
  galleryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  photo: { width: 104, height: 104, borderRadius: 8, backgroundColor: '#eee' },
  reminderRow: { flexDirection: 'row', gap: 8 },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  primaryButton: {
    backgroundColor: '#1565c0',
    borderRadius: 8,
    paddingHorizontal: 18,
    justifyContent: 'center',
  },
  primaryButtonText: { color: '#fff', fontWeight: '600' },
  empty: { color: '#8a8a8a' },
  message: { color: '#2e7d32', marginTop: 12 },
  error: { color: '#c62828', marginTop: 12 },
  bottomSpace: { height: 40 },
});
