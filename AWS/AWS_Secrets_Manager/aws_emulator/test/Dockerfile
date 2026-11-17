# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/dotnet/sdk:10.0
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/emulator-python \
    && /opt/emulator-python/bin/pip install --no-cache-dir boto3
ENV PATH="/opt/emulator-python/bin:${PATH}"
WORKDIR /src
COPY . .
RUN sed -i 's/\r$//' test/run-test.sh \
      test/populate-secrets.sh \
      test/configure-feed-auth.sh \
      test/PrepareKms.py \
      test/BlankApiSettings.py \
      test/AddProbeToDeps.py \
    && chmod +x test/run-test.sh \
      test/populate-secrets.sh
RUN --mount=type=secret,id=nuget_token \
    NUGET_PACKAGES=/tmp/nuget-packages \
    sh /src/test/configure-feed-auth.sh \
    && dotnet publish /src/api/MockApi.csproj -c Release -o /app -p:NuGetAudit=false -p:RestoreConfigFile=/tmp/nuget.auth.config \
    && dotnet publish /src/test/SecretsProbe.csproj -c Release -o /tmp/secrets-probe -p:NuGetAudit=false -p:RestoreConfigFile=/tmp/nuget.auth.config \
    && cp /tmp/secrets-probe/SecretsProbe.dll /app/SecretsProbe.dll \
    && python3 /src/test/AddProbeToDeps.py \
    && rm -f /tmp/nuget.auth.config
WORKDIR /app
ENTRYPOINT ["/src/test/run-test.sh"]
