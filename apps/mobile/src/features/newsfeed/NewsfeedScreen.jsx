import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { addComment, createPost, fetchComments, fetchNewsfeed } from './api';
import PostCard from './PostCard';

export default function NewsfeedScreen({ familyId }) {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [draft, setDraft] = useState('');
  const [openPost, setOpenPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentDraft, setCommentDraft] = useState('');

  const load = useCallback(async () => {
    try {
      const data = await fetchNewsfeed(familyId);
      setPosts(data.items);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [familyId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handlePost() {
    const content = draft.trim();
    if (!content) return;
    try {
      const created = await createPost(familyId, content);
      setPosts((current) => [created, ...current]);
      setDraft('');
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }

  async function openComments(post) {
    setOpenPost(post);
    setComments([]);
    try {
      setComments(await fetchComments(post.post_id));
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleComment() {
    const content = commentDraft.trim();
    if (!content || !openPost) return;
    try {
      const created = await addComment(openPost.post_id, content);
      setComments((current) => [...current, created]);
      setCommentDraft('');
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <View style={styles.composer}>
        <TextInput
          style={styles.input}
          placeholder="Chia sẻ với gia đình..."
          value={draft}
          onChangeText={setDraft}
          multiline
        />
        <TouchableOpacity style={styles.postButton} onPress={handlePost}>
          <Text style={styles.postButtonText}>Đăng</Text>
        </TouchableOpacity>
      </View>

      {error && <Text style={styles.error}>{error}</Text>}

      <FlatList
        data={posts}
        keyExtractor={(item) => item.post_id}
        renderItem={({ item }) => <PostCard post={item} onOpenComments={openComments} />}
        refreshing={refreshing}
        onRefresh={() => {
          setRefreshing(true);
          load();
        }}
        ListEmptyComponent={<Text style={styles.empty}>Chưa có bài viết nào.</Text>}
        contentContainerStyle={styles.list}
      />

      <Modal visible={openPost !== null} animationType="slide" onRequestClose={() => setOpenPost(null)}>
        <View style={styles.modal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Bình luận</Text>
            <TouchableOpacity onPress={() => setOpenPost(null)}>
              <Text style={styles.close}>Đóng</Text>
            </TouchableOpacity>
          </View>

          <FlatList
            data={comments}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <View style={styles.comment}>
                <Text style={styles.commentAuthor}>{item.author_name || 'Ẩn danh'}</Text>
                <Text>{item.content}</Text>
              </View>
            )}
            ListEmptyComponent={<Text style={styles.empty}>Chưa có bình luận.</Text>}
          />

          <View style={styles.composer}>
            <TextInput
              style={styles.input}
              placeholder="Viết bình luận..."
              value={commentDraft}
              onChangeText={setCommentDraft}
            />
            <TouchableOpacity style={styles.postButton} onPress={handleComment}>
              <Text style={styles.postButtonText}>Gửi</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#f4f5f7' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  list: { paddingTop: 12 },
  composer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
    padding: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderColor: '#e6e6e6',
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 110,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  postButton: { backgroundColor: '#1565c0', borderRadius: 20, paddingHorizontal: 18, paddingVertical: 10 },
  postButtonText: { color: '#fff', fontWeight: '600' },
  empty: { textAlign: 'center', color: '#8a8a8a', marginTop: 24 },
  error: { color: '#c62828', paddingHorizontal: 12, paddingTop: 8 },
  modal: { flex: 1, backgroundColor: '#fff' },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderColor: '#eee',
  },
  modalTitle: { fontSize: 17, fontWeight: '600' },
  close: { color: '#1565c0' },
  comment: { paddingHorizontal: 16, paddingVertical: 10, borderBottomWidth: 1, borderColor: '#f0f0f0' },
  commentAuthor: { fontWeight: '600', marginBottom: 2 },
});
