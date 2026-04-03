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

# ... your analysis code here ...

# After writing any output file:
# print(f"FILE:{output_path}", file=sys.stderr)
```

## How to run

Write the script to a temp file and run it directly:

```bash
uv run "$TMPDIR/bevcost_custom.py"        # macOS / Linux
uv run "$env:TEMP\bevcost_custom.py"      # Windows (PowerShell)
```

`uv` reads the inline metadata and installs dependencies automatically — no `--with` flags needed.

## FILE: Protocol — Required for All Generated Files

Any script that writes files for the user **MUST emit `FILE:<path>` on stderr** for each generated file. This is how the file-handling workflow (see `file-handling.md`) detects output files for display, save, and open.

```python
# After writing a file:
print(f"FILE:{output_path}", file=sys.stderr)
```

After running any script, **always check stderr for `FILE:` lines** and follow `file-handling.md` if any are present.

## Rules

- **Always** include the `# /// script` metadata block with all required dependencies.
- **Always** add the `sys.path.insert` line to access the bundled bevcost library.
- **Always** emit `FILE:<path>` on stderr for every file written for the user.
- Only list dependencies the script actually imports — don't add extras speculatively.
- Write scripts to the OS temp directory (`$TMPDIR` on macOS/Linux, `$env:TEMP` on Windows) unless the user requests a persistent location.
- Make scripts executable with the shebang line when saving to a persistent location (macOS/Linux only).
