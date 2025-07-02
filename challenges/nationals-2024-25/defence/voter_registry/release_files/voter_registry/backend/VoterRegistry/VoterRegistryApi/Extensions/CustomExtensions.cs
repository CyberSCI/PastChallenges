using System.IdentityModel.Tokens.Jwt;
using Microsoft.IdentityModel.JsonWebTokens;
using Microsoft.IdentityModel.Tokens;

namespace VoterRegistryApi.Extensions
{
    public static class CustomExtensions
    {
        public static void AddAuthentication(this WebApplicationBuilder builder)
        {
            builder.Services.AddAuthentication("Bearer")
                .AddJwtBearer("Bearer", options =>
                {
                    options.Audience = builder.Configuration["Authentication:Audience"];

                    // Trust self-signed certificate
                    options.TokenValidationParameters = new TokenValidationParameters
                    {
                        ValidateIssuer = false,
                        SignatureValidator = (token, _) => new JsonWebToken(token),
                    };
                    options.BackchannelHttpHandler = new HttpClientHandler
                    {
                        ServerCertificateCustomValidationCallback = (message, cert, chain, errors) => true
                    };
                });

            builder.Services.AddAuthorization();
        }
    }
}