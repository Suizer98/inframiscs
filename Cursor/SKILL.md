---
name: ado-inhouse-mcp
description: Use the ado-inhouse Azure DevOps MCP (on-prem collections, git, work items, pipelines). Use when the user asks about ADO, Azure DevOps Server, collections, repos, work items, or ado-inhouse tools. After a successful query, append reusable company or project facts to this file.
---

# ado-inhouse MCP

Skill path after you copy it into Cursor:

- `~/.cursor/skills/ado-inhouse-mcp/SKILL.md`
- Windows: `%USERPROFILE%\.cursor\skills\ado-inhouse-mcp\SKILL.md`

In this repo the template lives at `.cursor/skills/ado-inhouse-mcp/SKILL.md`. Agents should update the copy Cursor loaded (usually the personal one).

Namespace: whatever Cursor shows for the `ado-inhouse` MCP (or `azure-devops-mcp`). Auth is already on the connection. Do not ask for a PAT.

This file has two parts. How to use the tools is the initial skill; do not replace it with one-off answers. Company and project notes starts empty and is filled in by agents after they have queried the MCP.

## How to use the tools

1. `core_set_collection` with the collection the user named (or one already listed under notes). Collection is per MCP session. A new chat does not inherit it. stdio shares one collection for the process.
2. Unknown collection: `core_list_collections` with `collectionNameFilter`. Exact one match also sets the session.
3. Projects: `core_list_projects`. Repos: `repo_repository` `action=list` per project. There is no collection-wide repo list.
4. Files: `repo_file` `list_directory` to find paths, then `get_content`. Prefer matching folder and file names over full-text search.
5. Search is not a Git API. `search_code`, `search_wiki`, and `search_workitem` need the Azure DevOps Server **Search / Code Search** extension (plus its indexer, usually Elasticsearch). If that plugin is missing or unhealthy, those calls 500/404. Do not lead with them unless notes say search works on this host, or the ADO web search box works.
6. `repo_search_commits` is different: this MCP always posts to `https://almsearch.dev.azure.com/...`, so it 404s on-prem even when Code Search is installed. Do not use it against Azure DevOps Server.
7. Pull requests use the Git API (`repo_pull_request` list/get/list_by_commits, `repo_pull_request_thread`). That works without Search. There is no `git log` tool; commit SHAs come from `repo_branch` tips or PR payloads. File at a SHA: `repo_file` `get_content` with `version` and `versionType: Commit`.
8. If identities fail with REST 7.2 out of range, the server max is 7.0. If `get_content` throws `stream.setEncoding is not a function`, use listings only (older NTLM builds returned a fake HTTP message instead of a stream).
9. You only have MCP tools plus this workspace. You cannot run `git` against the ADO server. Write tools exist; do not use them unless the user asked to change ADO.

Inspect tool schemas with the MCP descriptor before calling an unfamiliar tool.

## Maintain company and project notes

After you answer, if this session produced a reusable fact about this company's ADO (collection names, where a class of repos or jobs lives, which tools fail), append it under Company and project notes in the same turn. Do not wait to be asked.

Write: stable layout (project / repo / folder for a class of work), host quirks, working tool fallbacks.

Do not write: secrets, tokens, passwords, one-off IDs, today's counts, full layer or file dumps, guessed names.

Newest first. One bullet per fact. Rewrite a bullet if it was wrong. Delete it if it went stale. Keep the section short.

## Company and project notes

- To be filled up by agent
