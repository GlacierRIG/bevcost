# Generated File Handling — Display, Save, and Open

Use these instructions whenever a bevcost script generates user-facing files. Generated files are indicated by `FILE:` lines on stderr.

## 1. Display files

Parse all `FILE:<path>` lines from stderr.

- **Image files** (`.png`, `.jpg`, `.jpeg`, `.svg`): Read each file and display it inline.
- **All other files**: List them by filename and file size. Do not attempt to display.

## 2. Offer to save files

After displaying, prompt the user to save files to a persistent location. Use `AskUserQuestion` with OS-appropriate common directories. Detect the OS from the platform info in your environment context (`darwin` = macOS, `linux` = Linux, `win32` = Windows).

Offer these options:

| OS      | Option 1                                   | Option 2                                     | Option 3                                     |
| ------- | ------------------------------------------ | -------------------------------------------- | -------------------------------------------- |
| macOS   | `~/Desktop/bevcost-output/`                | `~/Documents/bevcost-output/`                | `~/Downloads/bevcost-output/`                |
| Linux   | `~/Desktop/bevcost-output/`                | `~/Documents/bevcost-output/`                | `~/Downloads/bevcost-output/`                |
| Windows | `$env:USERPROFILE\Desktop\bevcost-output\` | `$env:USERPROFILE\Documents\bevcost-output\` | `$env:USERPROFILE\Downloads\bevcost-output\` |

Always include a **"Don't save"** option (files remain in their temp location).

If the user chooses to save:

- Create the `bevcost-output/` subfolder if it doesn't exist:
  - macOS/Linux: `mkdir -p <path>`
  - Windows (PowerShell): `New-Item -ItemType Directory -Force -Path <path>`
- Copy all generated files to that folder
- Report the saved file paths

## 3. Offer to open files

After saving (or if user chose "Don't save"), ask with `AskUserQuestion` whether to open the files in the OS default viewer:

- **macOS**: `open <path>`
- **Linux**: `xdg-open <path>`
- **Windows (PowerShell)**: `Start-Process <path>`

Options: **"Open"** and **"No thanks"**.
