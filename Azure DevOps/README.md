# Private NuGet on Azure DevOps

Use this when an app needs a package from a private Azure Artifacts feed. AWS SDK packages from nuget.org do not need this. A private package that loads AWS Secrets Manager does.

The feed can live in a different collection from the build. The pipeline reaches it through a service connection.

## Push a package

1. Raise `<Version>` in the library `.csproj` before packing. Use `yyyy.MM.dd.N`. Raise `N` for another push on the same day. Azure Artifacts rejects a version that was already pushed.

2. From the repo root, pack and push to the feed's NuGet v2 URL. `--api-key az` is a placeholder. The push uses your Windows login.

```powershell
dotnet pack "Your.Project\Your.Project.csproj" -c Release -o nupkg
dotnet nuget push "nupkg\Your.Project.yyyy.MM.dd.N.nupkg" --source "https://your-server/your-collection/_packaging/your-feed-id/nuget/v2/" --api-key az
```

3. Point the app at that same version:

```xml
<PackageReference Include="Your.Project" Version="yyyy.MM.dd.N" />
```

4. If restore cannot see the new version, clear the NuGet HTTP cache and restore again:

```powershell
dotnet nuget locals http-cache --clear
dotnet restore "Your.App\Your.App.csproj"
```

5. Delete the local `nupkg` folder so it is not committed.

Pack uses Release. `Debug.WriteLine` is removed from that build. Use `Trace.WriteLine` for messages that should show while debugging.

## Service connection

The build agent does not use your Windows login. Give the pipeline a personal access token.

1. In the collection that owns the feed, open User settings, Personal access tokens, New Token.
2. For a build that only restores, scope it to Packaging (Read). A token that also pushes needs Packaging (Read & write).
3. In the project that builds the app, open Project settings, Service connections, New service connection, NuGet.
4. Choose External Azure DevOps Server.
5. Set the feed URL to the NuGet v3 index, ending in `index.json`.
6. Paste the token into Personal Access Token. Name the connection after the feed. Save it and allow pipelines to use it.

The dots already shown in that box are the hidden token. Replace them when you paste a new one, or the old token stays.

## Authenticate task

`dotnet restore` on the agent does not send the token by itself. Add a task that does.

1. Edit the build pipeline.
2. Add NuGet authenticate and place it immediately before the Restore task.
3. In Service connection credentials for feeds outside this organization, select the service connection from the previous section.
4. Leave Reinstall the credential provider unchecked.
5. Save the pipeline.

That task sets `VSS_NUGET_EXTERNAL_FEED_ENDPOINTS` for the job. The agent's NuGet credential plugin then sends the token. Without this task, restore of a package that is not already cached fails with `NU1301` `401`.

The repo `nuget.config` still lists the private feed next to nuget.org.

## Restore and build

The existing .NET Core tasks stay after NuGet authenticate:

1. NuGet authenticate
2. Restore, command `restore`, using `nuget.config`
3. Build, command `build`

Restore downloads the private package, including one that wraps AWS Secrets Manager. Build compiles the app. `AWSSDK.*` packages from nuget.org restore without the private feed. A `PackageReference` to the private package does not.
