using Microsoft.Extensions.Configuration;

namespace Aws.SecretsManager
{
    public class AwsSecretsManagerConfigurationSource : IConfigurationSource
    {
        public IConfiguration Configuration { get; }

        public AwsSecretsManagerConfigurationSource(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfigurationProvider Build(IConfigurationBuilder builder)
        {
            return new AwsSecretsManagerConfigurationProvider(Configuration);
        }
    }
}
