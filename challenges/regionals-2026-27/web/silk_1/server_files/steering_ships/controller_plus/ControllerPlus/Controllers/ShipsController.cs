using ControllerPlus.Models;
using ControllerPlus.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace ControllerPlus.Controllers;

/// <summary>Provides the authenticated, read-only ship-tracking feed.</summary>
[ApiController]
[Authorize]
[Route("api/ships")]
public sealed class ShipsController(IShipService shipService) : ControllerBase
{
    /// <summary>Returns the current positions for all tracked vessels.</summary>
    [HttpGet]
    [ProducesResponseType(typeof(IReadOnlyList<ShipResponse>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<IReadOnlyList<ShipResponse>>> GetAll(CancellationToken cancellationToken)
    {
        return Ok(await shipService.GetAllAsync(cancellationToken));
    }

    /// <summary>Returns the current position for one tracked vessel.</summary>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(ShipResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ShipResponse>> GetById(Guid id, CancellationToken cancellationToken)
    {
        var ship = await shipService.GetByIdAsync(id, cancellationToken);
        return ship is null ? NotFound() : Ok(ship);
    }
}