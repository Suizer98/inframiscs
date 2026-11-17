namespace Aws.SecretsManager
{
    public static class AwsStreamBlob
    {
        private static readonly Dictionary<string, byte[]> files = new(StringComparer.OrdinalIgnoreCase);
        private static bool useMemory;

        public static void EnableMemory()
        {
            useMemory = true;
        }

        public static void Save(string relativePath, byte[] content)
        {
            files[Normalize(relativePath)] = content;
        }

        public static Stream Open(string relativePath)
        {
            if (!useMemory)
                return File.OpenRead(relativePath);

            if (!files.TryGetValue(Normalize(relativePath), out var content))
                throw new InvalidOperationException($"AwsStreamBlob has no in-memory secret for {relativePath}");

            return new MemoryStream(content, writable: false);
        }

        private static string Normalize(string path)
        {
            return path.Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar);
        }
    }
}
