import json

DEPS_PATH = "/app/MockApi.deps.json"
PROBE_KEY = "SecretsProbe/1.0.0"
PROBE_DLL = "SecretsProbe.dll"

with open(DEPS_PATH, encoding="utf-8") as deps_file:
    deps = json.load(deps_file)

runtime = deps["runtimeTarget"]["name"]
deps["targets"].setdefault(runtime, {})
deps["targets"][runtime][PROBE_KEY] = {"runtime": {PROBE_DLL: {}}}
deps["libraries"][PROBE_KEY] = {"type": "project", "serviceable": False, "sha512": ""}

with open(DEPS_PATH, "w", encoding="utf-8") as deps_file:
    json.dump(deps, deps_file)
