import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { getApiErrorMessage } from "@/shared/api/client";
import { deleteConfig, getConfigs, saveSiteSettings } from "../api/adminConfigApi";
import { SITE_SETTINGS_CHANGED, SITE_SETTINGS_QUERY_KEY, useSiteSettings } from "../SiteSettings";

const PAGE_SIZE = 20;
const fieldClass = "w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-leaf focus:ring-4 focus:ring-sage read-only:bg-stone-50";

function validLogoUrl(value) {
  if (!value || /[\s\\\u0000-\u001f]/.test(value)) return false;
  if (value.startsWith("/") && !value.startsWith("//")) return true;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password;
  } catch { return false; }
}

function WebsiteSettingsForm({ onSaved }) {
  const site = useSiteSettings();
  const cache = useQueryClient();
  const [failedLogo, setFailedLogo] = useState(null);
  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm({ values: site.settings, resetOptions: { keepDirtyValues: true } });
  const logo = watch("logo_url")?.trim() || "";
  const enabled = watch("registration_enabled");
  const save = useMutation({ mutationFn: saveSiteSettings, onSuccess: async (data) => {
    reset(data, { keepDirtyValues: false });
    cache.setQueryData(SITE_SETTINGS_QUERY_KEY, data);
    await onSaved();
  } });

  return <section className="rounded-2xl border border-stone-200 bg-white p-5" aria-labelledby="website-settings-title">
    <h2 id="website-settings-title" className="font-semibold text-forest">Thiết lập website</h2>
    <p className="mt-2 text-sm text-stone-600">Tên, logo và màu giao diện sẽ áp dụng cho mọi người sau khi lưu.</p>
    {site.isPending ? <p role="status" className="mt-4 text-sm">Đang tải thiết lập…</p>
      : site.isError ? <div className="mt-4"><p role="alert" className="text-sm text-red-700">{getApiErrorMessage(site.error)}</p><button type="button" className="mt-3 text-sm underline" onClick={() => site.refetch()}>Thử lại</button></div>
        : <form className="mt-5" onSubmit={handleSubmit((values) => save.mutate(values))} noValidate>
          <fieldset disabled={save.isPending} className="grid gap-5 md:grid-cols-2">
            <div><label htmlFor="website-name" className="mb-2 block text-sm font-semibold">Tên website</label>
              <input id="website-name" required maxLength={60} className={fieldClass} aria-invalid={Boolean(errors.site_name)}
                {...register("site_name", { required: "Bạn nhập tên website.", setValueAs: (value) => value.trim(), validate: (value) => Boolean(value.trim()) || "Tên website không được chỉ gồm khoảng trắng.", maxLength: { value: 60, message: "Tên website tối đa 60 ký tự." } })} />
              {errors.site_name && <p role="alert" className="mt-1 text-xs text-red-600">{errors.site_name.message}</p>}
            </div>
            <div><label htmlFor="website-theme" className="mb-2 block text-sm font-semibold">Màu giao diện</label>
              <select id="website-theme" className={fieldClass} {...register("theme", { required: true })}>
                <option value="forest">Xanh lá</option><option value="ocean">Xanh dương</option><option value="warm">Nâu ấm</option>
              </select>
            </div>
            <div className="min-w-0"><label htmlFor="website-logo" className="mb-2 block text-sm font-semibold">URL logo</label>
              <div className="flex items-start gap-3"><input id="website-logo" required maxLength={2048} className={fieldClass} aria-invalid={Boolean(errors.logo_url)}
                {...register("logo_url", { required: "Bạn nhập URL logo.", setValueAs: (value) => value.trim(), validate: (value) => validLogoUrl(value.trim()) || "Dùng URL HTTPS hoặc đường dẫn bắt đầu bằng /." })} />
                <img key={logo} className="h-11 w-11 shrink-0 rounded-lg object-contain" src={validLogoUrl(logo) && failedLogo !== logo ? logo : "/favicon.svg"} alt="Xem trước logo" onError={() => setFailedLogo(logo)} />
              </div>
              <p className="mt-1 text-xs text-stone-500">Dùng /favicon.svg để trở về logo mặc định.</p>
              {errors.logo_url && <p role="alert" className="mt-1 text-xs text-red-600">{errors.logo_url.message}</p>}
              {logo && failedLogo === logo && <p role="alert" className="mt-1 text-xs text-red-600">Không tải được logo. Hãy kiểm tra đường dẫn hoặc dùng logo mặc định.</p>}
            </div>
            <div><label className="flex min-h-11 items-center gap-3 text-sm font-semibold"><input type="checkbox" {...register("registration_enabled")} />Cho phép đăng ký tài khoản mới</label>
              <p className="mt-1 text-sm text-stone-600">{enabled ? "Đang mở đăng ký." : "Đăng ký sẽ tạm đóng."} Tài khoản đã có vẫn đăng nhập được.</p>
            </div>
            {save.isError && <p role="alert" className="text-sm text-red-700 md:col-span-2">{getApiErrorMessage(save.error)}</p>}
            <div className="flex flex-wrap gap-3 md:col-span-2"><button type="submit" disabled={save.isPending || Boolean(logo && failedLogo === logo)} className="rounded-xl bg-forest px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{save.isPending ? "Đang lưu…" : "Lưu thiết lập website"}</button>
              <button type="button" className="rounded-xl border border-stone-200 px-4 py-2.5 text-sm" onClick={() => { reset(site.settings, { keepDirtyValues: false }); save.reset(); }}>Hủy thay đổi</button>
            </div>
          </fieldset>
        </form>}
  </section>;
}

export function AdminConfig() {
  const { user } = useAuth();
  const site = useSiteSettings();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const queryKey = ["admin-configs", user.id, user.role];
  const query = useQuery({
    queryKey: [...queryKey, offset],
    queryFn: ({ signal }) => getConfigs({ limit: PAGE_SIZE, offset }, signal),
  });
  const rows = query.data ?? [];

  function refreshSiteSettings() {
    queryClient.invalidateQueries({ queryKey: SITE_SETTINGS_QUERY_KEY });
    localStorage.setItem(SITE_SETTINGS_CHANGED, String(Date.now()));
  }

  const remove = useMutation({
    mutationFn: deleteConfig,
    onMutate: () => { setNotice(""); setActionError(""); },
    onSuccess: async (_, key) => {
      refreshSiteSettings();
      if (rows.length === 1 && offset > 0) setOffset(offset - PAGE_SIZE);
      setNotice(`Đã xóa cấu hình "${key}".`);
      await queryClient.invalidateQueries({ queryKey });
    },
    onError: async (error) => {
      setActionError(getApiErrorMessage(error));
      if (error.response?.status === 404) await queryClient.invalidateQueries({ queryKey });
    },
  });
  const busy = remove.isPending;

  return (
    <section aria-labelledby="config-title" className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-leaf">Quản trị</p>
          <h1 id="config-title" className="mt-2 text-2xl font-bold text-forest sm:text-3xl">Cấu hình hệ thống</h1>
          <p className="mt-2 text-sm text-stone-500">Quản lý các giá trị dùng chung của {site.settings.site_name}.</p>
        </div>
        <button type="button" onClick={() => { query.refetch(); site.refetch(); }} disabled={query.isFetching || busy}
          className="rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-semibold text-forest hover:bg-sage disabled:opacity-50">
          {query.isFetching ? "Đang tải…" : "Làm mới"}
        </button>
      </div>

      {notice && <p role="status" className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">{notice}</p>}
      {actionError && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{actionError}</p>}

      <WebsiteSettingsForm onSaved={async () => {
        setNotice("Đã lưu thiết lập website."); setActionError(""); refreshSiteSettings();
        await queryClient.invalidateQueries({ queryKey });
      }} />

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
                    {rows.map((row) => <tr key={row.config_key} className="hover:bg-stone-50/60">
                      <th scope="row" className="min-w-40 px-5 py-4 align-top font-normal">
                        <span className="break-all font-mono font-semibold text-forest">{row.config_key}</span>
                        {row.description && <p className="mt-1 max-w-60 break-words text-xs text-stone-500">{row.description}</p>}
                      </th>
                      <td className="min-w-40 px-5 py-4 align-top"><p className="line-clamp-3 max-w-72 whitespace-pre-wrap break-words">{row.config_value === "" ? "(Trống)" : row.config_value}</p></td>
                      <td className="whitespace-nowrap px-5 py-4 align-top text-xs text-stone-500">{row.updated_at.replace("T", " ").replace("Z", "")}</td>
                      <td className="px-5 py-4 align-top"><div className="flex gap-3">
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

    </section>
  );
}
