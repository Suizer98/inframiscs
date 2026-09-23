# Sample release tasks (PowerShell + Extract Files)

Example release pipeline steps for publishing an `.atbx` build artifact to the SMB/IIS Artifacts share documented in [SMB/README.md](../../SMB/README.md).

Use mocked host and paths from that doc (`100.16.xx.101`, `network-share-1`). Replace with your server when deploying.

Pipeline variables (secret where noted):

| Variable | Example | Notes |
| -------- | ------- | ----- |
| `ShareAccount` | `network-share-1\Administrator` | SMB writer account |
| `SharePassword` | (secret) | Password for `ShareAccount` |

Task order:

1. [01-setup-variables.ps1](./01-setup-variables.ps1) — find `.atbx`, set output variables
2. [02-extract-files.md](./02-extract-files.md) — built-in Extract Files task
3. [03-copy-to-artifacts.ps1](./03-copy-to-artifacts.ps1) — copy to `Releases\data`
4. [04-print-download-paths.ps1](./04-print-download-paths.ps1) — log SMB and HTTP paths

HTTP downloads may require a signed-in browser or IIS MIME for `.atbx`; see SMB README troubleshooting.
