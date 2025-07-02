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
    public class PollingStationController : ControllerBase
    {
        private readonly ILogger<PollingStationController> _logger;
        private readonly VoterRegistryDbContext _dbContext;

        public PollingStationController(
            ILogger<PollingStationController> logger,
            VoterRegistryDbContext dbContext
            )
        {
            _logger = logger;
            _dbContext = dbContext;
        }

        [HttpGet("")]
        public async Task<IActionResult> GetAll(int offset = 0, int limit = 100)
        {
            if (offset < 0)
            {
                return BadRequest("Offset must be non-negative.");
            }

            if (limit <= 0 || limit > 2500)
            {
                return BadRequest("Limit must be between 1 and 2500.");
            }

            var totalCount = await _dbContext.PollingStations.CountAsync();

            var pollingStations = await _dbContext.PollingStations
                .Include(ps => ps.Streets)
                .Include(ps => ps.Advisories)
                .Skip(offset)
                .Take(limit)
                .ToListAsync();

            return Ok(new PagedResult<PollingStation>(
                pollingStations.Count,
                offset,
                totalCount,
                pollingStations
            ));
        }

        [HttpGet("{id}")]
        public async Task<IActionResult> GetById(int id)
        {
            var pollingStation = await _dbContext.PollingStations
                .Include(ps => ps.Streets)
                .Include(ps => ps.Advisories)
                .FirstOrDefaultAsync(ps => ps.Id == id);

            if (pollingStation == null)
            {
                return NotFound();
            }

            return Ok(pollingStation);
        }

        [HttpPost("lookup")]
        public async Task<IActionResult> Lookup([FromBody] PollingStationLookupDto lookupDto)
        {
            if (lookupDto == null || string.IsNullOrWhiteSpace(lookupDto.StreetNumber) || string.IsNullOrWhiteSpace(lookupDto.StreetName) || string.IsNullOrWhiteSpace(lookupDto.City) || string.IsNullOrWhiteSpace(lookupDto.State) || string.IsNullOrWhiteSpace(lookupDto.PostalCode))
            {
                return BadRequest(new { Error = "Invalid lookup parameters. All fields are required." });
            }

            var street = await _dbContext.Streets
                .Include(street => street.PollingStation)
                .ThenInclude(ps => ps.Advisories)
                .Where(street => street.StreetName == lookupDto.StreetName &&
                                 street.City == lookupDto.City &&
                                 street.State == lookupDto.State &&
                                 street.PostalCode == lookupDto.PostalCode)
                .FirstOrDefaultAsync();

            if (street == null)
            {
                return NotFound(new { Error = "We could not find this address in our database. Please make sure you typed the correct address." });
            }

            var pollingStation = street?.PollingStation;

            if (pollingStation == null)
            {
                return NotFound(new { Error = "Polling station not found for the given address." });
            }

            return Ok(pollingStation);
        }

        [HttpPost("{id}/advisory")]
        public async Task<IActionResult> AddAdvisory(int id, [FromBody] AdvisoryDto advisory)
        {
            if (advisory == null || string.IsNullOrWhiteSpace(advisory.Message))
            {
                return BadRequest("Invalid advisory data.");
            }

            var pollingStation = await _dbContext.PollingStations.FindAsync(id);
            if (pollingStation == null)
            {
                return NotFound("Polling station not found.");
            }

            pollingStation.Advisories.Add(new Advisory
            {
                Message = advisory.Message,
                Url = advisory.Url,
                CreatedAt = DateTime.UtcNow,
                PollingStationId = pollingStation.Id
            });

            await _dbContext.SaveChangesAsync();

            return CreatedAtAction(nameof(GetById), new { id = pollingStation.Id }, pollingStation);
        }

        [Authorize]
        [HttpDelete("{id}/advisory/{advisoryId}")]
        public async Task<IActionResult> DeleteAdvisory(int id, int advisoryId)
        {
            var pollingStation = await _dbContext.PollingStations
                .Include(ps => ps.Advisories)
                .FirstOrDefaultAsync(ps => ps.Id == id);

            if (pollingStation == null)
            {
                return NotFound("Polling station not found.");
            }

            var advisory = pollingStation.Advisories.FirstOrDefault(a => a.Id == advisoryId);
            if (advisory == null)
            {
                return NotFound("Advisory not found.");
            }

            _dbContext.Advisories.Remove(advisory);
            await _dbContext.SaveChangesAsync();

            return NoContent();
        }
    }
}