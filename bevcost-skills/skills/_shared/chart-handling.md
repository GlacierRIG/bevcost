# Chart Handling — Display, Save, and Open

Use these instructions whenever a bevcost script generates charts. Charts are indicated by `CHART:` lines on stderr.

## 1. Display charts

Parse all `CHART:<path>` lines from stderr. Read each PNG file and display it inline.

## 2. Offer to save charts

After displaying, prompt the user to save charts to a persistent location. Use `AskUserQuestion` with OS-appropriate common directories. Detect the OS from the platform info in your environment context (`darwin` = macOS, `linux` = Linux, `win32` = Windows).

Offer these options:

| OS      | Option 1                                   | Option 2                                     | Option 3                                     |
| ------- | ------------------------------------------ | -------------------------------------------- | -------------------------------------------- |
| macOS   | `~/Desktop/bevcost-charts/`                | `~/Documents/bevcost-charts/`                | `~/Downloads/bevcost-charts/`                |
| Linux   | `~/Desktop/bevcost-charts/`                | `~/Documents/bevcost-charts/`                | `~/Downloads/bevcost-charts/`                |
| Windows | `$env:USERPROFILE\Desktop\bevcost-charts\` | `$env:USERPROFILE\Documents\bevcost-charts\` | `$env:USERPROFILE\Downloads\bevcost-charts\` |

Always include a **"Don't save"** option (charts remain in their temp location).

If the user chooses to save:

- Create the `bevcost-charts/` subfolder if it doesn't exist:
  - macOS/Linux: `mkdir -p <path>`
  - Windows (PowerShell): `New-Item -ItemType Directory -Force -Path <path>`
- Copy all generated chart PNGs to that folder
- Report the saved file paths

## 3. Offer to open charts

After saving (or if user chose "Don't save"), ask with `AskUserQuestion` whether to open the charts in the OS default viewer:

- **macOS**: `open <path>`
- **Linux**: `xdg-open <path>`
- **Windows (PowerShell)**: `Start-Process <path>`

Options: **"Open in viewer"** and **"No thanks"**.
