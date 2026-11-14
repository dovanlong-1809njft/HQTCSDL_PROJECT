import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Modal,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import {
  DIRECTORY_BRANCHES,
  fetchDirectory,
  GENERATION_OPTIONS,
} from './api';

const PAGE_SIZE = 8;

const EMPTY_FILTERS = {
  branchId: '',
  generation: null,
  occupation: '',
  education: '',
  onlyCurrentJob: false,
};

function getInitials(name) {
  return name
    .trim()
    .split(/\s+/)
    .slice(-2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}

function FilterChip({ label, selected, onPress }) {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityState={{ selected }}
      onPress={onPress}
      style={[styles.chip, selected && styles.chipSelected]}
    >
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

function MemberCard({ member }) {
  const currentJobs = (member.work_histories || []).filter(
    (job) => job.end_date === null,
  );

  return (
    <View style={styles.card}>
      <View style={styles.memberHeader}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{getInitials(member.full_name)}</Text>
        </View>

        <View style={styles.memberHeading}>
          <Text style={styles.memberName}>{member.full_name}</Text>
          <Text style={styles.meta}>
            Đời thứ {member.generation}
            {member.birth_date
              ? ` · ${new Date(`${member.birth_date}T00:00:00`).getFullYear()}`
              : ''}
          </Text>
        </View>
      </View>

      {member.location ? (
        <Text style={styles.detail}>Địa chỉ: {member.location}</Text>
      ) : null}

      {member.work_histories?.length ? (
        <View style={styles.detailBlock}>
          <Text style={styles.label}>Công việc</Text>
          {member.work_histories.map((job, index) => (
            <Text key={`${job.company}-${index}`} style={styles.detail}>
              {job.position} · {job.company}
              {job.end_date === null ? ' · Đang công tác' : ''}
            </Text>
          ))}
        </View>
      ) : null}

      {member.educations?.length ? (
        <View style={styles.detailBlock}>
          <Text style={styles.label}>Học vấn</Text>
          {member.educations.map((education, index) => (
            <Text
              key={`${education.institution}-${index}`}
              style={styles.detail}
            >
              {education.degree
                ? `${education.degree} · `
                : ''}
              {education.institution}
            </Text>
          ))}
        </View>
      ) : null}
    </View>
  );
}

export default function DirectoryScreen({ familyId }) {
  const [keyword, setKeyword] = useState('');
  const [filters, setFilters] = useState({ ...EMPTY_FILTERS });
  const [draftFilters, setDraftFilters] = useState({ ...EMPTY_FILTERS });
  const [filterVisible, setFilterVisible] = useState(false);
  const [members, setMembers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError('');

    fetchDirectory(familyId, {
      ...filters,
      keyword,
      pageNumber: page,
      pageSize: PAGE_SIZE,
    })
      .then((result) => {
        if (!active) return;
        setMembers(result.items);
        setTotal(result.total);
      })
      .catch((err) => {
        if (active) setError(err.message || 'Không tải được danh bạ.');
      })
      .finally(() => {
        if (active) {
          setLoading(false);
          setRefreshing(false);
        }
      });

    return () => {
      active = false;
    };
  }, [familyId, filters, keyword, page, revision]);

  const activeFilterCount = [
    filters.branchId,
    filters.generation,
    filters.occupation.trim(),
    filters.education.trim(),
    filters.onlyCurrentJob,
  ].filter(Boolean).length;

  function openFilters() {
    setDraftFilters({ ...filters });
    setFilterVisible(true);
  }

  function applyFilters() {
    setFilters({
      ...draftFilters,
      occupation: draftFilters.occupation.trim(),
      education: draftFilters.education.trim(),
    });
    setPage(1);
    setFilterVisible(false);
  }

  function clearFilters() {
    setFilters({ ...EMPTY_FILTERS });
    setDraftFilters({ ...EMPTY_FILTERS });
    setPage(1);
    setFilterVisible(false);
  }

  function refresh() {
    setRefreshing(true);
    setRevision((value) => value + 1);
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.title}>Danh bạ gia đình</Text>
        <Text style={styles.subtitle}>{total} thành viên</Text>
      </View>

      <View style={styles.searchRow}>
        <TextInput
          accessibilityLabel="Tìm thành viên"
          style={styles.searchInput}
          placeholder="Tìm theo tên thành viên..."
          value={keyword}
          onChangeText={(text) => {
            setKeyword(text);
            setPage(1);
          }}
          returnKeyType="search"
        />

        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Mở bộ lọc"
          style={styles.filterButton}
          onPress={openFilters}
        >
          <Text style={styles.filterButtonText}>
            Bộ lọc{activeFilterCount ? ` (${activeFilterCount})` : ''}
          </Text>
        </TouchableOpacity>
      </View>

      {error ? (
        <View accessibilityRole="alert" style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={() => setRevision((value) => value + 1)}>
            <Text style={styles.retryText}>Thử lại</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {loading && !refreshing ? (
        <ActivityIndicator
          accessibilityLabel="Đang tải danh bạ"
          color="#1565c0"
          style={styles.loading}
        />
      ) : null}

      <FlatList
        data={members}
        keyExtractor={(member) => member.id}
        renderItem={({ item }) => <MemberCard member={item} />}
        contentContainerStyle={[
          styles.listContent,
          members.length === 0 && styles.emptyList,
        ]}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={refresh} />
        }
        ListEmptyComponent={
          !loading ? (
            <Text style={styles.emptyText}>
              Không tìm thấy thành viên phù hợp.
            </Text>
          ) : null
        }
        ListFooterComponent={
          total > PAGE_SIZE ? (
            <View style={styles.pagination}>
              <TouchableOpacity
                disabled={page <= 1 || loading}
                onPress={() => setPage((value) => value - 1)}
                style={[
                  styles.pageButton,
                  (page <= 1 || loading) && styles.disabledButton,
                ]}
              >
                <Text style={styles.pageButtonText}>Trước</Text>
              </TouchableOpacity>

              <Text style={styles.pageText}>
                Trang {page} / {totalPages}
              </Text>

              <TouchableOpacity
                disabled={page >= totalPages || loading}
                onPress={() => setPage((value) => value + 1)}
                style={[
                  styles.pageButton,
                  (page >= totalPages || loading) && styles.disabledButton,
                ]}
              >
                <Text style={styles.pageButtonText}>Sau</Text>
              </TouchableOpacity>
            </View>
          ) : null
        }
      />

      <Modal
        visible={filterVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setFilterVisible(false)}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.filterSheet}>
            <View style={styles.sheetHeader}>
              <Text style={styles.sheetTitle}>Bộ lọc danh bạ</Text>
              <TouchableOpacity onPress={() => setFilterVisible(false)}>
                <Text style={styles.closeText}>Đóng</Text>
              </TouchableOpacity>
            </View>

            <ScrollView
              style={styles.filterContent}
              keyboardShouldPersistTaps="handled"
            >
              <Text style={styles.sectionTitle}>Chi nhánh</Text>
              <View style={styles.chipGroup}>
                <FilterChip
                  label="Tất cả"
                  selected={!draftFilters.branchId}
                  onPress={() =>
                    setDraftFilters((current) => ({
                      ...current,
                      branchId: '',
                    }))
                  }
                />
                {DIRECTORY_BRANCHES.map((branch) => (
                  <FilterChip
                    key={branch.id}
                    label={branch.name}
                    selected={draftFilters.branchId === branch.id}
                    onPress={() =>
                      setDraftFilters((current) => ({
                        ...current,
                        branchId:
                          current.branchId === branch.id ? '' : branch.id,
                      }))
                    }
                  />
                ))}
              </View>

              <Text style={styles.sectionTitle}>Thế hệ</Text>
              <View style={styles.chipGroup}>
                <FilterChip
                  label="Tất cả"
                  selected={!draftFilters.generation}
                  onPress={() =>
                    setDraftFilters((current) => ({
                      ...current,
                      generation: null,
                    }))
                  }
                />
                {GENERATION_OPTIONS.map((generation) => (
                  <FilterChip
                    key={generation}
                    label={`Đời ${generation}`}
                    selected={draftFilters.generation === generation}
                    onPress={() =>
                      setDraftFilters((current) => ({
                        ...current,
                        generation:
                          current.generation === generation
                            ? null
                            : generation,
                      }))
                    }
                  />
                ))}
              </View>

              <Text style={styles.sectionTitle}>Nghề nghiệp / công ty</Text>
              <TextInput
                accessibilityLabel="Lọc theo nghề nghiệp hoặc công ty"
                style={styles.filterInput}
                placeholder="Ví dụ: bác sĩ, công nghệ..."
                value={draftFilters.occupation}
                onChangeText={(text) =>
                  setDraftFilters((current) => ({
                    ...current,
                    occupation: text,
                  }))
                }
              />

              <Text style={styles.sectionTitle}>Học vấn</Text>
              <TextInput
                accessibilityLabel="Lọc theo học vấn"
                style={styles.filterInput}
                placeholder="Tên trường hoặc bằng cấp..."
                value={draftFilters.education}
                onChangeText={(text) =>
                  setDraftFilters((current) => ({
                    ...current,
                    education: text,
                  }))
                }
              />

              <FilterChip
                label="Chỉ người đang công tác"
                selected={draftFilters.onlyCurrentJob}
                onPress={() =>
                  setDraftFilters((current) => ({
                    ...current,
                    onlyCurrentJob: !current.onlyCurrentJob,
                  }))
                }
              />
            </ScrollView>

            <View style={styles.sheetActions}>
              <TouchableOpacity
                style={styles.clearButton}
                onPress={clearFilters}
              >
                <Text style={styles.clearButtonText}>Xóa lọc</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.applyButton}
                onPress={applyFilters}
              >
                <Text style={styles.applyButtonText}>Áp dụng</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#f4f5f7' },
  header: { paddingHorizontal: 16, paddingTop: 16, paddingBottom: 10 },
  title: { color: '#18212f', fontSize: 22, fontWeight: '700' },
  subtitle: { color: '#777', fontSize: 13, marginTop: 4 },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 12,
    paddingBottom: 12,
  },
  searchInput: {
    flex: 1,
    minHeight: 44,
    backgroundColor: '#fff',
    borderColor: '#ddd',
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 12,
  },
  filterButton: {
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1565c0',
    borderRadius: 10,
    paddingHorizontal: 12,
  },
  filterButtonText: { color: '#fff', fontWeight: '600' },
  listContent: { padding: 12, paddingTop: 4 },
  emptyList: { flexGrow: 1, justifyContent: 'center' },
  card: {
    backgroundColor: '#fff',
    borderColor: '#e6e6e6',
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 10,
    padding: 14,
  },
  memberHeader: { flexDirection: 'row', alignItems: 'center' },
  avatar: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e3f2fd',
    borderRadius: 22,
    marginRight: 12,
  },
  avatarText: { color: '#1565c0', fontWeight: '700' },
  memberHeading: { flex: 1 },
  memberName: { color: '#18212f', fontSize: 16, fontWeight: '700' },
  meta: { color: '#777', fontSize: 13, marginTop: 3 },
  detailBlock: { marginTop: 10 },
  label: { color: '#555', fontSize: 12, fontWeight: '700' },
  detail: { color: '#555', fontSize: 13, lineHeight: 19, marginTop: 4 },
  loading: { marginVertical: 8 },
  emptyText: { color: '#777', textAlign: 'center' },
  errorBox: {
    alignItems: 'center',
    backgroundColor: '#ffebee',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginHorizontal: 12,
    marginBottom: 8,
    padding: 10,
    borderRadius: 8,
  },
  errorText: { color: '#c62828', flex: 1, marginRight: 8 },
  retryText: { color: '#1565c0', fontWeight: '600' },
  pagination: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    paddingVertical: 12,
  },
  pageButton: {
    backgroundColor: '#e3f2fd',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  disabledButton: { opacity: 0.45 },
  pageButtonText: { color: '#1565c0', fontWeight: '600' },
  pageText: { color: '#555' },
  modalBackdrop: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0, 0, 0, 0.35)',
  },
  filterSheet: {
    maxHeight: '90%',
    backgroundColor: '#fff',
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    paddingBottom: 20,
  },
  sheetHeader: {
    alignItems: 'center',
    borderBottomColor: '#eee',
    borderBottomWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 16,
  },
  sheetTitle: { color: '#18212f', fontSize: 17, fontWeight: '700' },
  closeText: { color: '#1565c0' },
  filterContent: { paddingHorizontal: 16 },
  sectionTitle: {
    color: '#333',
    fontSize: 14,
    fontWeight: '700',
    marginTop: 16,
    marginBottom: 8,
  },
  chipGroup: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    alignSelf: 'flex-start',
    backgroundColor: '#f1f3f5',
    borderColor: '#e1e4e8',
    borderRadius: 18,
    borderWidth: 1,
    marginBottom: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  chipSelected: { backgroundColor: '#e3f2fd', borderColor: '#1565c0' },
  chipText: { color: '#555', fontSize: 13 },
  chipTextSelected: { color: '#1565c0', fontWeight: '600' },
  filterInput: {
    minHeight: 42,
    backgroundColor: '#fff',
    borderColor: '#ddd',
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 12,
  },
  sheetActions: {
    borderTopColor: '#eee',
    borderTopWidth: 1,
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  clearButton: {
    alignItems: 'center',
    borderColor: '#ddd',
    borderRadius: 9,
    borderWidth: 1,
    justifyContent: 'center',
    paddingHorizontal: 18,
    paddingVertical: 11,
  },
  clearButtonText: { color: '#555', fontWeight: '600' },
  applyButton: {
    alignItems: 'center',
    backgroundColor: '#1565c0',
    borderRadius: 9,
    flex: 1,
    justifyContent: 'center',
    paddingVertical: 11,
  },
  applyButtonText: { color: '#fff', fontWeight: '700' },
});