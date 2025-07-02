namespace VoterRegistryApi.Dtos
{
    public class PollingStationLookupDto
    {
        public string? StreetNumber { get; set; }

        public string? StreetName { get; set; }

        public string? City { get; set; }

        public string? State { get; set; }

        public string? PostalCode { get; set; }
    }
}