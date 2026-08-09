# Evidence

- `npm run build`: Next.js 16.3.0 compiled successfully and generated 23/23 routes.
- `npm run lint`: exit 0 with five non-blocking legacy image/navigation warnings and no errors.
- `npm audit --omit=dev`: 0 vulnerabilities.
- `python3 -m unittest discover -s ingestion/tests -v`: 5/5 freshness policy tests passed.
- `python3 -m compileall`: freshness and hazard modules compiled.
- `git diff --check`: passed.
- `zsh -n START_CHEAPHOUSE.command` and executable-bit check: passed.
- Production smoke: `/`, `/properties`, and `/verify` returned 200.
- Redirect smoke: `/pricing` -> `/verify`; `/fr/properties` -> `/properties`.
- Security smoke: disabled subscription checkout returned 410; unsigned/unconfigured webhook returned 503; unconfigured intake returned 503.
- Desktop renders inspected at `cheaphouse-home.png` and `cheaphouse-verify.png` in the task visualization folder.
