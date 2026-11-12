import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { fetchMonthlyEvents } from './api';
import EventDetail from './EventDetail';

const WEEKDAYS = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];

// Dựng lưới tháng: thêm ô trống đầu tháng cho khớp thứ trong tuần.
function buildMonthGrid(year, month) {
  const first = new Date(year, month - 1, 1);
  const daysInMonth = new Date(year, month, 0).getDate();
  const cells = Array.from({ length: first.getDay() }, () => null);
  for (let day = 1; day <= daysInMonth; day += 1) cells.push(day);
  return cells;
}

export default function CalendarScreen({ familyId, memberId }) {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);
  const [openEvent, setOpenEvent] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setEvents(await fetchMonthlyEvents(familyId, year, month));
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [familyId, year, month]);

  useEffect(() => {
    load();
  }, [load]);

  // Gom sự kiện theo ngày để chấm dấu trên lưới lịch.
  const eventsByDay = useMemo(() => {
    const map = {};
    events.forEach((event) => {
      const day = new Date(event.event_date).getDate();
      map[day] = map[day] ? [...map[day], event] : [event];
    });
    return map;
  }, [events]);

  function changeMonth(step) {
    const next = new Date(year, month - 1 + step, 1);
    setYear(next.getFullYear());
    setMonth(next.getMonth() + 1);
    setSelectedDay(null);
  }

  const dayEvents = selectedDay ? eventsByDay[selectedDay] || [] : events;

  if (openEvent) {
    return (
      <EventDetail
        event={openEvent}
        memberId={memberId}
        onBack={() => {
          setOpenEvent(null);
          load();
        }}
      />
    );
  }

  return (
    <View style={styles.screen}>
      <View style={styles.monthBar}>
        <TouchableOpacity onPress={() => changeMonth(-1)}>
          <Text style={styles.navButton}>‹</Text>
        </TouchableOpacity>
        <Text style={styles.monthLabel}>
          Tháng {month} / {year}
        </Text>
        <TouchableOpacity onPress={() => changeMonth(1)}>
          <Text style={styles.navButton}>›</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.weekRow}>
        {WEEKDAYS.map((label) => (
          <Text key={label} style={styles.weekday}>
            {label}
          </Text>
        ))}
      </View>

      <View style={styles.grid}>
        {buildMonthGrid(year, month).map((day, index) => (
          <TouchableOpacity
            key={`${day}-${index}`}
            style={[styles.cell, selectedDay === day && styles.cellSelected]}
            disabled={day === null}
            onPress={() => setSelectedDay(selectedDay === day ? null : day)}
          >
            <Text style={[styles.cellText, selectedDay === day && styles.cellTextSelected]}>
              {day || ''}
            </Text>
            {day && eventsByDay[day] && <View style={styles.dot} />}
          </TouchableOpacity>
        ))}
      </View>

      {error && <Text style={styles.error}>{error}</Text>}
      {loading && <ActivityIndicator style={styles.loading} />}

      <Text style={styles.listTitle}>
        {selectedDay ? `Sự kiện ngày ${selectedDay}/${month}` : 'Sự kiện trong tháng'}
      </Text>

      <FlatList
        data={dayEvents}
        keyExtractor={(item) => item.event_id}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.eventRow} onPress={() => setOpenEvent(item)}>
            <Text style={styles.eventTitle}>{item.title}</Text>
            <Text style={styles.eventMeta}>
              {new Date(item.event_date).toLocaleString('vi-VN', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
              })}
              {item.location ? ` · ${item.location}` : ''}
            </Text>
            <Text style={styles.eventMeta}>{item.going_count} người tham dự</Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={!loading && <Text style={styles.empty}>Không có sự kiện.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#f4f5f7' },
  monthBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 14,
    backgroundColor: '#fff',
  },
  navButton: { fontSize: 26, color: '#1565c0', paddingHorizontal: 10 },
  monthLabel: { fontSize: 17, fontWeight: '600' },
  weekRow: { flexDirection: 'row', backgroundColor: '#fff', paddingBottom: 6 },
  weekday: { flex: 1, textAlign: 'center', color: '#8a8a8a', fontSize: 12 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', backgroundColor: '#fff', paddingBottom: 10 },
  cell: { width: `${100 / 7}%`, height: 46, alignItems: 'center', justifyContent: 'center' },
  cellSelected: { backgroundColor: '#e3f2fd', borderRadius: 8 },
  cellText: { fontSize: 15 },
  cellTextSelected: { color: '#1565c0', fontWeight: '700' },
  dot: { width: 5, height: 5, borderRadius: 3, backgroundColor: '#1565c0', marginTop: 2 },
  listTitle: { fontSize: 15, fontWeight: '600', paddingHorizontal: 16, paddingVertical: 12 },
  eventRow: {
    backgroundColor: '#fff',
    marginHorizontal: 12,
    marginBottom: 10,
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#e6e6e6',
  },
  eventTitle: { fontSize: 15, fontWeight: '600' },
  eventMeta: { color: '#777', fontSize: 13, marginTop: 3 },
  empty: { textAlign: 'center', color: '#8a8a8a', marginTop: 16 },
  error: { color: '#c62828', paddingHorizontal: 16 },
  loading: { marginVertical: 10 },
});
