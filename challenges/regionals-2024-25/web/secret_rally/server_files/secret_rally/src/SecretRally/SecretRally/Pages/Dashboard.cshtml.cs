using System.Security.Cryptography;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;
using SecretRally.Database;
using SecretRally.Models;

namespace SecretRally.Pages;

[Authorize]
public class DashboardModel : PageModel
{
    private readonly ILogger<DashboardModel> _logger;
    private readonly SecretRallyDbContext _dbContext;

    public DashboardModel(ILogger<DashboardModel> logger,
        SecretRallyDbContext dbContext)
    {
        _logger = logger;
        _dbContext = dbContext;
    }

    public async Task<IActionResult> OnGet()
    {
        Rallies = await _dbContext.Rallies.ToListAsync();

        AttendeeEntranceCode = RandomNumberGenerator.GetHexString(16);

        return Page();
    }

    public IList<Rally> Rallies { get; set; } = new List<Rally>();


    [BindProperty]
    public string AttendeeName { get; set; }

    [BindProperty]
    public string AttendeeEntranceCode { get; set; }

    [BindProperty]
    public int RallyId { get; set; }

    public async Task<IActionResult> OnPostAsync()
    {
        if (!ModelState.IsValid)
        {
            TempData["ErrorMessage"] = "Attendee information is required.";
            return RedirectToPage();
        }

        const string ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-, ";

        if (AttendeeName.Any(c => !ALLOWED_CHARS.Contains(c)))
        {
            TempData["ErrorMessage"] = "Invalid characters in attendee name.";
            return RedirectToPage();
        }

        var rowCount = await _dbContext.Database.ExecuteSqlRawAsync($"INSERT INTO \"Attendees\" (\"Name\", \"EntranceCode\", \"RallyId\") VALUES ('{AttendeeName}', '{AttendeeEntranceCode}', {RallyId})");

        if (rowCount == 0)
        {
            TempData["ErrorMessage"] = "Failed to add attendee.";
            return RedirectToPage();
        }

        TempData["SuccessMessage"] = "Attendee added successfully.";
        return RedirectToPage();
    }
}