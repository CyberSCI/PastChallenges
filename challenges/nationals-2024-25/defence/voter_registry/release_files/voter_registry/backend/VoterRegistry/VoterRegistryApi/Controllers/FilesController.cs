using Microsoft.AspNetCore.Mvc;
using VoterRegistryApi.Database;

namespace VoterRegistryApi.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class FilesController : ControllerBase
    {
        private readonly ILogger<FilesController> _logger;
        private readonly VoterRegistryDbContext _dbContext;
        private readonly IConfiguration _configuration;

        public FilesController(
            ILogger<FilesController> logger,
            VoterRegistryDbContext dbContext,
            IConfiguration configuration
            )
        {
            _logger = logger;
            _dbContext = dbContext;
            _configuration = configuration;
        }

        [HttpGet("")]
        public async Task<IActionResult> GetFile([FromQuery] string path)
        {
            var fullPath = Path.Combine(_configuration["RegistrationFilePath"] ?? ".", path);

            if (!System.IO.File.Exists(fullPath))
            {
                return NotFound("File not found.");
            }

            var extension = Path.GetExtension(fullPath).ToLowerInvariant();
            var fileMimeType = extension switch
            {
                ".pdf" => "application/pdf",
                ".jpg" => "image/jpeg",
                ".jpeg" => "image/jpeg",
                ".png" => "image/png",
                _ => "application/octet-stream"
            };

            var fileBytes = await System.IO.File.ReadAllBytesAsync(fullPath);

            return File(fileBytes, fileMimeType, Path.GetFileName(fullPath));
        }
    }
}