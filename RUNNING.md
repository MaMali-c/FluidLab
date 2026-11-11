# Run FluidLab locally

The project now includes an independent physics package, a thin FastAPI adapter in
`api/`, and a React + TypeScript + Vite dashboard in `web/`. Three.js visualization is included.
No scientific equations are evaluated by the frontend; forms come from backend
metadata, and results, equations, assumptions and warnings come from the engine.

## Requirements

Python 3.10+; Node 22.12+; pnpm (via Corepack). Start in this project directory.

Terminal 1:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-api.txt
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```sh
cd web
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Open http://127.0.0.1:5173. API documentation: http://127.0.0.1:8000/docs.
Vite proxies `/api` to port 8000, so browser requests remain same-origin. Both servers
are bound to loopback. Change the proxy target in `web/vite.config.ts` if necessary.

## Checks

From project root, with the Python environment active:

```sh
python -m pytest -q
```

From `web/`, with the API running on port 8000:

```sh
corepack pnpm test
corepack pnpm build
```

Frontend integration tests require the real API. Only Plotly rendering is stubbed in
DOM tests; calculations are real HTTP requests to the Python engine. The production
build includes Plotly in a separate lazy-loaded chunk. A large-chunk warning is
expected for that scientific chart library.

## Application behavior

- Four bookmarkable module routes: `#/bernoulli`, `#/hydrostatics`, `#/pipe-flow`,
  `#/buoyancy`. Parameters are retained during page and language changes, in memory.
- English/Persian UI; document language/direction changes; logical CSS spacing;
  equations, units and numeric input stay LTR. Language preference persists locally.
- Persian/Arabic digits and Persian decimal separator are accepted. Group separators
  are intentionally rejected rather than interpreted ambiguously.
- 300 ms input debounce, aborted obsolete requests, no stale result display.
- SI only. Defaults are illustrative, not sourced fluid-property presets.
- Chart compares returned quantities sharing one unit, with values also in cards.
- Transitional/undefined results remain explicit. Warnings and assumptions are
  presented beside outputs. Model errors have Persian explanations with expandable
  original English technical details.
- Hydrostatics UI supports rectangular loading; buoyancy UI supports floating
  equilibrium for upright prisms. Other pure-engine functions are not exposed here.

## API

`GET /api/v1/models` returns bilingual field metadata and defaults.
`POST /api/v1/{module}/calculate` accepts all listed fields as an object, with numeric
SI values (not strings). The four module IDs match the routes above. Responses contain
`values` (named value/unit objects), `equations`, `assumptions`, `warnings`, `status`.
Invalid schemas or physical inputs return HTTP 422. Numerical failures are explicit.
The physics package remains independent of FastAPI and all localization code.

## Deployment boundary

This is a local application, not a hosted service. For production, serve `web/dist`
and reverse-proxy `/api` to FastAPI under the same origin. Do not use the Vite dev
server for production. Authentication, rate limiting and production hosting remain
outside this task. The frontend is not an experimental validation of the engine.

## 3D and scientific charts update

Three.js now renders all four modules using the `visualization` packet in the same
calculation response. Bernoulli provides station-only charts, hydrostatics a net
pressure profile, pipe flow accumulated dissipative loss, and buoyancy force versus
immersion. Rendering code does not calculate scientific outputs.

Drag to orbit, scroll/pinch to zoom, right-drag to pan, and use Reset view to restore
the fitted camera. Particles start paused; their speed is illustrative, not CFD.
Rendering pauses offscreen and in hidden tabs. Static scenes render on demand.
GPU resources, observers and listeners are disposed when a scene is removed.

Limits: Bernoulli connector/tank geometry is schematic; slender pipe diameter is
magnified explicitly; force vectors are scaled for readability. Minor losses are
shown at the outlet, not at known fitting locations. Transitional pipe loss remains
undefined. Buoyant bodies are upright square-base prisms, with no sinking dynamics
or rotational stability. WebGL is required for 3D; numerical results remain usable
without it. Exports and fully worked numerical substitutions remain future work.

## Engineering workspace redesign

The default page is Hydrostatics. The navy workspace includes a module sidebar,
compact SI input panel, interactive Three.js viewport, result cards, Plotly charts,
and the existing equations, assumptions, warnings and error handling. All numerical
results and chart samples continue to come from FastAPI; the physics package is unchanged.
The language button switches English/LTR and Persian/RTL without clearing inputs.
On narrow screens the navigation scrolls horizontally and panels stack vertically.

The viewport supports orbit, zoom, pan, reset and an expanded view (Escape closes
it). The grid is a visual orientation aid, not a calibrated measurement scale.
Geometry and arrows remain illustrative, not CFD. Flow Simulation has only a
clearly marked development page. Existing Buoyancy functionality remains accessible.
No new dependencies were added.

Redesign checks: 59 backend tests and 19 frontend tests passed; TypeScript and
production build passed. Live browser checks covered Hydrostatics width changes
(1 m to 2 m: net force 19613.3 N to 39226.6 N with default remaining inputs),
language switching, mobile overflow, expanded-view controls and the development
page. The build retains bundle-size advisories for the lazy-loaded Three.js and
Plotly packages. These checks do not constitute exhaustive scientific certification.

## Surface pressure colors

Blue → cyan → yellow → red maps increasing pressure in the 3D view. The bilingual
legend gives numerical limits in Pa and the pressure reference. Limits autoscale
per result; a uniform field is blue with equal limits. Gray surfaces have no mapped
pressure. The frontend only interpolates backend pressure samples for rendering.

- Hydrostatics: net pressure relative to the opposing side, only on the wetted
  rectangle, using the same samples as the pressure chart. Dry regions stay gray.
- Buoyancy: hydrostatic pressure increment relative to the free surface on the wet
  part of the upright prism (Δp = rho*g*h). No atmospheric pressure is assumed.
  For neutral/sinking bodies the immersion remains illustrative, not a solved depth.
- Pipe flow: signed pressure change from inlet due to major friction only. It is
  not absolute pressure; minor-loss positions are unknown and excluded from the
  surface map. Transitional flow has no predicted pressure map.
- Bernoulli: only the two solved station bands are colored by absolute pressure.
  The connecting geometry has no invented interior pressure field.

Pressure meshes use a small graphical offset to avoid overlapping faces; this
has no effect on calculations. The scene remains an analytical illustration, not CFD.
Validation after this addition: 64 Python tests, 21 frontend tests, TypeScript and
production build passed. Tests cover known pressure values, partial/dry/horizontal
surfaces, signed loads, uniform pressure, station-only mapping and transition flow.
