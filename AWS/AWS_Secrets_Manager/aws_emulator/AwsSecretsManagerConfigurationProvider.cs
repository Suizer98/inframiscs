using Amazon;
using Amazon.SecretsManager;
using Amazon.SecretsManager.Model;
using Microsoft.Extensions.Configuration;
using System.Diagnostics;
using System.Text;

// https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_ListSecrets.html
// https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_BatchGetSecretValue.html
// https://aws.amazon.com/blogs/modernizing-with-aws/how-to-load-net-configuration-from-aws-secrets-manager/
namespace Aws.SecretsManager
{
    // Load() runs first. The configuration system calls it after Program.cs Add().
    // Load() waits on LoadAsync().
    // LoadAsync() returns immediately when AwsSecretsManager:Enabled is false.
    // Otherwise it calls EnableMemory(), creates the client, then ApplyAsync(), then StartTimer().
    // ApplyAsync() calls FetchSecretsAsync(). Binary blobs are stored there:
    // .pem/.ppk/.key/.asc/.gpg/.pgp/.json go to AwsStreamBlob, everything else goes to AwsFileBlob.
    // ApplyAsync() then writes only the string secrets into Data.
    // The timer later calls RefreshAsync(), which calls ApplyAsync() again.
    // OnReload() runs only on that refresh, and only when at least one string secret came back.
    internal class AwsSecretsManagerConfigurationProvider : ConfigurationProvider
    {
        private readonly IConfiguration configuration;
        private readonly object reloadLock = new();
        private IAmazonSecretsManager? client;
        private Timer? refreshTimer;

        public AwsSecretsManagerConfigurationProvider(IConfiguration configuration)
        {
            this.configuration = configuration;
        }

        public override void Load()
        {
            LoadAsync().ConfigureAwait(false).GetAwaiter().GetResult();
        }

        private async Task LoadAsync()
        {
            var section = configuration.GetSection("AwsSecretsManager");
            if (!section.GetValue<bool>("Enabled"))
                return;

            AwsStreamBlob.EnableMemory();

            client ??= CreateClient(section);
            var secretsClient = client;

            try
            {
                await ApplyAsync(secretsClient, section, reload: false).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                Trace.WriteLine($"AwsSecretsManager load failed: {ex.Message}");
            }

            StartTimer(secretsClient, section);
        }

        private void StartTimer(IAmazonSecretsManager secretsClient, IConfigurationSection section)
        {
            if (refreshTimer != null)
                return;

            var interval = section.GetValue<TimeSpan?>("SecretsTTL") ?? TimeSpan.Zero;
            if (interval <= TimeSpan.Zero)
                return;
            refreshTimer = new Timer(async state =>
            {
                await RefreshAsync(secretsClient, section).ConfigureAwait(false);
            }, null, interval, interval);
        }

        private async Task RefreshAsync(IAmazonSecretsManager secretsClient, IConfigurationSection section)
        {
            try
            {
                await ApplyAsync(secretsClient, section, reload: true).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                Trace.WriteLine($"AwsSecretsManager refresh failed: {ex.Message}");
            }
        }

        private async Task ApplyAsync(IAmazonSecretsManager secretsClient, IConfigurationSection section, bool reload)
        {
            var secrets = await FetchSecretsAsync(secretsClient, section).ConfigureAwait(false);
            if (secrets.Count == 0)
            {
                Trace.WriteLine("AwsSecretsManager connected; loaded 0 secret(s).");
                return;
            }

            lock (reloadLock)
            {
                Data = secrets.ToDictionary(pair => pair.Key, pair => (string?)pair.Value, StringComparer.OrdinalIgnoreCase);
            }

            // If subsequent reloads signal a change, trigger the IConfiguration OnReload
            if (reload)
                OnReload();

            Trace.WriteLine($"AwsSecretsManager loaded {secrets.Count} secret(s).");
        }

        private IAmazonSecretsManager CreateClient(IConfigurationSection section)
        {
            var region = RegionEndpoint.GetBySystemName(section["Region"] ?? "ap-southeast-1");
            var accessKeyId = section["AwsAccessKeyId"];
            var secretAccessKey = section["AwsSecretAccessKey"];
            // Grab easy credentials from appsettings.json for quick DEV testings
            // Use local machine AWS CLI SSO profile login to act as IAM role in DEV environment
            // In GCC+ AWS EC2 instances it will automatically scan for IAM instance role
            if (!string.IsNullOrWhiteSpace(accessKeyId) && !string.IsNullOrWhiteSpace(secretAccessKey))
                return new AmazonSecretsManagerClient(accessKeyId, secretAccessKey, region);

            return new AmazonSecretsManagerClient(region);
        }

        private async Task<Dictionary<string, string>> FetchSecretsAsync(IAmazonSecretsManager secretsClient, IConfigurationSection section)
        {
            var environmentTagKey = section["EnvironmentTagKey"];
            var environmentTagValue = section["EnvironmentTagValue"];
            var applicationTagKey = section["ApplicationTagKey"];
            var applicationTagValue = section["ApplicationTagValue"];

            // ListSecrets can filter with multiple tag pairs
            // BatchGetSecretValue looks up correct tags from ListSecrets response
            var names = new List<string>();
            string? nextToken = null;
            do
            {
                var response = await secretsClient.ListSecretsAsync(new ListSecretsRequest
                {
                    NextToken = nextToken,
                    Filters =
                    [
                        new Filter { Key = FilterNameStringType.TagKey, Values = [environmentTagKey] },
                        new Filter { Key = FilterNameStringType.TagValue, Values = [environmentTagValue] },
                    ],
                }).ConfigureAwait(false);

                foreach (var secret in response.SecretList ?? [])
                {
                    var tags = (secret.Tags ?? []).ToDictionary(tag => tag.Key, tag => tag.Value);
                    if (applicationTagKey == null
                        || !string.Equals(tags.GetValueOrDefault(applicationTagKey), applicationTagValue, StringComparison.Ordinal))
                        continue;
                    if (!string.IsNullOrEmpty(secret.Name))
                        names.Add(secret.Name);
                }

                nextToken = response.NextToken;
            }
            while (!string.IsNullOrEmpty(nextToken));

            // Aws Secrets Manager does not accept colon in secret name.
            // Names are prefixed with the application tag, for example {ApplicationTagValue}.ConnectionStrings.AuditLogs.
            // BatchGetSecretValue accepts 20 names per call. The prefix is removed, then '.' becomes the IConfiguration ':'.
            var secrets = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            for (var index = 0; index < names.Count; index += 20)
            {
                var batch = names.Skip(index).Take(20).ToList();
                var response = await secretsClient.BatchGetSecretValueAsync(new BatchGetSecretValueRequest
                {
                    SecretIdList = batch,
                }).ConfigureAwait(false);

                foreach (var entry in response.SecretValues ?? [])
                {
                    if (string.IsNullOrEmpty(entry.Name))
                        continue;
                    var secretName = StripApplicationPrefix(entry.Name, applicationTagValue);
                    if (string.IsNullOrEmpty(secretName))
                        continue;
                    if (entry.SecretBinary != null && entry.SecretBinary.Length > 0)
                    {
                        SaveSecretFile(secretName, entry.SecretBinary);
                        continue;
                    }
                    if (entry.SecretString == null)
                        continue;
                    if (AwsBlobConstants.StreamableExtensions.Contains(Path.GetExtension(secretName)))
                    {
                        AwsStreamBlob.Save(SecretNameToRelativePath(secretName), Encoding.UTF8.GetBytes(entry.SecretString));
                        continue;
                    }
                    secrets[secretName.Replace('.', ':')] = entry.SecretString;
                }

                foreach (var error in response.Errors ?? [])
                    Trace.WriteLine($"AwsSecretsManager failed to read {error.SecretId}: {error.Message}");
            }

            return secrets;
        }

        private static string StripApplicationPrefix(string secretName, string? applicationTagValue)
        {
            if (string.IsNullOrEmpty(applicationTagValue))
                return secretName;

            var prefix = applicationTagValue + ".";
            if (secretName.StartsWith(prefix, StringComparison.Ordinal))
                return secretName[prefix.Length..];

            return secretName;
        }

        // Upload scripts name a file from its appsettings path: folder.file.ext or folder.subfolder.file.ext.
        private static void SaveSecretFile(string secretName, Stream secretBinary)
        {
            var relativePath = SecretNameToRelativePath(secretName);

            if (secretBinary.CanSeek)
                secretBinary.Position = 0;
            using var buffer = new MemoryStream();
            secretBinary.CopyTo(buffer);
            var content = buffer.ToArray();

            if (AwsBlobConstants.StreamableExtensions.Contains(Path.GetExtension(relativePath)))
                AwsStreamBlob.Save(relativePath, content);
            else
                AwsFileBlob.Restore(relativePath, content);
        }

        private static string SecretNameToRelativePath(string secretName)
        {
            var extension = Path.GetExtension(secretName);
            var stem = extension.Length == 0 ? secretName : secretName[..^extension.Length];
            var firstDot = stem.IndexOf('.');
            if (firstDot <= 0)
                return secretName;

            var secondDot = stem.IndexOf('.', firstDot + 1);
            if (secondDot < 0)
                return Path.Combine(secretName[..firstDot], secretName[(firstDot + 1)..]);

            return Path.Combine(secretName[..firstDot], secretName[(firstDot + 1)..secondDot], secretName[(secondDot + 1)..]);
        }
    }
}
