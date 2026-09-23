import json
import sys
import zipfile
from datetime import date
from pathlib import Path

root = Path(__file__).resolve().parent
configPath = root / "config.json"


def toolboxExecuteEntries(sourceAtbx):
    with zipfile.ZipFile(sourceAtbx, "r") as sourceZip:
        return sorted(
            name
            for name in sourceZip.namelist()
            if name.endswith("tool.script.execute.py")
        )


def loadConfig():
    config = json.loads(configPath.read_text(encoding="utf-8"))
    sourceAtbx = root / config["source_atbx"]
    outputAtbx = root / config["output_atbx"]
    stamp = date.today().strftime("%Y_%m_%d")
    outputAtbx = outputAtbx.with_name(f"{outputAtbx.stem}_{stamp}{outputAtbx.suffix}")

    scriptPaths = [root / relPath for relPath in config["scripts"]]
    entries = toolboxExecuteEntries(sourceAtbx)

    if len(entries) != len(scriptPaths):
        print(
            f"Toolbox has {len(entries)} execute.py entries but config lists {len(scriptPaths)} scripts.",
            file=sys.stderr,
        )
        sys.exit(1)

    replacements = dict(zip(entries, scriptPaths))
    return sourceAtbx, outputAtbx, replacements


def readScript(path):
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data


def copyEntry(info):
    entry = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
    entry.compress_type = info.compress_type
    entry.external_attr = info.external_attr
    entry.create_system = info.create_system
    return entry


def buildToolbox():
    sourceAtbx, outputAtbx, replacements = loadConfig()
    missingFiles = [path for path in replacements.values() if not path.is_file()]
    if missingFiles:
        for path in missingFiles:
            print(f"Missing script: {path}", file=sys.stderr)
        sys.exit(1)

    outputAtbx.parent.mkdir(parents=True, exist_ok=True)
    for oldAtbx in outputAtbx.parent.glob("*.atbx"):
        oldAtbx.unlink()
    replaced = []

    with zipfile.ZipFile(sourceAtbx, "r") as sourceZip, zipfile.ZipFile(outputAtbx, "w") as outputZip:
        names = set(sourceZip.namelist())
        missingEntries = [name for name in replacements if name not in names]
        if missingEntries:
            for name in missingEntries:
                print(f"Missing toolbox entry: {name}", file=sys.stderr)
            sys.exit(1)

        for info in sourceZip.infolist():
            data = sourceZip.read(info.filename)
            if info.filename in replacements:
                data = readScript(replacements[info.filename])
                replaced.append(info.filename)
            outputZip.writestr(copyEntry(info), data)

    print(f"Wrote {outputAtbx}")
    for entry in replaced:
        script = replacements[entry]
        print(f"Replaced {script.relative_to(root)}")


if __name__ == "__main__":
    buildToolbox()
