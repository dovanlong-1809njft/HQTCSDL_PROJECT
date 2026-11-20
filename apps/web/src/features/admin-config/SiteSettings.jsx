import { createContext, useContext, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSiteSettings } from "./api/adminConfigApi";

export const SITE_SETTINGS_QUERY_KEY = ["site-settings"];
export const SITE_SETTINGS_CHANGED = "familyconnect.site-settings.updated";
export const DEFAULT_SITE_SETTINGS = { site_name: "FamilyConnect", logo_url: "/favicon.svg", theme: "forest", registration_enabled: true };

const SiteSettingsContext = createContext({ settings: DEFAULT_SITE_SETTINGS, isPending: false, isError: false });

export function SiteSettingsProvider({ children }) {
  const query = useQuery({ queryKey: SITE_SETTINGS_QUERY_KEY, queryFn: ({ signal }) => getSiteSettings(signal),
    staleTime: 0, refetchInterval: 30000, refetchOnWindowFocus: true });
  const settings = query.data ?? DEFAULT_SITE_SETTINGS;

  useEffect(() => {
    document.documentElement.dataset.theme = settings.theme;
    document.title = `${settings.site_name} — Gia phả & Di sản gia đình`;
    document.querySelector('meta[property="og:title"]')?.setAttribute("content", `${settings.site_name} — Không gian gia đình`);
    const favicon = document.querySelector('link[rel="icon"]');
    if (favicon) {
      favicon.href = settings.logo_url;
      favicon.removeAttribute("type");
    }
  }, [settings.site_name, settings.logo_url, settings.theme]);

  useEffect(() => {
    function refresh(event) {
      if (event.key === SITE_SETTINGS_CHANGED) query.refetch();
    }
    window.addEventListener("storage", refresh);
    return () => window.removeEventListener("storage", refresh);
  }, [query.refetch]);

  return <SiteSettingsContext.Provider value={{ ...query, settings }}>{children}</SiteSettingsContext.Provider>;
}

export function useSiteSettings() {
  return useContext(SiteSettingsContext);
}
