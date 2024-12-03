using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;
using SecretRally.Auth;
using SecretRally.Database;

namespace SecretRally.Pages;

[AllowAnonymous]
public class LoginModel : PageModel
{
    private readonly ILogger<LoginModel> _logger;
    private readonly SecretRallyDbContext _dbContext;
    private readonly TokenHandler _tokenHandler;

    [BindProperty]
    public string Username { get; set; }

    [BindProperty]
    public string Password { get; set; }

    public LoginModel(ILogger<LoginModel> logger,
        SecretRallyDbContext dbContext,
        TokenHandler tokenHandler)
    {
        _logger = logger;
        _dbContext = dbContext;
        _tokenHandler = tokenHandler;
    }

    public IActionResult OnGet()
    {
        if (User.Identity?.IsAuthenticated ?? false)
        {
            return RedirectToPage("./Dashboard");
        }

        return Page();
    }

    public async Task<IActionResult> OnPostAsync()
    {
        if (!ModelState.IsValid)
        {
            return RedirectToPage();
        }

        var user = await _dbContext.Users.FirstOrDefaultAsync(u => u.Username == Username && u.Password == Password);

        if (user == null)
        {
            TempData["ErrorMessage"] = "Invalid username or password.";

            return RedirectToPage();
        }

        var token = _tokenHandler.CreateToken(user);

        Response.Cookies.Append("token", token);

        return RedirectToPage("./Dashboard");
    }
}

