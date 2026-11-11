# Demo walkthrough

## Three-minute presentation

1. Run `uv run talent_scout --offline --metrics`. State that the four resumes and all
   responses are curated synthetic fixtures, and no Claude call is being made.
2. Explain the 35/25/25/15 rubric and the supported/partial/not_stated labels. Show an
   exact quote and one missing-information question. Coverage points are not hiring odds.
3. Run `uv run talent_scout --review`. Inspect the source evidence, then type `n` to show
   decline. A separate run may demonstrate `y`; it records only `approved_simulation`.
4. Show `uv run talent_scout --format json` and `uv run python scripts/evaluate.py`.
5. Show the negative tests for invented quotes, modified Judge order and timeouts.
6. Explain that live quality and fairness are unmeasured. Describe the paid eval command
   without running it unless configured and intended.

`bash scripts/demo.sh` runs the noninteractive offline pipeline and regression checks.
For a local report, create `artifacts/` and pass a new `--output artifacts/review.json` path.

## Artifacts

- `demo.gif`: animated pages rendered from actual captured CLI output, not a desktop screencast.
- `demo.cast`: asciinema v2 output events captured from the process; replay with `asciinema play docs/demo.cast`.
- `demo-transcript.txt`: the complete unedited output, including the zero-call metrics.
- `demo-preview.png`: the first animation frame for static sharing.
- `evaluation-results.json`: the actual offline regression report.

Regenerate the recording with `uv run python scripts/capture_demo.py`. It runs only the
offline CLI and uses Pillow to render the transcript. It never supplies an approval response.
Captured dependencies are locked, and fixture source text can be inspected in `data/`.

The terminal review path was also exercised in a real local PTY: typing `n` printed
`Aborted by user.` and completed with zero API calls. Automated tests cover yes, no,
blank input and the nonterminal refusal separately.
