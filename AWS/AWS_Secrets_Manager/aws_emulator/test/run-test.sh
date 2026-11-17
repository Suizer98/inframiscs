#!/bin/sh
set -eu
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE AWS_DEFAULT_PROFILE \
  AWS_WEB_IDENTITY_TOKEN_FILE AWS_ROLE_ARN AWS_ROLE_SESSION_NAME \
  AWS_CONTAINER_CREDENTIALS_RELATIVE_URI AWS_CONTAINER_CREDENTIALS_FULL_URI \
  AWS_CONTAINER_AUTHORIZATION_TOKEN
python3 /src/test/BlankApiSettings.py /work/appsettings.json /app/appsettings.json
echo "Spinning up API"
export ASPNETCORE_URLS=http://127.0.0.1:8080
export DOTNET_ROLL_FORWARD=Major
export ASPNETCORE_HOSTINGSTARTUPASSEMBLIES=SecretsProbe
dotnet /app/MockApi.dll > /tmp/api.log 2>&1 &
api_pid=$!
i=0
while [ "$i" -lt 90 ]; do
  if grep -q "^LOADED_SECRETS_END$" /tmp/api.log; then
    secrets=$(sed -n '/^LOADED_SECRETS_BEGIN$/,/^LOADED_SECRETS_END$/p' /tmp/api.log | sed '1d;$d')
    if [ -z "$secrets" ]; then
      echo API_FAILED
      tail -n 40 /tmp/api.log
      exit 1
    fi
    echo "Logging out secrets from IConfiguration for those retrieved from AWS Emulator Secrets Manager"
    printf '%s\n' "$secrets"
    kill "$api_pid" || true
    wait "$api_pid" || true
    exit 0
  fi
  if ! kill -0 "$api_pid" 2>/dev/null; then
    echo API_FAILED
    tail -n 40 /tmp/api.log
    exit 1
  fi
  i=$((i + 1))
  sleep 1
done
echo API_TIMEOUT
exit 1
