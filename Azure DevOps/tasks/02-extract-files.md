# Extract files (built-in task)

Add this task after **Setup variables**.

| Field | Value |
| ----- | ----- |
| Task | Extract files |
| Task version | 1.* |
| Display name | Extract files |
| Archive file patterns | `$(ArtifactPath)` |
| Destination folder | `$(NewArtifactDirectory)` |
| Clean destination folder before extracting | (your choice) |
| Overwrite existing files | enabled |
| Path to 7z utility | (default) |

No script body — configure in the release pipeline UI or YAML equivalent.
