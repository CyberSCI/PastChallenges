using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SecretRally.Models
{
    public class Attendee
    {
        public int Id { get; set; }

        [Required]
        public string Name { get; set; }

        [Required] 
        public string EntranceCode { get; set; }
        
        public int RallyId { get; set; }

        public virtual Rally Rally { get; set; }
    }
}
