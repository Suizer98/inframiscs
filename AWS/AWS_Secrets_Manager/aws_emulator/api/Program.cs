using Aws.SecretsManager;

var builder = WebApplication.CreateBuilder(args);

if (builder.Configuration.GetValue<bool>("AwsSecretsManager:Enabled"))
    ((IConfigurationBuilder)builder.Configuration).Add(new AwsSecretsManagerConfigurationSource(builder.Configuration));

var app = builder.Build();
app.Run();
