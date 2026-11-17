#!/bin/sh
set -eu
cp /src/nuget.config /tmp/nuget.auth.config
if [ ! -s /run/secrets/nuget_token ]; then
  exit 0
fi
secret=$(tr -d '\r' < /run/secrets/nuget_token)
username=az
case "$secret" in
  "{"*)
    token=$(printf '%s' "$secret" | sed -n 's/.*"password"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    parsedUser=$(printf '%s' "$secret" | sed -n 's/.*"username"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    if [ -n "$parsedUser" ]; then
      username=$parsedUser
    fi
    ;;
  *)
    token=$(printf '%s' "$secret" | tr -d '\n')
    ;;
esac
if [ -z "$token" ]; then
  echo "NuGet token secret did not contain a password"
  exit 1
fi
echo "NuGet token length: ${#token}"
dotnet nuget update source Mock.Artifacts --username "$username" --password "$token" --store-password-in-clear-text --valid-authentication-types basic --configfile /tmp/nuget.auth.config
unset token secret parsedUser
