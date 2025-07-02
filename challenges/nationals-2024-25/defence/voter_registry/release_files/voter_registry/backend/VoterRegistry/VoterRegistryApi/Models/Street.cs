using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Text.Json.Serialization;

namespace VoterRegistryApi.Models
{
    public class Street
    {
        [Key]
        [JsonIgnore]
        public int Id { get; set; }

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

        [JsonIgnore]
        public int PollingStationId { get; set; }

        [ForeignKey("PollingStationId")]
        [JsonPropertyName("polling_station")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public PollingStation PollingStation { get; set; }
    }
}
