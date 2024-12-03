using Microsoft.AspNetCore.Authentication;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using SecretRally.Database;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text.Encodings.Web;

namespace SecretRally.Auth
{
    public class JwtAuthHandler : AuthenticationHandler<JwtAuthOptions>
    {
        public const string SchemeName = "JwtAuthScheme";

        private readonly TokenHandler _tokenHandler;
        private readonly SecretRallyDbContext _context;
        
        public JwtAuthHandler(
            TokenHandler tokenHandler,
            SecretRallyDbContext context,
            IOptionsMonitor<JwtAuthOptions> options,
            ILoggerFactory logger,
            UrlEncoder encoder) : base(options, logger, encoder)
        {
            _tokenHandler = tokenHandler;
            _context = context;
        }

        protected override Task HandleChallengeAsync(AuthenticationProperties properties)
        {
            Response.Redirect("/Login");

            return Task.CompletedTask;
        }

        protected override async Task<AuthenticateResult> HandleAuthenticateAsync()
        {
            if (!Request.Cookies.TryGetValue("token", out var token))
            {
                return AuthenticateResult.Fail("Cookie token was not found");
            }

            string username;

            try
            {
                var securityToken = new JwtSecurityTokenHandler().ReadJwtToken(token);
                username = securityToken.Claims.First(c => c.Type == ClaimTypes.NameIdentifier).Value;
            }
            catch
            {
                return AuthenticateResult.Fail("Invalid token");
            }

            var user = await _context.Users.FirstOrDefaultAsync(u => u.Username == username);

            if (user == null)
            {
                return AuthenticateResult.Fail("User not found");
            }

            var claims = new[]
            {
                new Claim(ClaimTypes.NameIdentifier, user.Username)
            };

            var identity = new ClaimsIdentity(claims, Scheme.Name);

            var ticket = new AuthenticationTicket(new ClaimsPrincipal(identity), Scheme.Name);

            return AuthenticateResult.Success(ticket);
        }
    }
}
