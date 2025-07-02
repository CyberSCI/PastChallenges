using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace VoterRegistryApi.Models
{
    public class PollingStation
    {
        [Key]
        public int Id { get; set; }

        [Required]
        [JsonPropertyName("street_number")]
        public int StreetNumber { get; set; }

        [Required]
        [JsonPropertyName("street_name")]
        public string StreetName { get; set; }

        [Required]
        [JsonPropertyName("city")]
        public string City { get; set; }

        [Required]
        [JsonPropertyName("state")]
        public string State { get; set; }

        [Required]
        [JsonPropertyName("postal_code")]
        public string PostalCode { get; set; }

        [JsonPropertyName("streets")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public List<Street> Streets { get; set; } = new();

        [JsonPropertyName("advisories")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public List<Advisory> Advisories { get; set; } = new();
    }
}
