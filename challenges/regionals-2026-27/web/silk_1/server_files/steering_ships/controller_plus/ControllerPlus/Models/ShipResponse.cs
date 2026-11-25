namespace ControllerPlus.Models;

/// <summary>Represents a vessel position returned by the tracking API.</summary>
/// <param name="Id">Stable identifier used by the tracking console.</param>
/// <param name="Name">Vessel name.</param>
/// <param name="CallSign">Radio call sign.</param>
/// <param name="Mmsi">Maritime Mobile Service Identity.</param>
/// <param name="VesselType">Vessel class.</param>
/// <param name="Destination">Reported destination.</param>
/// <param name="Status">Current operational status.</param>
/// <param name="Latitude">Current latitude in decimal degrees.</param>
/// <param name="Longitude">Current longitude in decimal degrees.</param>
/// <param name="SpeedKnots">Current speed over ground in knots.</param>
/// <param name="Heading">Current heading in degrees.</param>
/// <param name="CargoPercent">Approximate cargo load percentage.</param>
/// <param name="UpdatedAt">Time the ship last reported the position.</param>
public sealed record ShipResponse(
    Guid Id,
    string Name,
    string CallSign,
    string Mmsi,
    string VesselType,
    string Destination,
    string Status,
    double Latitude,
    double Longitude,
    double SpeedKnots,
    double Heading,
    int CargoPercent,
    DateTimeOffset UpdatedAt);