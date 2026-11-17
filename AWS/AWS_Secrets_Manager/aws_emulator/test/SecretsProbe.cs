using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

[assembly: HostingStartup(typeof(SecretsProbe))]

public class SecretsProbe : IHostingStartup
{
    public void Configure(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            services.AddSingleton<IStartupFilter, SecretsStartupFilter>();
        });
    }
}

public class SecretsStartupFilter : IStartupFilter
{
    static readonly string[] SecretKeyWords = ["password", "passphrase", "jwtsigningkey", "thumbprint"];
    static bool printed;
    readonly IConfiguration configuration;

    public SecretsStartupFilter(IConfiguration configuration)
    {
        this.configuration = configuration;
    }

    public Action<IApplicationBuilder> Configure(Action<IApplicationBuilder> next)
    {
        if (!printed)
        {
            printed = true;
            Console.WriteLine("LOADED_SECRETS_BEGIN");
            foreach (var pair in configuration.AsEnumerable().Where(pair => pair.Value != null).OrderBy(pair => pair.Key, StringComparer.Ordinal))
            {
                if (IsSecret(pair.Key))
                    Console.WriteLine($"{pair.Key}={pair.Value}");
            }

            Console.WriteLine("LOADED_SECRETS_END");
        }

        return next;
    }

    static bool IsSecret(string key)
    {
        if (key.StartsWith("ConnectionStrings:", StringComparison.OrdinalIgnoreCase))
            return true;

        var leaf = key.Contains(':') ? key[(key.LastIndexOf(':') + 1)..] : key;
        return SecretKeyWords.Any(word => leaf.Contains(word, StringComparison.OrdinalIgnoreCase));
    }
}
