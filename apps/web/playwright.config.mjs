import {defineConfig} from "@playwright/test";
import {tmpdir} from "node:os";
import {join} from "node:path";

export default defineConfig({
  testDir:"../../tests/e2e",
  testMatch:["ux-upgrades.spec.mjs","profile-events.spec.mjs"],
  outputDir:join(tmpdir(),"familyconnect-ux-playwright"),
  reporter:"list",
  workers:1,
  use:{baseURL:"http://127.0.0.1:5179",headless:true},
  webServer:{command:"node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5179 --strictPort",url:"http://127.0.0.1:5179",reuseExistingServer:false},
});
