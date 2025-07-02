using Microsoft.EntityFrameworkCore;
using VoterRegistryApi.Models;

namespace VoterRegistryApi.Database
{
    public class VoterRegistryDbContext : DbContext
    {
        public VoterRegistryDbContext(DbContextOptions<VoterRegistryDbContext> options) : base(options)
        {
        }

        public DbSet<PollingStation> PollingStations { get; set; }

        public DbSet<Street> Streets { get; set; }

        public DbSet<Advisory> Advisories { get; set; }
        
        public DbSet<RegisteredPerson> RegisteredPersons { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.HasCollation("case_insensitive", locale: "en-u-ks-primary", provider: "icu", deterministic: false);

            modelBuilder.Entity<Street>()
                .Property(s => s.StreetName)
                .UseCollation("case_insensitive");

            modelBuilder.Entity<Street>()
                .Property(s => s.City)
                .UseCollation("case_insensitive");

            modelBuilder.Entity<Street>()
                .Property(s => s.State)
                .UseCollation("case_insensitive");

            modelBuilder.Entity<RegisteredPerson>()
                .Property(rp => rp.FirstName)
                .UseCollation("case_insensitive");

            modelBuilder.Entity<RegisteredPerson>()
                .Property(rp => rp.LastName)
                .UseCollation("case_insensitive");

            modelBuilder.Entity<Street>()
                .Property(s => s.PostalCode)
                .UseCollation("case_insensitive");

            modelBuilder.Entity<PollingStation>()
                .HasMany(p => p.Streets)
                .WithOne(s => s.PollingStation)
                .HasForeignKey(s => s.PollingStationId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<PollingStation>()
                .HasMany(p => p.Advisories)
                .WithOne(a => a.PollingStation)
                .HasForeignKey(a => a.PollingStationId)
                .OnDelete(DeleteBehavior.Cascade);
        }
    }
}