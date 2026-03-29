---
name: process-debug
description: Run the tube2txt pipeline end-to-end in debug mode against a URL or slug, printing every on_progress event to trace pipeline failures. Pass a YouTube URL as the argument.
---

Run a debug pipeline execution for `$ARGUMENTS`:

1. Activate the venv: `source .venv/bin/activate`

2. Run the pipeline with verbose progress tracing:
```python
python3 -c "
from tube2txt import process_video
import traceback
try:
    process_video(
        'debug-test',
        '$ARGUMENTS',
        on_progress=lambda t, s, m: print(f'[{t}] {s}: {m}', flush=True)
    )
    print('Pipeline completed successfully.')
except Exception as e:
    print(f'Pipeline FAILED: {e}')
    traceback.print_exc()
"
```

3. Report:
   - Which step last printed before failure (`[type] step: message`)
   - The exact exception and traceback
   - Whether `projects/debug-test/` was created and what files are present (`ls projects/debug-test/ 2>/dev/null`)

4. Clean up after: `rm -rf projects/debug-test/`
