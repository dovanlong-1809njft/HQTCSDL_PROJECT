import fakeDirectory from '../../../../../packages/mock-data/fake_members.json';

export const DIRECTORY_BRANCHES = fakeDirectory.branches;

const members = fakeDirectory.members;

export const GENERATION_OPTIONS = [
  ...new Set(members.map((member) => member.generation)),
].sort((a, b) => a - b);

function normalize(value = '') {
  return String(value)
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd');
}

export async function fetchDirectory(familyId, filters = {}) {
  const keyword = normalize(filters.keyword);
  const occupation = normalize(filters.occupation);
  const education = normalize(filters.education);
  const pageNumber = Math.max(1, Number(filters.pageNumber) || 1);
  const pageSize = Math.min(200, Math.max(1, Number(filters.pageSize) || 50));

  const filtered = members
    .filter(
      (member) =>
        !familyId || member.family_id === familyId,
    )
    .filter(
      (member) =>
        !filters.branchId || member.branch_id === filters.branchId,
    )
    .filter(
      (member) =>
        !filters.generation ||
        member.generation === Number(filters.generation),
    )
    .filter(
      (member) =>
        !keyword || normalize(member.full_name).includes(keyword),
    )
    .filter((member) => {
      const jobs = member.work_histories || [];

      if (!occupation && !filters.onlyCurrentJob) return true;

      return jobs.some((job) => {
        const isCurrent = job.end_date === null;
        const matchesOccupation =
          !occupation ||
          normalize(job.position).includes(occupation) ||
          normalize(job.company).includes(occupation);

        return (
          matchesOccupation &&
          (!filters.onlyCurrentJob || isCurrent)
        );
      });
    })
    .filter((member) => {
      if (!education) return true;

      return (member.educations || []).some(
        (item) =>
          normalize(item.institution).includes(education) ||
          normalize(item.degree).includes(education),
      );
    })
    .sort(
      (a, b) =>
        a.generation - b.generation ||
        (a.birth_date || '9999-12-31').localeCompare(
          b.birth_date || '9999-12-31',
        ) ||
        a.full_name.localeCompare(b.full_name, 'vi'),
    );

  const start = (pageNumber - 1) * pageSize;

  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
  };
}  