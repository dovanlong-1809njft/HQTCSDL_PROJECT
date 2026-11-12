import React, { useState } from 'react';
import { Image, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { setReaction } from './api';

const REACTIONS = ['Like', 'Love', 'Haha', 'Wow', 'Sad', 'Angry'];

function formatTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function PostCard({ post, onOpenComments }) {
  const [myReaction, setMyReaction] = useState(null);
  const [reactionCount, setReactionCount] = useState(post.reaction_count);
  const [picking, setPicking] = useState(false);
  const [error, setError] = useState(null);

  async function handleReaction(type) {
    const next = myReaction === type ? null : type; // bấm lại đúng loại cũ thì gỡ
    setPicking(false);
    try {
      const result = await setReaction(post.post_id, next);
      setMyReaction(next);
      setReactionCount(result.reaction_count);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.author}>{post.author_name || 'Ẩn danh'}</Text>
        <Text style={styles.time}>{formatTime(post.created_at)}</Text>
      </View>

      <Text style={styles.content}>{post.content}</Text>

      {post.media_urls.length > 0 && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.mediaRow}>
          {post.media_urls.map((url) => (
            <Image key={url} source={{ uri: url }} style={styles.media} />
          ))}
        </ScrollView>
      )}

      <View style={styles.actions}>
        <TouchableOpacity onPress={() => setPicking((value) => !value)}>
          <Text style={[styles.action, myReaction && styles.actionActive]}>
            {myReaction || 'Cảm xúc'} · {reactionCount}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => onOpenComments(post)}>
          <Text style={styles.action}>Bình luận · {post.comment_count}</Text>
        </TouchableOpacity>
      </View>

      {picking && (
        <View style={styles.reactionRow}>
          {REACTIONS.map((type) => (
            <TouchableOpacity key={type} onPress={() => handleReaction(type)}>
              <Text style={styles.reactionItem}>{type}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginHorizontal: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e6e6e6',
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  author: { fontWeight: '600', fontSize: 15 },
  time: { color: '#8a8a8a', fontSize: 12 },
  content: { marginTop: 8, fontSize: 15, lineHeight: 21 },
  mediaRow: { marginTop: 10 },
  media: { width: 180, height: 130, borderRadius: 8, marginRight: 8, backgroundColor: '#eee' },
  actions: { flexDirection: 'row', gap: 20, marginTop: 12 },
  action: { color: '#555', fontSize: 14 },
  actionActive: { color: '#1565c0', fontWeight: '600' },
  reactionRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 10 },
  reactionItem: { color: '#1565c0', fontSize: 14 },
  error: { color: '#c62828', marginTop: 8, fontSize: 13 },
});
