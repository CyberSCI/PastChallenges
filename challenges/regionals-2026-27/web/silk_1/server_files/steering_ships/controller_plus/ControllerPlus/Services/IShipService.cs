using ControllerPlus.Models;

namespace ControllerPlus.Services;

/// <summary>Reads ship positions from the legacy controller API.</summary>
public interface IShipService
{
    /// <summary>Returns the current position of every vessel.</summary>
    Task<IReadOnlyList<ShipResponse>> GetAllAsync(CancellationToken cancellationToken);

    /// <summary>Returns the current position of a vessel, if it exists.</summary>
    Task<ShipResponse?> GetByIdAsync(Guid id, CancellationToken cancellationToken);
}