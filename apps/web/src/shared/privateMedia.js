import {api} from "./api/client";

export const isPrivateMedia = url => typeof url === "string" && url.startsWith("/media/uploads/");
export async function loadPrivateImage(url, signal) {
  // No token in the URL, cookies, browser history or image referrers.
  const response = await api.get(url, {baseURL:"", responseType:"blob", signal, headers:{"Cache-Control":"no-cache"}});
  return URL.createObjectURL(response.data);
}
