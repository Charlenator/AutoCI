# CV generator (test data)

Workflow for producing the synthetic `.docx` CVs that feed the inbound pipeline test.

## Step 1 — Generate JSON batches

Open Claude.ai (or ChatGPT) and paste the prompt from this conversation's chat. Run it as many times as you need to reach 20-50 CVs total. Each run gives you 8 CVs.

Save each run's JSON output to this folder as `cvs_batch_1.json`, `cvs_batch_2.json`, etc.

## Step 2 — Convert to .docx

```bash
cd dev-tools/cv_generator
pip install python-docx     # one-time, if not already installed
python make_cvs.py *.json
```

Output `.docx` files land in `dev-tools/cv_generator/output/`.

## Step 3 — Send through inbound pipeline

Once the inbound pipeline is wired (Sprint B4-B5), there will be two ways to ingest:

1. **Email each `.docx` as an attachment** to the Resend-watched address (live demo path).
2. **POST to `/simulate-inbound`** with the file attached (dev/test path, no email roundtrip).

I'll update this README when those endpoints are live.

## Schema reminder

Each CV JSON object should match this shape (see prompt for full spec):

```json
{
  "filename": "...",
  "name": "...",
  "email": "...",
  "phone": "...",
  "location": "...",
  "role_target": "Senior Java Developer | Customer Service Associate | HR Specialist",
  "years_experience": 7,
  "summary": "...",
  "skills": ["..."],
  "experience": [{"company": "...", "title": "...", "start_year": ..., "end_year": ..., "highlights": ["..."]}],
  "education": [{"degree": "...", "institution": "...", "year": ...}],
  "current_salary_zar": 920000,
  "expected_salary_zar": 1100000
}
```

The `make_cvs.py` script tolerates missing fields — it only writes the sections that have data, which is what we want for the "missing field flagging" demo.
