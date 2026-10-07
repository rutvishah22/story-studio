# Story Studio — session demo

One PDF/DOCX intake → compact fact summary → Story focus → Case Study or One-Pager → validation → human review.

## Run locally

Requires Python 3.10+. Run `python -m pip install -r requirements.txt`, copy `.env.example` to `.env`, and configure the provider variables. Start `python server.py` and open its printed address. The bundled workspace Python already has the runtime dependencies; `start.ps1` uses it when available.

The frontend keeps state in browser session storage. Refresh restores the tab's work; use a new tab/private window for an independent session. Server-side projects and uploads are not persisted in session mode. Copy/download draft text before closing the tab. API credentials stay on the server.

## Fact review

The default view shows a four-part story summary, results under an expandable panel, and the number of restrictions excluded. Individual fact cards appear only for missing information, ambiguous metrics, contradictions flagged by extraction, or manual-source verification. All evidence and restrictions remain available under “View all facts.” One explicit summary confirmation confirms the clear permitted facts; unresolved exceptions stay excluded.

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
