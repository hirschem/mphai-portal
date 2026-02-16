# MPH AI Portal — Pre-Commit Checklist

Before every commit, verify:

- [ ] **Backend runs locally** (`uvicorn app.main:app --reload` in apps/api)
- [ ] **Auth returns 401 without header** (try `/api/auth/login` with no Authorization)
- [ ] **Admin saves round-trip** (PUT/GET `/api/admin-saves/{kind}/{entity_id}`)
- [ ] **Restart backend → data persists** (if `/data` is persistent)
- [ ] **Frontend builds cleanly** (`npm run build` in apps/web)
- [ ] **Save → refresh works** (Invoice + Book pages)
- [ ] **Incognito auth behavior correct** (test in private window)
- [ ] **git diff shows only intended files**

If all boxes are checked, commit confidently.
