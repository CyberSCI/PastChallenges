using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Text.Json.Serialization;

namespace VoterRegistryApi.Models
{
    public class Advisory
    {
        [Key]
        [JsonPropertyName("id")]
        public int Id { get; set; }

        [Required]
        [JsonPropertyName("message")]
        public string Message { get; set; } = string.Empty;

        [Required]
        [JsonPropertyName("created_at")]
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        [JsonPropertyName("url")]
        public string? Url { get; set; } = null;

        [Required]
        [JsonIgnore]
        public int PollingStationId { get; set; }

        [Required]
        [ForeignKey("PollingStationId")]
        [JsonPropertyName("polling_station")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public PollingStation? PollingStation { get; set; }
    }
}