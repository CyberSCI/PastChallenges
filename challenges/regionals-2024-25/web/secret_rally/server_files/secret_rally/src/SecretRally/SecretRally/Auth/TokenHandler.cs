using Microsoft.IdentityModel.Tokens;
using SecretRally.Models;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;

namespace SecretRally.Auth
{
    public class TokenHandler
    {
        private readonly ILogger<TokenHandler> _logger;
        private readonly IConfiguration _configuration;

        private readonly JwtSecurityTokenHandler _tokenHandler;
        private readonly TokenValidationParameters _validationParameters;
        private readonly byte[] _signingKey;

        public TokenHandler(ILogger<TokenHandler> logger,
            IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;

            var signingKey = _configuration["Jwt:Key"];

            if (string.IsNullOrEmpty(signingKey))
            {
                signingKey = RandomNumberGenerator.GetHexString(32);
            }

            _signingKey = Encoding.UTF8.GetBytes(signingKey);

            _tokenHandler = new();
            _validationParameters = new()
            {
                ValidateIssuer = false,
                ValidateAudience = false,
                IssuerSigningKey = new SymmetricSecurityKey(_signingKey)
            };
        }

        public string CreateToken(User user)
        {
            // Create token with user ID
            var token = new JwtSecurityToken(
                claims: new[]
                {
                    new Claim(ClaimTypes.NameIdentifier, user.Username)
                },
                expires: DateTime.UtcNow.AddHours(1),
                signingCredentials: new SigningCredentials(
                    new SymmetricSecurityKey(_signingKey),
                    SecurityAlgorithms.HmacSha256)
            );

            return _tokenHandler.WriteToken(token);
        }
        
        public bool ValidateToken(string token, out string username)
        {
            username = string.Empty;

            try
            {
                var claimsPrincipal = _tokenHandler.ValidateToken(token, _validationParameters, out var validatedToken);

                var usernameClaim = claimsPrincipal.FindFirst(ClaimTypes.NameIdentifier);

                if (usernameClaim == null)
                {
                    return false;
                }

                username = usernameClaim.Value;

                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to validate token.");

                return false;
            }
        }
    }
}
