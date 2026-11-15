import {test} from "node:test";
import assert from "node:assert/strict";
import {safeMedia,isImageUrl} from "../../apps/web/src/shared/media.mjs";

test("media accepts HTTPS and existing media paths only",()=>{
  for(const url of ["https://example.org/a.jpg?x=1","/media/heritage/a.jpg"])assert.equal(safeMedia(url),url);
  for(const url of [null,"","javascript:alert(1)","data:image/png,abc","//evil.com/x","/\\evil.com/x","http://a.com/x","https://user:pass@a.com/x","https://a.com/\nx","/api/auth/me"])assert.equal(safeMedia(url),null);
});
test("documents are not inferred as images",()=>{
  assert.equal(isImageUrl("/media/a.pdf"),false);
  assert.equal(isImageUrl("https://example.org/a.JPG?download=1"),true);
});
