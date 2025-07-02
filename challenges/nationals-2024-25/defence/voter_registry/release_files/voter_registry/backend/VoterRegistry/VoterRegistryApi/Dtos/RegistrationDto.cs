namespace VoterRegistryApi.Dtos
{
    public class RegistrationDto
    {
        public string? FirstName { get; set; }

        public string? LastName { get; set; }

        public DateOnly? Birthdate { get; set; }

        public string? PhotoIdNumber { get; set; }

        public string? StreetNumber { get; set; }

        public string? StreetName { get; set; }

        public string? City { get; set; }

        public string? State { get; set; }

        public string? PostalCode { get; set; }

        public IFormFile? AddressProof { get; set; }
    }
}