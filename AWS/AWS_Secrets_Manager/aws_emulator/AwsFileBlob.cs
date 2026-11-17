namespace Aws.SecretsManager
{
    // For blobs that an external process must open by path (.pfx, .cer, ...).
    // Restore writes the AWS bytes to the same relative path appsettings.json already points to,
    // so existing code that opens that path needs no changes.
    internal static class AwsFileBlob
    {
        public static void Restore(string relativePath, byte[] content)
        {
            var fullPath = Path.Combine(AppContext.BaseDirectory, relativePath);
            var directory = Path.GetDirectoryName(fullPath);
            if (!string.IsNullOrEmpty(directory))
                Directory.CreateDirectory(directory);

            File.WriteAllBytes(fullPath, content);
        }
    }
}
