# Verification

- Python physics + API tests: **59 passed**.
- Frontend tests against live FastAPI: **19 passed**.
- TypeScript strict compilation: **passed**.
- Vite production build: **passed**.
- Browser preview: confirmed returned calculations and Plotly charts.
- Persian desktop: translated controls/results, RTL document, mirrored sidebar,
  no document horizontal overflow at a 1440px viewport.
- Persian mobile: verified at 390px; single-column inputs, scrollable module navigation,
  no document horizontal overflow.
- English/LTR restoration: verified; input values retained across language changes.

Frontend checks cover all four live HTTP calculations, all four rendered module
pages, input-driven updates, invalid-input result clearing, backend physical errors,
connection errors, Persian digits, and language/dir switching. DOM tests stub chart
rendering and omit jsdom AbortSignals in their Node HTTP bridge; they do not assert
network cancellation. Charts were checked in the real browser separately.

Nonblocking tool warnings: Plotly's lazy-loaded bundle exceeds Vite's 500 kB warning
threshold (about 378 kB gzip); Starlette reports a test-client httpx deprecation.
No scientific validation claims beyond the existing analytical reference tests.

See RUNNING.md to restart the local application. No hosted deployment was made. Three.js scenes were added and inspected in the browser.

3D checks: API tests assert geometry and chart sampling for all four modules,
including dry surfaces, rest, transition and no-equilibrium cases. Frontend tests
assert a single input change updates both geometry and chart tables in each module.
Five Three.js adapter tests build/dispose real API geometry and check area changes.
GPU rendering was inspected manually for all four scenes, including particle play
and orbit/reset controls. Automated DOM tests mock GPU rendering.
