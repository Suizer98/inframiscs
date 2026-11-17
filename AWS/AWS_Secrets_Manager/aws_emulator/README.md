# Mock Secrets Manager emulator

Run these commands from this folder. The fixture is `test/appsettings.json`. Passwords in the fixture are fake. The application tag is `MOCKAPP` and the KMS alias is `alias/mock-kms`. Emulator telemetry is off.

The emulator keeps secrets in memory. `down` removes the containers and that memory.

## Light

`test/Dockerfile.test` builds this image. Leave the emulator running between the populate step and the light step. `aws-secrets-manager-light-test` prints the values the loader read. This image restores packages from nuget.org only.

```
docker compose build aws-emulator aws-secrets-manager-populate aws-secrets-manager-light-test
docker compose run --rm aws-secrets-manager-populate
docker compose up --no-deps --abort-on-container-exit --exit-code-from aws-secrets-manager-light-test aws-secrets-manager-light-test
docker compose down -v --remove-orphans
```

## API

`test/Dockerfile` builds this image. It publishes a small API, publishes `SecretsProbe`, and copies that dll next to the API. `AddProbeToDeps.py` registers the probe in the API deps file. At startup the API adds `AwsSecretsManagerConfigurationSource` when `AwsSecretsManager:Enabled` is true. The probe then prints secret values from `IConfiguration`. The API settings file inside the container has empty secret values, so a non-empty value came from the emulator.

`test/configure-feed-auth.sh` runs before publish. An empty token file skips feed auth. A token file is JSON `{"username":"...","password":"..."}`, or one raw token line. The script writes that password onto the `Mock.Artifacts` source. That source stays disabled in `nuget.config`, so a local build restores from nuget.org and does not call the mock feed. Remove the disabled entry and set the source URL before using a real feed. The pipeline writes the token from the `Mock.Artifacts` service connection and passes it as `NUGET_TOKEN_FILE`. `azure-pipelines.yml` expects this folder at `aws_emulator` from the repository root.

Leave the emulator running between the populate step and the API step.

```
docker compose build aws-emulator aws-secrets-manager-populate aws-secrets-manager-test
docker compose run --rm aws-secrets-manager-populate
docker compose up --no-deps --abort-on-container-exit --exit-code-from aws-secrets-manager-test aws-secrets-manager-test
docker compose down -v --remove-orphans
```

`aws-secrets-manager-populate` creates the KMS alias and uploads the mock secrets. `aws-secrets-manager-test` prints the values the API loaded. The last command removes every container from this compose file, including when an earlier command failed.
