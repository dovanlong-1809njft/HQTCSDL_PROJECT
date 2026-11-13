import React, { useEffect, useState } from 'react';
import { Alert, ActivityIndicator, Button, FlatList, Linking, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

const tabs = { items: 'Di sản', honors: 'Vinh danh', ranking: 'Xếp hạng' };

function Editor({ resource, row, busy, onSave, onCancel }) {
  const [form, setForm] = useState({ type: 'story', title: '', description: '', content: '', media_url: '', member_id: '', date_awarded: '', ...row });
  const field = (name, label, maxLength, multiline = false) => <View><Text>{label}</Text><TextInput accessibilityLabel={label} editable={!busy} style={styles.input} value={form[name] || ''} maxLength={maxLength} multiline={multiline} onChangeText={(text) => setForm((old) => ({ ...old, [name]: text }))} /></View>;
  function save() {
    const payload = { title: form.title.trim(), description: form.description?.trim() || null };
    if (resource === 'items') Object.assign(payload, { type: form.type, content: form.content?.trim() || null, media_url: form.media_url?.trim() || null });
    else {
      payload.date_awarded = form.date_awarded || null;
      if (!row?.id) payload.member_id = form.member_id;
    }
    if (row?.id) payload.expected_version = row.version_token;
    onSave(payload);
  }
  return <ScrollView style={styles.editor} keyboardShouldPersistTaps="handled"><Text style={styles.heading}>{row?.id ? 'Chỉnh sửa' : 'Thêm mới'}</Text>
    {resource === 'items' && <View style={styles.actions}>{['document', 'story', 'photo'].map((type) => <Button key={type} title={`${form.type === type ? '✓ ' : ''}${type}`} disabled={busy} onPress={() => setForm((old) => ({ ...old, type }))} />)}</View>}
    {resource === 'honors' && !row?.id && field('member_id', 'Mã hồ sơ thành viên (UUID)', 36)}
    {field('title', 'Tiêu đề', 200)}{field('description', 'Mô tả', resource === 'items' ? 500 : 1000, true)}
    {resource === 'items' ? <>{field('content', 'Nội dung', 200000, true)}{field('media_url', 'URL HTTPS hoặc /media/', 500)}<Text>Chưa hỗ trợ tải tệp lên.</Text></> : field('date_awarded', 'Ngày trao (YYYY-MM-DD)', 10)}
    <Button title={busy ? 'Đang lưu…' : 'Lưu'} disabled={busy} onPress={save} /><Button title="Hủy" disabled={busy} onPress={onCancel} />
  </ScrollView>;
}

export function HeritageScreen({ api, user }) {
  const [families, setFamilies] = useState([]);
  const [familyId, setFamilyId] = useState('');
  const [resource, setResource] = useState('items');
  const [page, setPage] = useState(1);
  const [q, setQ] = useState('');
  const [type, setType] = useState('');
  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [editor, setEditor] = useState(null);
  const [detail, setDetail] = useState(null);
  const [revision, setRevision] = useState(0);
  const [familyRevision, setFamilyRevision] = useState(0);
  const manager = ['admin', 'family_head'].includes(user.role);
  useEffect(() => {
    let active = true;
    setFamilies([]); setFamilyId(''); setData({ items: [], total: 0 });
    api.families().then((rows) => { if (active) { setFamilies(rows); setFamilyId(rows[0]?.id || ''); setLoading(false); } })
      .catch((err) => { if (active) { setError(err.message); setLoading(false); } });
    return () => { active = false; };
  }, [api, user.id, familyRevision]);
  useEffect(() => {
    if (!familyId) return;
    let active = true;
    setLoading(true); setError(''); setData({ items: [], total: 0 }); setDetail(null);
    api.list(resource, familyId, { page, page_size: 12, q, ...(resource === 'items' && type ? { item_type: type } : {}) })
      .then((rows) => { if (active) setData(rows); }).catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [api, familyId, resource, page, q, type, revision]);
  async function write(operation) {
    if (busy) return;
    setBusy(true); setError('');
    try { await operation(); setEditor(null); setDetail(null); setPage(1); setRevision((r) => r + 1); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  function changeTab(tab) { setResource(tab); setPage(1); setEditor(null); setDetail(null); setError(''); }
  async function openDetail(row) {
    try { setDetail(await api.get(resource, familyId, row.id)); } catch (err) { setError(err.message); }
  }
  function remove(row) { Alert.alert('Xác nhận xóa', row.title, [{ text: 'Hủy', style: 'cancel' }, { text: 'Xóa', style: 'destructive', onPress: () => write(() => api.remove(resource, familyId, row)) }]); }
  async function openMedia(url) {
    if (!/^https:\/\//i.test(url || '') || /[\s\\]/.test(url)) { setError('Mobile cần URL HTTPS đầy đủ để mở tệp.'); return; }
    try { await Linking.openURL(url); } catch { setError('Không mở được đường dẫn media.'); }
  }
  return <View style={styles.container}><Text style={styles.heading}>Di sản & Vinh danh</Text>
    {error ? <View accessibilityRole="alert"><Text>{error}</Text><Button title="Thử lại" onPress={() => { setRevision((r) => r + 1); if (!families.length) setFamilyRevision((r) => r + 1); }} /></View> : null}
    <ScrollView horizontal style={styles.familyBar}>{families.map((f) => <Button key={f.id} title={`${familyId === f.id ? '✓ ' : ''}${f.name}`} disabled={busy} onPress={() => { setFamilyId(f.id); setPage(1); setEditor(null); }} />)}</ScrollView>
    {!loading && !families.length && <Text>Chưa có gia đình liên kết; liên hệ người quản lý để xác minh.</Text>}
    {!!familyId && <><View style={styles.actions}>{Object.entries(tabs).map(([key, label]) => <Button key={key} title={label} disabled={busy} onPress={() => changeTab(key)} />)}</View>
      <TextInput accessibilityLabel="Tìm kiếm" style={styles.input} placeholder="Tìm tiêu đề / thành viên" maxLength={200} value={q} onChangeText={(text) => { setQ(text); setPage(1); }} />
      {resource === 'items' && <View style={styles.actions}>{['', 'story', 'photo', 'document'].map((value) => <Button key={value} title={value || 'Tất cả'} onPress={() => { setType(value); setPage(1); }} />)}</View>}
      {resource !== 'ranking' && (resource === 'items' || manager) && <Button title="Thêm mới" disabled={busy} onPress={() => setEditor({})} />}
      {editor && <Editor key={editor.id || 'new'} resource={resource} row={editor} busy={busy} onCancel={() => setEditor(null)} onSave={(payload) => write(() => editor.id ? api.update(resource, familyId, editor.id, payload) : api.create(resource, familyId, payload))} />}
      {detail && <View style={styles.card}><Text style={styles.heading}>{detail.title}</Text><Text>{detail.description}</Text><Text>{detail.content}</Text>{detail.media_url && <Button title="Mở media" onPress={() => openMedia(detail.media_url)} />}<Button title="Đóng chi tiết" onPress={() => setDetail(null)} /></View>}
      {loading ? <ActivityIndicator accessibilityLabel="Đang tải" /> : <FlatList data={data.items} keyExtractor={(row) => row.id || row.member_id} ListEmptyComponent={<Text>Chưa có kết quả.</Text>} renderItem={({ item }) => <View style={styles.card}>
        <Text style={styles.heading}>{resource === 'ranking' ? `#${item.rank} ${item.full_name} · ${item.honor_count} danh hiệu` : item.title}</Text><Text>{item.description}</Text>
        {resource !== 'ranking' && <><Button title="Chi tiết" onPress={() => openDetail(item)} />{(manager || (resource === 'items' && item.created_by_user_id === user.id)) && <View style={styles.actions}><Button title="Sửa" disabled={busy} onPress={() => setEditor(item)} /><Button title="Xóa" disabled={busy} onPress={() => remove(item)} /></View>}</>}
      </View>} />}
      <View style={styles.actions}><Button title="Trước" disabled={page === 1 || busy} onPress={() => setPage((p) => p - 1)} /><Text>Trang {page} · {data.total} kết quả</Text><Button title="Sau" disabled={page * 12 >= data.total || busy} onPress={() => setPage((p) => p + 1)} /></View>
    </>}
  </View>;
}

const styles = StyleSheet.create({ container: { flex: 1, padding: 16, backgroundColor: '#f6f5ef', gap: 10 }, heading: { fontSize: 18, fontWeight: '700', color: '#254f3e' },
  actions: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 8 }, input: { borderWidth: 1, borderColor: '#aaa', backgroundColor: 'white', padding: 10, borderRadius: 8 },
  card: { padding: 12, backgroundColor: 'white', marginVertical: 6, borderRadius: 12, gap: 8 }, familyBar: { maxHeight: 48 }, editor: { maxHeight: 340, backgroundColor: 'white', padding: 10 } });
