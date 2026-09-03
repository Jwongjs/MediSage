# MediSage — Developer Documentation

Technical reference for the evidence-based differential pipeline. For what the
product is and how to run it, see [README.md](README.md).

> **This file was rewritten on 2026-09-02.** The previous version documented a
> GPU-accelerated local-inference architecture (`LocalModelAdapter`, GGUF
> models, cuBLAS tuning), a WebSocket manager, image/skin-lesion analysis and a
> user-account system. **None of that exists.** It had drifted far enough that
> reconciling it was not possible; it was replaced rather than edited.

---

## 1. Architecture

Three LLM nodes separated by two purely deterministic stages. The deterministic
stages are where correctness lives — they are fully unit-tested and make no
network calls.

```
POST /diagnosis/start
   │
   ├─ Node A  differential ............. LLM, 1 call (candidates + plain-language definitions)
   ├─ Node B  criteria profiles ........ LLM, N calls, parallel, cached
   ├─ merge_rank_pre ................... deterministic  (builds the criterion set)
   ├─ Node C  evidence ................. LLM, 1 call (chunked above 40 criteria)
   ├─ merge_rank ....................... deterministic  (ranking + open questions)
   └─ interrupt_before=["summary"]  ◀── returns to the client here

POST /diagnosis/{id}/answers  → re-runs merge_rank out of band, rewrites state
POST /diagnosis/{id}/finalize → resumes into summary
POST /patient/export_report   → renders the evidence table as PDF or Word
```

Node A returns `{name, definition}` per candidate in one JSON call — zero
extra LLM calls for definitions. **The definition is ungrounded**: the
model's own general knowledge, not a retrieved or verified source, unlike
everything else this pipeline shows the user. Two earlier designs were tried
and superseded before landing here (raw-extracted MedlinePlus text, then
RAG-grounded LLM synthesis from a retrieved passage) — both correctly kept
the field sourced-or-omitted, but the current design deliberately trades that
guarantee for simplicity and zero added latency/cost. See §6 for the
consequence. `summary` reuses the same per-session result for the top
diagnosis instead of asking again.

`interrupt_before=["summary"]` is why `/answers` runs `MergeRankNode` directly
rather than resuming the graph: a plain resume would execute only `summary` and
ignore the answers entirely.

### State

`backend/schemas/diagnosis_schemas.py`. `MemorySaver` holds it in-process; it is
never written to disk.

| Field | Meaning |
|---|---|
| `patient_text` | the symptom narrative |
| `candidates` | Node A output |
| `explanations` | `diagnosis name → Explanation \| None`, from MedlinePlus |
| `profiles` / `grounded` | Node B output, per candidate |
| `canonical` | merged `Criterion(key, label, plain_label, kind)` list |
| `matrix` | `diagnosis → criterion key → importance` |
| `judgements` | `criterion key → {status, evidence, source}` |
| `ranking` | `list[list[str]]` — inner lists are ties |
| `not_evaluated` | candidates whose profile could not be built |
| `open_questions` | criterion keys, most discriminating first |
| `steps` | one replay entry per interaction |

`canonical` holds real `Criterion` **dataclasses**, not dicts. Do not redeclare
`Criterion` as a TypedDict — two types with one name, where state holds the
dataclass, is how attribute access starts failing at runtime.

---

## 2. The four invariants

Break any of these and the system fails **silently** — plausible output, wrong
mechanism. Each has a test; the greps below are the release gate.

**2.1 No numeric confidence, anywhere.** Not computed, stored, returned or
rendered.
```bash
grep -rn "diagnosis_confidence\|average_confidence\|final_confidence\|confidence_score" \
  backend/ my-app/src/ --include=*.py --include=*.ts --include=*.tsx
```
`split_rank` orders *questions* and must never reach the client:
```bash
grep -rn "split_rank" backend/api/
```

**2.2 Node B never sees patient text.** If the presentation is in context while
criteria are written, the model writes criteria that fit the patient, every
criterion returns `supported`, and the mechanism collapses into self-agreement.
Enforced structurally — separate node, separate prompt, separate cache key.
```bash
grep -n "patient_text" backend/nodes/profile_node.py
```
Guarded by `test_patient_text_never_reaches_the_prompt`, which asserts on the
*prompt actually sent*. Asserting on state keys is insufficient; the leak
happens inside the prompt.

**2.3 The merge stage owns the criterion key set, not the LLM.** In
`reconcile()`: requested keys the model omits default to `not_mentioned`; keys
it invents are discarded; patient answers are restricted to canonical keys.

**2.4 Evidence must be locatable in the patient's text.** `_verbatim_span()`
matches whitespace-flexibly (a textarea produces line breaks the model
normalises away) and returns the span **as the patient wrote it**, so the UI
quotes them rather than the model's paraphrase. An unlocatable quote downgrades
the criterion.

---

## 3. Module map

| Path | Responsibility |
|---|---|
| `backend/diagnosis/hpo.py` | HPO index; `normalize`, `strip_prose`, `lookup` |
| `backend/diagnosis/merge.py` | canonicalisation, the diagnosis×criterion matrix |
| `backend/diagnosis/ranking.py` | lexicographic ranking, tie groups, `split_rank` |
| `backend/knowledge/interface.py` | corpus retrieval seam (Node B grounding), no LLM — the only import surface |
| `backend/nodes/differential_node.py` | Node A — candidates + ungrounded plain-language definitions |
| `backend/nodes/profile_node.py` | Node B + process-wide profile cache |
| `backend/nodes/evidence_node.py` | Node C + deterministic reconciliation |
| `backend/nodes/summary_node.py` | severity, specialist, reused Node A explanation |
| `backend/nodes/medical_report_node.py` | PDF / Word / text export only |
| `backend/graphs/diagnosis_workflow.py` | graph wiring, `MergeRankNode` |
| `backend/api/diagnosis_routes.py` | every route |

### Ranking

Per diagnosis, tally criteria by `(importance, status)`, then order by
lexicographic comparison of an 8-field tuple — no weights, no arithmetic:

```
(strong_contradicted    asc,  strong_supported    desc,  strong_missing    asc,
 moderate_contradicted  asc,  moderate_supported  desc,  moderate_missing  asc,
 weak_contradicted      asc,  weak_supported      desc)
```

`weak_missing` is deliberately absent. Ties are returned as groups and **must
render at equal rank** — that visibility is what motivates answering questions.

An empty tally is `(0,)*8` — **neutral, not last**. A candidate with no criteria
would therefore outrank one whose criteria are merely unconfirmed, so
`MergeRankNode` excludes them from `ranking` and returns them in
`not_evaluated`. Do not "fix" this in the tuple.

### Question ordering

`split_rank = min(|present|, |candidates| - |present|) × mean importance` — zero
when a criterion is in all or no candidates, maximal at an even split. It is an
ordering key for the question list, never a property of a diagnosis.

### Profile cache

Module-level, keyed on the normalised diagnosis name, unbounded, shared across
sessions. Safe because a profile depends only on the condition — it holds no
patient data. It stores `(criteria, grounded)` together and returns a defensive
copy; a cache hit must not report an ungrounded profile as grounded, and callers
must not be able to mutate the shared entry.

---

## 4. API

No authentication. The `session_id` is the only handle on a session, so it is
full-entropy, server-generated, and ignored if a client supplies one.

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/diagnosis/start` | form `patient_text` | `{session_id, result}` |
| POST | `/diagnosis/{id}/answers` | JSON `{key: "yes"\|"no"\|"unsure"}` | `{result}` |
| POST | `/diagnosis/{id}/finalize` | — | `{result}` |
| POST | `/patient/export_report` | form `session_id`, `format`, `include_details` | file stream |
| GET | `/health` | — | probes the LLM |
| GET | `/debug/routes` | — | route list |

`result` is `_view(state)` — a deliberately narrow projection. `profiles` and
any ordering weights stay server-side. Unknown sessions return **404**, which is
also what a client sees after a restart, since state is in-process.

---

## 5. Testing

```bash
cd backend && python -m pytest tests/     # 129 tests
cd my-app  && npx tsc --noEmit && npx vite build
```

There is **no frontend test runner**, by design. Do not add one.

`tests/test_rag_embedder.py` has two tests that call a live API and are
rate-limit flaky; deselect them for a deterministic count.

`tests/test_pipeline_fixture.py` uses five real cases from the
[MACCROBAT 2020](https://figshare.com/collections/MACCROBAT/4652765) release
(CC BY 4.0). It is a regression fixture, **not a benchmark**, and publishes no
accuracy metric.

---

## 6. Known limitations

- **Lost update on `/answers`.** It reads state, recomputes and writes back with
  no compare-and-set, and `DiagnosisState` has no reducers, so concurrent
  submissions discard one — and the losing request still returns 200. The picker
  holds an in-flight latch against double-clicks; two tabs remain unhandled.
- **Single worker only.** In-process state; a second worker 404s sessions it did
  not start.
- **HPO resolution is ~35%** on real Node B output. The remaining gap is Node B
  emitting prose (`"Presence of nausea"`) where HPO names concepts; the fix is a
  prompt change, not embeddings.
- **The embedding fallback is disabled.** `merge.py` would embed all 19,836 HPO
  labels serially per call. Needs precomputed vectors first.
- **The OPQRST alternative path (spec §12.3) was never built.**
- **`plain_label` has no independent quality check.** It is Node B's own
  rewrite of its own `description`, not a separately-graded output, so a
  plain label that quietly loses the clinical specificity of its source
  criterion (e.g. broadens "McBurney's point tenderness" into generic
  "belly pain") would not be caught by anything in the pipeline today.
- **The consumer definition is fully ungrounded LLM output — the one field in
  this pipeline with no sourcing, no verification, and no structural check of
  any kind.** Node A is asked for a plain-language definition of each
  candidate from its own general knowledge; nothing retrieves, cites, or
  checks it. This is a real, deliberate step down in reliability from
  everything else the system shows a user: Node B's criteria are at least
  attributable to a candidate's medical literature (when the corpus has
  coverage), and Node C's evidence must quote the patient's own text
  verbatim or get downgraded. The definition has neither. Two prior designs
  (raw MedlinePlus extraction, then RAG-grounded LLM synthesis from a
  retrieved MedlinePlus passage) kept it sourced-or-omitted; both were
  superseded in favour of this simpler, zero-extra-call version. If asked
  in an interview "how do you know this isn't hallucinated" — the honest
  answer is "I don't, for this one field, and here's what I gave up to get
  there and why (§1)."

---

## 7. Where the history lives

`docs/` is gitignored, so these are on-disk only:

- `docs/superpowers/specs/2026-09-01-project-a-evidence-differential-design.md`
  — the design and its rationale.
- `docs/superpowers/plans/…-ledger.md` — the execution record: every deviation,
  25 defects found in the plan, and the outstanding decisions.
- `docs/archive/removed-auth-2026-09-02/` — the deleted account system, with
  restore instructions. Git restore point `9b0c1b5`.

---

## 8. Dead code — present but unused

Not deleted, so that greps do not mislead you into thinking it is live:

- `backend/adapters/` — the pre-Groq local-inference era.
- `backend/models/ai_schema.py`, `backend/nodes/old_version_ref/` — same era.
- `backend/test/` (singular) — old GPU/CUDA scripts. The live suite is
  `backend/tests/` (plural); `pytest.ini` scopes to it.
- `backend_reference_example/` — a reference copy at the repo root.
- `GPU_ACCELERATION_GUIDE.md` (root and `backend/`) and `how-to-run.txt` —
  **actively misleading.** `how-to-run.txt` instructs you to download an 8 GB
  GGUF file and claims the backend will not start without it. That is false.
