# Custom Scripts — uv Inline Dependencies (PEP 723)

When a skill needs to generate a custom Python script on the fly, use **uv inline dependency metadata** (PEP 723) so the script is self-contained and reproducible.

## Template

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "matplotlib",
#     "numpy",
#     "numpy_financial",
# ]
# ///

import sys, os
sys.path.insert(0, os.path.join(r'${CLAUDE_PLUGIN_ROOT}', 'lib'))

# ... your code here ...
```

## How to run

Write the script to a temp file and run it directly:

```bash
uv run "$TMPDIR/bevcost_custom.py"        # macOS / Linux
uv run "$env:TEMP\bevcost_custom.py"      # Windows (PowerShell)
```

`uv` reads the inline metadata and installs dependencies automatically — no `--with` flags needed.

## Rules

- **Always** include the `# /// script` metadata block with all required dependencies.
- **Always** add the `sys.path.insert` line to access the bundled bevcost library.
- Only list dependencies the script actually imports — don't add extras speculatively.
- Write scripts to the OS temp directory (`$TMPDIR` on macOS/Linux, `$env:TEMP` on Windows) unless the user requests a persistent location.
- Make scripts executable with the shebang line when saving to a persistent location (macOS/Linux only).
