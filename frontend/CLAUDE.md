# Frontend

## Commands (in order)
- Typecheck: `npm run typecheck` (fast, run first)
- Tests: `npm test` (Vitest + Testing Library, jsdom; no network)
  - one file: `npx vitest run src/pages/Fresher.test.tsx`
- Lint: `npm run lint`
- Dev: `npm run dev` (Vite on 0.0.0.0:5173; needs the API at `VITE_API_URL`, default `http://localhost:8000`)
- Screenshots for UI review: `node scripts/screenshots.mjs http://127.0.0.1:5173 screenshots <passphrase> / /receipts`
  (390/768/1440, light and dark; reports horizontal overflow and console errors)

## Architecture
- `src/main.tsx`: fonts, tokens, QueryClient (any `AuthError` re-locks the gate), router.
- `src/App.tsx`: routes, nav, page wipe; sets `body[data-page]` so each page wears its own paper.
- `src/lib/api.ts` is the only place that talks to the backend; `src/lib/types.ts` mirrors its models.
- `src/lib/copy.ts` holds every line with personality. `src/lib/money.ts` formats ₹ LPA / Cr.
- `src/styles/tokens.css` is the design system (colour, type, motion tokens, light and dark);
  one CSS file per page beside it. No Tailwind.
- `src/lib/motion.ts`: ✱ burst and `useParallax` (`[data-depth]` layers); both respect reduced motion.

## Rules
- TypeScript strict, no `any`, no `!` assertions; no `.js`/`.jsx` source files.
- Colours only through tokens in `tokens.css`; every new token gets light and dark values.
- New copy goes in `copy.ts`, not inline.
- Status changes are optimistic and roll back on error with a toast that says what the server said.
- Tests stub `fetch` with `src/test/fakeApi.tsx`; never hit a real API.

## Gotchas
- A `<output>` element has the `status` role too: find the toast by name (`Notifications`).
- `react-router` is pinned to v7: v8 needs newer docs than Context7 had when this was built.
