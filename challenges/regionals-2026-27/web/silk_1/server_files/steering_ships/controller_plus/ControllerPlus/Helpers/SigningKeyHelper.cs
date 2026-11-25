using System.Text.Json;
using Microsoft.IdentityModel.Tokens;

namespace ControllerPlus.Helpers;

internal static class SigningKeyHelper
{
    internal static IEnumerable<SecurityKey> ResolveIssuerSigningKeys(
        string token,
        SecurityToken securityToken,
        string keyId,
        TokenValidationParameters validationParameters)
    {
        using var client = new HttpClient();
        var metadata = client.GetStringAsync(
            $"{securityToken.Issuer.TrimEnd('/')}/.well-known/openid-configuration")
            .GetAwaiter().GetResult();
        var jwksUri = JsonDocument.Parse(metadata).RootElement
            .GetProperty("jwks_uri").GetString()!;
        var jwks = client.GetStringAsync(jwksUri).GetAwaiter().GetResult();
        return new JsonWebKeySet(jwks).GetSigningKeys();
    }
}