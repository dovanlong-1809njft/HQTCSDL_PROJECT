import {defineConfig} from "@playwright/test";
import {tmpdir} from "node:os";
import {join} from "node:path";

export default defineConfig({
  testDir:"../../tests/e2e",testMatch:"upload-live.spec.mjs",workers:1,reporter:"list",
  outputDir:join(tmpdir(),"familyconnect-upload-playwright"),
  use:{baseURL:"http://127.0.0.1:18101",headless:true},
});
