The test suite failed after your change. Given the failing test output and the current diff, diagnose the cause and propose the next edit.

Return JSON:
```json
{
  "diagnosis": "what went wrong",
  "file": "path/to/fix.py",
  "fix_summary": "what to change"
}
```

If the failure is a pre-existing flaky test unrelated to your change, say so in the diagnosis.
