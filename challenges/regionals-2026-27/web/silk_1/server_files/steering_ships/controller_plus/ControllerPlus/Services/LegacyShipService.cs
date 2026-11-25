using System.Net;
using System.Net.Http.Json;
using ControllerPlus.Models;

namespace ControllerPlus.Services;

public sealed class LegacyShipService(HttpClient httpClient) : IShipService
{
    public async Task<IReadOnlyList<ShipResponse>> GetAllAsync(CancellationToken cancellationToken)
    {
        using var response = await httpClient.GetAsync("api/ships", cancellationToken);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadFromJsonAsync<List<ShipResponse>>(cancellationToken)
            ?? throw new InvalidDataException("The legacy API returned an empty ship list response.");
    }

    public async Task<ShipResponse?> GetByIdAsync(Guid id, CancellationToken cancellationToken)
    {
        using var response = await httpClient.GetAsync($"api/ships/{id}", cancellationToken);
        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }

        response.EnsureSuccessStatusCode();

        return await response.Content.ReadFromJsonAsync<ShipResponse>(cancellationToken)
            ?? throw new InvalidDataException("The legacy API returned an empty ship response.");
    }
}