# Mock Secrets Manager light test

Run these commands from this folder. The fixture is `test/appsettings.json`. Passwords in the fixture are fake. The application tag is `MOCKAPP` and the KMS alias is `alias/mock-kms`. Emulator telemetry is off.

The emulator keeps secrets in memory. `down` removes the containers and that memory.

Leave the emulator running between the populate step and the light step. `aws-secrets-manager-light-test` prints the values the loader read.

```
docker compose build aws-emulator aws-secrets-manager-populate aws-secrets-manager-light-test
docker compose run --rm aws-secrets-manager-populate
docker compose up --no-deps --abort-on-container-exit --exit-code-from aws-secrets-manager-light-test aws-secrets-manager-light-test
docker compose down -v --remove-orphans
```

`aws-secrets-manager-populate` creates the KMS alias and uploads the mock secrets. `aws-secrets-manager-light-test` prints the values loaded from the emulator. The last command removes every container from this compose file, including when an earlier command failed.
