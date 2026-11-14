import { api } from '../../core/api';

// Đời 1..10. Backend chưa có API trả số đời tối đa nên dùng danh sách cố định.
export const GENERATION_OPTIONS = Array.from({ length: 10 }, (_, i) => i + 1);

// GET /api/genealogy/directory -> genealogy.usp_SearchDirectory
// Trả về { items, total }. Mỗi item: id, full_name, birth_date, location, generation,
// latest_position, latest_company, latest_institution, latest_degree.
export async function fetchDirectory(familyId, filters = {}) {
  const keyword = (filters.keyword || '').trim();
  const occupation = (filters.occupation || '').trim();
  const education = (filters.education || '').trim();
  const pageNumber = Math.max(1, Number(filters.pageNumber) || 1);
  const pageSize = Math.min(200, Math.max(1, Number(filters.pageSize) || 50));

  const data = await api.get('/genealogy/directory', {
    family_id: familyId,
    keyword: keyword || undefined,
    occupation: occupation || undefined,
    // usp_SearchDirectory chỉ áp dụng "đang công tác" cùng với ô nghề nghiệp
    only_current_job: occupation && filters.onlyCurrentJob ? true : undefined,
    education: education || undefined,
    generation: filters.generation || undefined,
    branch_id: filters.branchId || undefined,
    page: pageNumber,
    page_size: pageSize,
  });

  return { items: data.items, total: data.total };
}