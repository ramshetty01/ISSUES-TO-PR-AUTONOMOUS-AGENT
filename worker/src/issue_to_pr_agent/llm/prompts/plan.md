Given the issue and the repository context, produce a short plan to fix it.

Return JSON:
```json
{
  "summary": "one sentence describing the fix",
  "files_to_edit": ["path/one.py"],
  "steps": ["step 1", "step 2"],
  "risk": "low|medium|high"
}
```

Keep the plan minimal — only the files that must change.
Choose at least one concrete target file and one concrete edit path, not just a diagnosis.
