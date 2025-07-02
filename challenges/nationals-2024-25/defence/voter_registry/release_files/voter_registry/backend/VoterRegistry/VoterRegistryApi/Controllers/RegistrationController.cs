using System.Diagnostics;
using System.Security.Cryptography;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using VoterRegistryApi.Database;
using VoterRegistryApi.Dtos;
using VoterRegistryApi.Models;

namespace VoterRegistryApi.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class RegistrationController : ControllerBase
    {
        private readonly ILogger<RegistrationController> _logger;
        private readonly VoterRegistryDbContext _dbContext;
        private readonly IConfiguration _configuration;

        public RegistrationController(
            ILogger<RegistrationController> logger,
            VoterRegistryDbContext dbContext,
            IConfiguration configuration
            )
        {
            _logger = logger;
            _dbContext = dbContext;
            _configuration = configuration;
        }

        [HttpPost("")]
        public async Task<IActionResult> Post([FromForm] RegistrationDto registrationDto)
        {
            if (registrationDto == null
                || string.IsNullOrWhiteSpace(registrationDto.FirstName)
                || string.IsNullOrWhiteSpace(registrationDto.LastName)
                || string.IsNullOrWhiteSpace(registrationDto.PhotoIdNumber)
                || string.IsNullOrWhiteSpace(registrationDto.StreetNumber)
                || string.IsNullOrWhiteSpace(registrationDto.StreetName)
                || string.IsNullOrWhiteSpace(registrationDto.City)
                || string.IsNullOrWhiteSpace(registrationDto.State)
                || string.IsNullOrWhiteSpace(registrationDto.PostalCode)
                || registrationDto.Birthdate == null
                || registrationDto.AddressProof == null)
            {
                return BadRequest("Invalid registration data.");
            }

            var person = await _dbContext.RegisteredPersons
                .FirstOrDefaultAsync(p => p.PhotoIdNumber == registrationDto.PhotoIdNumber
                    && p.FirstName == registrationDto.FirstName
                    && p.LastName == registrationDto.LastName
                    && p.Birthdate == registrationDto.Birthdate);

            if (person == null)
            {
                return BadRequest(new { Error = "This registration service could not validate your identity. Please make sure you typed your personal information correctly." });
            }

            var address = await _dbContext.Streets
                .Include(s => s.PollingStation)
                .ThenInclude(ps => ps.Advisories)
                .FirstOrDefaultAsync(a => a.StreetName == registrationDto.StreetName
                    && a.City == registrationDto.City
                    && a.State == registrationDto.State
                    && a.PostalCode == registrationDto.PostalCode);

            if (address == null)
            {
                return BadRequest(new { Error = "We could not find this address in our database. Please make sure you typed the correct address." });
            }

            string? fileName = null;
            string? filePath = null;
            try
            {
                fileName = $"{Guid.NewGuid()}_{registrationDto.AddressProof.FileName}";
                filePath = Path.Combine(_configuration.GetValue("RegistrationFilePath", "./"), fileName);
                using (var stream = new FileStream(filePath, FileMode.Create))
                {
                    await registrationDto.AddressProof.CopyToAsync(stream);
                }
            }
            catch { }

            var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = "bash",
                    Arguments = $"-c \"python3 documentscanner.py '{filePath}'\"",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false
                }
            };

            process.Start();
            var output = await process.StandardOutput.ReadToEndAsync();
            var errorOutput = await process.StandardError.ReadToEndAsync();
            process.WaitForExit();

            if (output.Length < 100 || process.ExitCode != 0)
            {
                return BadRequest(new { Error = "An error occurred while processing your registration. Please try again." });
            }

            var personInfo = new[] {
                registrationDto.FirstName,
                registrationDto.LastName,
                registrationDto.StreetNumber,
                registrationDto.StreetName,
                registrationDto.City,
                registrationDto.State
            };

            var outputMatches = personInfo.All(info => !string.IsNullOrEmpty(info) && output.Contains(info, StringComparison.OrdinalIgnoreCase));

            for (var i = 0; i < 5; i++)
            {
                try
                {
                    person.RegistrationFile = fileName;
                    person.RegistrationNumber = RandomNumberGenerator.GetInt32(100_000_000, 1_000_000_000);
                    person.RegistrationFileMatchesInfo = outputMatches;
                    person.RegistrationFileReviewed = false;
                    person.RegistrationFileApproved = false;
                    person.RegistrationAddressNumber = registrationDto.StreetNumber;
                    person.RegistrationAddressStreet = address;
                    person.RegistrationDate = DateTime.UtcNow;
                    _dbContext.Update(person);

                    await _dbContext.SaveChangesAsync();

                    return Ok(new
                    {
                        RegistrationNumber = person.RegistrationNumber.ToString(),
                        address.PollingStation
                    });
                }
                catch (DbUpdateException)
                {
                    continue;
                }
            }

            return BadRequest(new { Error = "An error occurred while processing your registration. Please try again." });
        }

        [Authorize]
        [HttpGet("Files")]
        public async Task<IActionResult> GetFiles(int offset = 0, int limit = 100)
        {
            if (offset < 0)
            {
                return BadRequest("Offset must be non-negative.");
            }

            if (limit <= 0 || limit > 2500)
            {
                return BadRequest("Limit must be between 1 and 2500.");
            }

            var registeredPersons = await _dbContext.RegisteredPersons
                .Include(p => p.RegistrationAddressStreet)
                .Where(p => p.RegistrationFile != null && !p.RegistrationFileReviewed)
                .OrderBy(p => p.RegistrationDate)
                .Skip(offset)
                .Take(limit)
                .ToListAsync();

            var totalCount = await _dbContext.RegisteredPersons
                .CountAsync(p => p.RegistrationFile != null && !p.RegistrationFileReviewed);

            return Ok(new PagedResult<RegisteredPerson>(
                registeredPersons.Count,
                offset,
                totalCount,
                registeredPersons
            ));
        }

        [Authorize]
        [HttpPost("Files/{registrationNumber}")]
        public async Task<IActionResult> ReviewFile(int registrationNumber, [FromBody] ReviewFileDto reviewFileDto)
        {
            var person = await _dbContext.RegisteredPersons
                .FirstOrDefaultAsync(p => p.RegistrationNumber == registrationNumber);

            if (person == null)
            {
                return NotFound("Person not found.");
            }

            if (person.RegistrationFileReviewed)
            {
                return BadRequest("This file has already been reviewed.");
            }

            person.RegistrationFileReviewed = true;
            person.RegistrationFileApproved = reviewFileDto.Approved;

            _dbContext.Update(person);
            await _dbContext.SaveChangesAsync();

            return Ok(new
            {
                Message = reviewFileDto.Approved ? "File approved." : "File rejected.",
                RegistrationNumber = person.RegistrationNumber.ToString()
            });
        }
    }
}