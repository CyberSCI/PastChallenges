namespace SecretRally.Models
{
    public class Rally
    {
        public int Id { get; set; }

        public string Name { get; set; }

        public string Location { get; set; }

        public string Description { get; set; }

        public bool Hidden { get; set; }

        public virtual ICollection<Attendee> Attendees { get; set; }
    }
}
