using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Text.Json.Serialization;
using Microsoft.EntityFrameworkCore;

namespace VoterRegistryApi.Models
{
    [Index(nameof(PhotoIdNumber), IsUnique = true)]
    [Index(nameof(RegistrationNumber), IsUnique = true)]
    public class RegisteredPerson
    {
        [Key]
        public int Id { get; set; }

        [Required]
        [JsonPropertyName("first_name")]
        public string FirstName { get; set; }

        [Required]
        [JsonPropertyName("last_name")]
        public string LastName { get; set; }

        [Required]
        [JsonPropertyName("birthdate")]
        public DateOnly Birthdate { get; set; }

        [Required]
        [JsonPropertyName("photo_id_number")]
        public string PhotoIdNumber { get; set; }

        public int? RegistrationNumber { get; set; } = null;

        public string? RegistrationFile { get; set; } = null;

        public bool RegistrationFileMatchesInfo { get; set; } = false;

        public bool RegistrationFileReviewed { get; set; } = false;

        public bool RegistrationFileApproved { get; set; } = false;

        public string? RegistrationAddressNumber { get; set; } = null;

        public int? RegistrationAddressStreetId { get; set; } = null;

        [ForeignKey("RegistrationAddressStreetId")]
        public Street? RegistrationAddressStreet { get; set; } = null;

        public DateTime? RegistrationDate { get; set; } = null;
    }
}