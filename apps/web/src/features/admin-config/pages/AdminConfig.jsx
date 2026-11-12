import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { getApiErrorMessage } from "@/shared/api/client";
import { createConfig, deleteConfig, getConfigs, updateConfig } from "../api/adminConfigApi";

const PAGE_SIZE = 20;
const emptyForm = { config_key: "", config_value: "", description: "" };
const fieldClass = "w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-leaf focus:ring-4 focus:ring-sage read-only:bg-stone-50";

export function AdminConfig() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [editingKey, setEditingKey] = useState(null);
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const { register, handleSubmit, reset, formState: { errors } } = useForm({ defaultValues: emptyForm });
  const queryKey = ["admin-configs", user.id, user.role];
  const query = useQuery({
    queryKey: [...queryKey, offset],
    queryFn: ({ signal }) => getConfigs({ limit: PAGE_SIZE, offset }, signal),
  });
  const rows = query.data ?? [];

  function resetForm() {
    setEditingKey(null);
    reset(emptyForm);
  }

  const save = useMutation({
    mutationFn: ({ key, payload }) => key === null ? createConfig(payload) : updateConfig(key, payload),
    onMutate: () => { setNotice(""); setActionError(""); },
    onSuccess: async (data, { key }) => {
      resetForm();
      if (key === null) setOffset(0);
      setNotice(`Đã ${key === null ? "thêm" : "lưu"} cấu hình "${data.config_key}".`);
      await queryClient.invalidateQueries({ queryKey });
    },
    onError: (error) => setActionError(getApiErrorMessage(error)),
  });

  const remove = useMutation({
    mutationFn: deleteConfig,
    onMutate: () => { setNotice(""); setActionError(""); },
    onSuccess: async (_, key) => {
      if (editingKey === key) resetForm();
      if (rows.length === 1 && offset > 0) setOffset(offset - PAGE_SIZE);
      setNotice(`Đã xóa cấu hình "${key}".`);
      await queryClient.invalidateQueries({ queryKey });
    },
    onError: async (error) => {
      setActionError(getApiErrorMessage(error));
      if (error.response?.status === 404) await queryClient.invalidateQueries({ queryKey });
    },
  });
  const busy = save.isPending || remove.isPending;

  function edit(row) {
    setNotice("");
    setActionError("");
    setEditingKey(row.config_key);
    reset({ config_key: row.config_key, config_value: row.config_value, description: row.description ?? "" });
  }

  function submit(values) {
    const payload = {
      config_value: values.config_value,
      description: values.description === "" ? null : values.description,
    };
    if (editingKey === null) payload.config_key = values.config_key;
    save.mutate({ key: editingKey, payload });
  }

  return (
    <section aria-labelledby="config-title" className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-leaf">Quản trị</p>
          <h1 id="config-title" className="mt-2 text-2xl font-bold text-forest sm:text-3xl">Cấu hình hệ thống</h1>
          <p className="mt-2 text-sm text-stone-500">Quản lý các giá trị dùng chung của FamilyConnect.</p>
        </div>
        <button type="button" onClick={() => query.refetch()} disabled={query.isFetching || busy}
          className="rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-semibold text-forest hover:bg-sage disabled:opacity-50">
          {query.isFetching ? "Đang tải…" : "Làm mới"}
        </button>
      </div>

      {notice && <p role="status" className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">{notice}</p>}
      {actionError && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{actionError}</p>}

      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0 overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
          <div className="border-b border-stone-100 px-5 py-4"><h2 className="font-semibold text-forest">Danh sách cấu hình</h2></div>
          {query.isPending ? <p role="status" className="p-6 text-sm text-stone-500">Đang tải cấu hình…</p>
            : query.isError ? <p role="alert" className="p-6 text-sm text-red-700">{getApiErrorMessage(query.error)}</p>
              : rows.length === 0 ? <p className="p-6 text-sm text-stone-500">Chưa có cấu hình trên trang này.</p>
                : <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <caption className="sr-only">Các cấu hình hệ thống và thao tác quản lý</caption>
                    <thead className="bg-stone-50 text-xs text-stone-500"><tr>
                      <th scope="col" className="px-5 py-3">Khóa / Mô tả</th>
                      <th scope="col" className="px-5 py-3">Giá trị</th>
                      <th scope="col" className="whitespace-nowrap px-5 py-3">Cập nhật (UTC)</th>
                      <th scope="col" className="px-5 py-3">Thao tác</th>
                    </tr></thead>
                    <tbody className="divide-y divide-stone-100">
                      {rows.map((row) => <tr key={row.config_key} className={editingKey === row.config_key ? "bg-sage/40" : "hover:bg-stone-50/60"}>
                        <th scope="row" className="min-w-40 px-5 py-4 align-top font-normal">
                          <span className="break-all font-mono font-semibold text-forest">{row.config_key}</span>
                          {row.description && <p className="mt-1 max-w-60 break-words text-xs text-stone-500">{row.description}</p>}
                        </th>
                        <td className="min-w-40 px-5 py-4 align-top"><p className="line-clamp-3 max-w-72 whitespace-pre-wrap break-words">{row.config_value === "" ? "(Trống)" : row.config_value}</p></td>
                        <td className="whitespace-nowrap px-5 py-4 align-top text-xs text-stone-500">{row.updated_at.replace("T", " ").replace("Z", "")}</td>
                        <td className="px-5 py-4 align-top"><div className="flex gap-3">
                          <button type="button" disabled={busy} onClick={() => edit(row)} aria-label={`Sửa ${row.config_key}`} className="font-semibold text-leaf hover:underline disabled:opacity-50">Sửa</button>
                          <button type="button" disabled={busy} onClick={() => { if (window.confirm(`Xóa cấu hình "${row.config_key}"?`)) remove.mutate(row.config_key); }} aria-label={`Xóa ${row.config_key}`} className="font-semibold text-red-600 hover:underline disabled:opacity-50">Xóa</button>
                        </div></td>
                      </tr>)}
                    </tbody>
                  </table>
                </div>}
          {!query.isError && <div className="flex items-center justify-between border-t border-stone-100 px-5 py-4 text-sm">
            <span className="text-stone-500">Trang {offset / PAGE_SIZE + 1}</span>
            <div className="flex gap-2">
              <button type="button" disabled={offset === 0 || query.isFetching || busy} onClick={() => setOffset(offset - PAGE_SIZE)} className="rounded-lg border px-3 py-2 hover:bg-sage disabled:opacity-40">Trang trước</button>
              <button type="button" disabled={rows.length < PAGE_SIZE || query.isFetching || busy} onClick={() => setOffset(offset + PAGE_SIZE)} className="rounded-lg border px-3 py-2 hover:bg-sage disabled:opacity-40">Trang sau</button>
            </div>
          </div>}
        </div>

        <form onSubmit={handleSubmit(submit)} noValidate className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold text-forest">{editingKey === null ? "Thêm cấu hình" : "Chỉnh sửa cấu hình"}</h2>
          <fieldset disabled={busy} className="mt-5 space-y-4 disabled:opacity-60">
            <div>
              <label htmlFor="config-key" className="mb-2 block text-sm font-semibold">Khóa cấu hình</label>
              <input id="config-key" className={fieldClass} maxLength={100} readOnly={editingKey !== null} placeholder="site.name"
                aria-invalid={Boolean(errors.config_key)} aria-describedby="config-key-help config-key-error"
                {...register("config_key", { required: "Bạn nhập khóa cấu hình.", maxLength: { value: 100, message: "Khóa tối đa 100 ký tự." }, pattern: { value: /^[A-Za-z0-9_.-]+$/, message: "Chỉ dùng chữ không dấu, số, dấu chấm, gạch dưới hoặc gạch ngang." } })} />
              <p id="config-key-help" className="mt-1.5 text-xs text-stone-500">{editingKey === null ? "Tối đa 100 ký tự, ví dụ site.name." : "Khóa được giữ nguyên khi chỉnh sửa."}</p>
              {errors.config_key && <p id="config-key-error" role="alert" className="mt-1 text-xs text-red-600">{errors.config_key.message}</p>}
            </div>
            <div>
              <label htmlFor="config-value" className="mb-2 block text-sm font-semibold">Giá trị</label>
              <textarea id="config-value" rows={4} className={fieldClass} {...register("config_value")} />
            </div>
            <div>
              <label htmlFor="config-description" className="mb-2 block text-sm font-semibold">Mô tả <span className="font-normal text-stone-400">(tùy chọn)</span></label>
              <textarea id="config-description" rows={3} maxLength={500} className={fieldClass} aria-invalid={Boolean(errors.description)}
                {...register("description", { maxLength: { value: 500, message: "Mô tả tối đa 500 ký tự." } })} />
              {errors.description && <p role="alert" className="mt-1 text-xs text-red-600">{errors.description.message}</p>}
            </div>
            <div className="flex flex-wrap gap-2 pt-1">
              <button type="submit" className="rounded-xl bg-forest px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#1d4034]">{save.isPending ? "Đang lưu…" : editingKey === null ? "Thêm cấu hình" : "Lưu thay đổi"}</button>
              {editingKey !== null && <button type="button" onClick={resetForm} className="rounded-xl border px-4 py-2.5 text-sm hover:bg-stone-50">Hủy chỉnh sửa</button>}
            </div>
          </fieldset>
        </form>
      </div>
    </section>
  );
}
