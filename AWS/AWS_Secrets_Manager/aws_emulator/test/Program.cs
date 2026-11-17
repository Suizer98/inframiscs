using Aws.SecretsManager;
using Microsoft.Extensions.Configuration;

const string awsSettingsSection = "AwsSecretsManager";

var settingsPath = args.Length > 0 ? args[0] : "/work/appsettings.json";
var builder = new ConfigurationBuilder();
builder.AddJsonFile(settingsPath, optional: false);
var bootstrap = builder.Build();

var awsBootstrap = new ConfigurationBuilder()
    .AddInMemoryCollection(bootstrap.GetSection(awsSettingsSection).AsEnumerable())
    .Build();
var secretsBuilder = new ConfigurationBuilder();
secretsBuilder.Add(new AwsSecretsManagerConfigurationSource(awsBootstrap));
var configuration = secretsBuilder.Build();

var entries = configuration.AsEnumerable()
    .Where(pair => pair.Value != null)
    .OrderBy(pair => pair.Key, StringComparer.Ordinal)
    .ToList();

if (entries.Count == 0)
{
    Console.WriteLine("RETRIEVE_MISSING");
    Environment.ExitCode = 1;
    return;
}

foreach (var pair in entries)
    Console.WriteLine($"{pair.Key}={pair.Value}");
