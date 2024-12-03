using Microsoft.EntityFrameworkCore;
using SecretRally.Models;

namespace SecretRally.Database
{
    public class SecretRallyDbContext : DbContext
    {
        public SecretRallyDbContext(DbContextOptions<SecretRallyDbContext> options) : base(options)
        {
        }

        public DbSet<User> Users => Set<User>();

        public DbSet<Rally> Rallies => Set<Rally>();

        public DbSet<Attendee> Attendees => Set<Attendee>();

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Rally>()
                .HasMany(r => r.Attendees)
                .WithOne(a => a.Rally)
                .HasForeignKey(a => a.RallyId)
                .IsRequired();
            
            modelBuilder.Entity<Attendee>()
                .HasIndex(a => a.EntranceCode)
                .IsUnique();
        }
    }
}
