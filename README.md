# Story Studio — session demo

One PDF/DOCX intake → compact fact summary → Story focus → Case Study or One-Pager → validation → human review.

## Run locally

Requires Python 3.10+. Run `python -m pip install -r requirements.txt`, copy `.env.example` to `.env`, and configure the provider variables. Start `python server.py` and open its printed address. The bundled workspace Python already has the runtime dependencies; `start.ps1` uses it when available.

The frontend keeps state in browser session storage. Refresh restores the tab's work; use a new tab/private window for an independent session. Server-side projects and uploads are not persisted in session mode. Copy/download draft text before closing the tab. API credentials stay on the server.

## Intake summary and optional review

After reading an intake, the app shows what it understood: client context, the problem, what changed and the result. Click **Continue with intake** to accept clear, source-backed facts; there is no mandatory checkbox or requirement to fix a category label. Individual review is optional and the writer can return later.

Flagged facts are collapsed under an optional review panel. Ambiguous metrics, unverified interpretations and restrictions remain excluded until resolved. Missing story classifications are advisory, not evidence that the document lacks the information. Extraction recognises alternate wording and measured results can fulfil the outcome role without duplicating a metric as another fact. Baseline and projected figures do not count as achieved results.

Even if no usable facts remain, the writer can open an editable draft with visible evidence-pending placeholders, save it and add evidence later. These placeholders are not real factual content and cannot pass final approval. Unresolved claims and unavailable validation still prevent approval; continuing is not automatic verification or human approval. The acceptance record distinguishes clicking Continue from individual fact confirmation.

## Deploy to Vercel

See DEPLOY-VERCEL.md. Deploy the clean story-studio-vercel.zip contents or this folder with secrets and data excluded. The Vercel Python adapter is api/index.py, static output is web/, and vercel.json supplies routing and duration configuration. Set Groq credentials in Vercel Environment Variables. No storage service is required for this session demo. A live Vercel deployment has not yet been performed.

## Checks

Install requirements-dev.txt and run `python -m unittest test_session test_resilience -v`. Tests cover stateless API routing, visitor isolation, no saved project files, upload limits, batch confirmation, ambiguous metrics, both formats, restrictions, editing invalidation, provider failure and source matching. The shared deterministic checks can also be run with the selected test_workflow unit tests. That older file's HTTP test assumes a running local server.

## Provisional / limits

One-Pager remains provisional. CTA remains a placeholder until approved messaging is supplied. The original case-study PDF is not included; the sanitised editorial guide is used. The real model can still make errors; validation and human review remain necessary. Unavailable AI checks prevent approval. Free provider quotas may require retrying. Uploads are limited to 2.8 MB and readable text; scanned PDFs require OCR before uploading. Hosted deployment must receive its final smoke test after publishing.

## Writing update

The applied writing brief preserves the observed section purposes, narrative sequence, business voice, paragraph development, length guidance and presentation. The original five-example PDF is never loaded or supplied to inference. Both formats use the same confirmed facts and approved plan. With a model configured, fictional examples now use the same AI writer and reviewer as uploads; without a key, the unchanged fictional intake has a curated full narrative and honestly unavailable AI checks.

Read story presents the complete narrative. Edit sections exposes source links, section rewriting and revision controls. A rewrite requests only that section with the surrounding draft as context. Edits and rewrites invalidate prior validation. Deterministic metric checks permit natural prose but preserve each linked metric's value, unit, period, qualifier and comparison. Missing evidence links and unsupported verbal fractions block validation. Writing checks flag repeated sentences and compressed sections; model-assisted review checks nonnumeric claims and business writing quality. Fictional material always remains sample-only, including after automated checks pass.

Run the regression suite: `python -m unittest test_session test_resilience test_writing test_workflow.Workflow.test_both_formats_and_integrity test_workflow.Workflow.test_references_and_exclusions test_workflow.Workflow.test_missing_story -v`. These tests do not spend inference quota. Live model tests use fictional data only. Free-provider rate limits or outages may require retrying; a writing-quality test is not a guarantee that every intake will produce an approved draft.

## Optional-review regression checks

Run `python -m unittest test_transparent_review test_session test_resilience test_writing test_workflow.Workflow.test_both_formats_and_integrity test_workflow.Workflow.test_references_and_exclusions test_workflow.Workflow.test_missing_story -v`.

Checks include continuation with flagged facts/missing labels, incomplete metric exclusion, semantic category aliases, metric outcome vs baseline/target distinction, source-only fallback, offline partial sample continuation, placeholder editing in both formats and unchanged approval safeguards. No inference quota is consumed by these automated tests. Browser checks use the fictional sample; deployed inference depends on the configured provider.


### Structured intake reading
PDFs use pdfplumber to preserve table rows, cells and reading order; Word files retain paragraphs and table question/answer relationships. Groq receives structured source blocks and extracts complete answers into six intake groups, retaining exact passages and metric details. Word fragments and unmatched claims are discarded. Failed AI extraction retains the readable source and offers Retry extraction; it never substitutes raw lines for facts. Supporting-evidence checkboxes have been removed from the normal story-focus flow.

This uses free open-source libraries and the configured inference provider. No Docling service or paid OCR is required. Scanned/image-only PDFs are explicitly rejected because OCR is not implemented. Groq free-tier quotas and latency still apply. The original file is processed temporarily; only structured text and session state are returned, avoiding a base64 file in every later request. Retry uses the already-read document.

Run the regression tests with `python -m unittest test_document_reading test_transparent_review test_session test_resilience test_writing -v`. Real provider writing quality must also be assessed using a completed, permitted intake; mocked tests cannot establish that quality.


### AI-independent structured forms
Recognisable questions and section headings are mapped locally before any model call. The mapper retains completed table cells, joins answer continuations across pages, keeps original passages/locations, and excludes template hints and empty answers. Each of the six intake groups has named fields. AI extraction remains a clearly labelled recovery path for unstructured documents only; normal structured upload and Retry consume no inference quota. Drafting and semantic validation still require the configured model. Targets, multi-value results and missing measurement periods are flagged rather than silently treated as verified results.

Run `python -m unittest test_intake_mapping test_document_reading test_transparent_review test_session test_resilience test_writing -v`. Optional real-intake regression uses environment variable REAL_INTAKE_TEST pointing to a permitted local file; client material is not bundled, seeded into demo data, or sent to a provider by this regression. Model drafting is mocked in automated regression, so live prose quality remains a separate assessment.
