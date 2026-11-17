import json
import sys

SOURCE_PATH = sys.argv[1]
TARGET_PATH = sys.argv[2]
SECRET_KEY_WORDS = ("password", "passphrase", "jwtsigningkey", "thumbprint")


def blank(node, path):
    if isinstance(node, dict):
        return {key: blank(value, path + [key]) for key, value in node.items()}
    if isinstance(node, list):
        return [blank(value, path + [str(index)]) for index, value in enumerate(node)]
    if path and path[0] == "ConnectionStrings" and isinstance(node, str):
        return ""
    if path and isinstance(node, str) and any(word in path[-1].lower() for word in SECRET_KEY_WORDS):
        return ""
    return node


with open(SOURCE_PATH, encoding="utf-8") as source_file:
    settings = json.load(source_file)

blanked = blank(settings, [])
if blanked["ConnectionStrings"]["Development"] != "":
    raise SystemExit("api connection string was not cleared")

with open(TARGET_PATH, "w", encoding="utf-8") as target_file:
    json.dump(blanked, target_file)

print('Cleared all uploaded secrets to empty or ""')
