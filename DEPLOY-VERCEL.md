# Session demo on Vercel

This version is prepared for Vercel, but has not been deployed or verified on a live Vercel account.

## Deploy

1. Upload the contents of this folder to a Git repository. Do not upload `.env`, `data/`, or the original reference PDFs. The clean `story-studio-vercel.zip` deliverable already excludes secrets and client files.
2. Import that repository into Vercel. Set the project Root Directory to the folder containing `vercel.json` if it is nested.
3. Use Framework Preset **Other**. There is no frontend build command. Output Directory is `web`; `vercel.json` supplies that configuration.
4. Add environment variables in Vercel's project settings:
   - `OPENAI_API_KEY`: your Groq key (the generic name is intentional).
   - `MODEL_BASE_URL`: `https://api.groq.com/openai/v1`.
   - `MODEL_NAME`: `openai/gpt-oss-120b`, or a compatible JSON-capable model available to your account.
   - `SESSION_ONLY`: `1`.
5. Deploy. Enable Fluid Compute if it is not enabled; the API is configured for a maximum of 120 seconds, subject to your plan's limit.
6. Check `/api/state`, then run the fictional example through confirmation, focus, both formats, editing and validation. Test a permitted fictional PDF/DOCX with the model key configured. Check the Vercel logs if the deployment reports import or configuration errors.

## What visitors get

- Each browser tab has its own session state; there is no shared “latest project.”
- Refresh restores the current tab's work through `sessionStorage`. Closing the tab ends normal access to that session. Browser session restoration may restore tabs; use a fresh tab/private window for a fresh visitor demo.
- The original upload is read in memory for processing. The server does not write uploaded files, projects or revisions to persistent disk in session mode.
- Copy/download the draft before ending the session. The Save control retains the current version in the browser session; it is not a durable project save.
- Intake text and selected references are sent to the configured inference provider when real AI processing is enabled.

## Limits

- Maximum PDF/DOCX upload: 2.8 MB. The file is base64-encoded for processing; this leaves room under Vercel's 4.5 MB request limit. Later requests include source text and current state, not the original binary.
- Maximum extracted intake text: 120,000 characters. Very large projects or many references may exceed the session request limit; download the draft and begin a fresh session.
- Recent draft history is capped at 12 revisions to bound request size.
- Groq free quotas can cause a request to fail or leave validation unavailable. The app reports this honestly and lets the user retry. No automatic human approval is implied.
- There is no login or access-control layer in this demo. Use Vercel deployment protection for a limited review audience where appropriate; everyone able to use real drafting consumes the configured provider quota.

## Local run and tests

Run `python server.py` and open the printed localhost address. Session mode is enabled by default; existing local files are not loaded into visitors' sessions. Local-only persistent mode remains available with `SESSION_ONLY=0`; Vercel always forces session mode.

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest test_session test_resilience -v
```

The tests exercise the Vercel HTTP adapter locally, session isolation, no project disk writes, summary confirmation, exception handling, upload limits, provenance fallbacks and both formats. Local tests do not substitute for the final live deployment smoke test.

Configuration follows Vercel's official Python runtime and function limits documentation:
- https://vercel.com/docs/functions/runtimes/python
- https://vercel.com/docs/functions/limitations
- https://vercel.com/docs/project-configuration/vercel-json

The deployment package includes the applied writing brief and offline fictional narrative. Keep these files beside server.py. A configured model writes both real and fictional intakes; the offline sample remains clearly labelled when no key is present.
