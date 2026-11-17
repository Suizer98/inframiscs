namespace Aws.SecretsManager
{
    internal static class AwsBlobConstants
    {
        public const string PemExtension = ".pem";
        public const string PpkExtension = ".ppk";
        public const string KeyExtension = ".key";
        public const string AscExtension = ".asc";
        public const string GpgExtension = ".gpg";
        public const string PgpExtension = ".pgp";
        public const string JsonExtension = ".json";

        public static readonly HashSet<string> StreamableExtensions = new(StringComparer.OrdinalIgnoreCase)
        {
            PemExtension,
            PpkExtension,
            KeyExtension,
            AscExtension,
            GpgExtension,
            PgpExtension,
            JsonExtension
        };
    }
}
