# Build log

Built on November 11, 2026. Commands below can be reproduced from the repository root.
Commit subjects describe concrete checkpoints; `git log --oneline --reverse` is authoritative.

1. **Initialize Python package and safe configuration** (`1157849`). Created an isolated
   local Git repository, installable src-layout package, CLI entry point, environment template
   and ignore rules. Existing workspace projects were preserved.
2. **Validated workflow and budgeted provider** (`423aec0`). Added strict evidence contracts,
   bounded parsers, deterministic scoring, three role prompts, explicit live mode, per-run
   Decimal reservations and metadata auditing.
3. **Offline data and hash-bound replay** (`c8d38ab`). Added four synthetic resumes, explicit
   rubric, curated stage outputs and reproducible fixture generation. Ran the complete demo
   with six replayed responses and zero API calls.
4. **Contract and SDK transport verification** (`e9efb70`). Added offline tests, the evaluation
   script, CI configuration and lint hooks. Verified the installed official SDK's schema
   transformation and Count Tokens signature. Corrected the metadata output-limit field to
   `max_tokens`, used the same output schema for counting and generation, and bounded file
   output behavior. The local run passed 61 tests with 93% coverage.
5. **Documentation checkpoint.** Added architecture, threat model, honest limitations,
   competency matrix, project narrative, interview answers and reproducible evaluation evidence.
   The five offline evaluation checks passed using 12 fixture responses and zero API calls.
6. **Demo and release checkpoint.** Captured actual offline output as a transcript, asciinema
   event file and rendered GIF. Manually exercised terminal decline. Completed final lint,
   tests, regression and packaging checks before preparing the public repository.
7. **Publication and CI.** Published [sharath559/talentscout](https://github.com/sharath559/talentscout).
   [CI run 43057637526](https://github.com/sharath559/talentscout/actions/runs/43057637526)
   passed all three Python jobs (3.10, 3.12, 3.14), including lint, format, tests and offline
   evaluation. Both wheel and source distribution built successfully locally.

## Deviations from the original proposal

- Used argparse and an installable `src/talentscout/` package instead of flat import modules.
- Fixed rubric coverage points replace ungrounded fit probabilities and tournament ranking.
- A fairness flag blocks simulated approval; an empty result is not called unbiased.
- Used current SDK schema transformation and local strict validation, not JSON prompting alone.
- Implemented a conservative application budget, without claiming provider spend-limit administration.
- Kept dispatch sequential; no agent framework, Gemini/ADK dependency, Node or React was added.
- No prompt caching, model fallback or MCP is claimed as implemented.
- Replaced invented business outcomes and fairness guarantees with recorded offline evidence.
- No live Claude calls were run. No secrets, real resumes or approval decisions were published.

## Environment

Initial dependency installation required network access. Restricted cache writes were resolved
by setting `UV_CACHE_DIR=/tmp/talentscout-uv-cache` in the build environment. Normal local
machines can use uv's default cache. The lockfile records resolved dependencies. A sandboxed
GitHub auth check initially failed; the network-enabled check confirmed valid authentication.
