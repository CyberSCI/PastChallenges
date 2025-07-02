using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using VoterRegistryApi.Database;
using VoterRegistryApi.Extensions;
using VoterRegistryApi.Models;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("https://register.valverde.vote")
              .WithExposedHeaders("Content-Disposition")
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.ReferenceHandler = System.Text.Json.Serialization.ReferenceHandler.IgnoreCycles;
    });


builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddDbContext<VoterRegistryDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

builder.AddAuthentication();

var app = builder.Build();

// Apply migrations
using (var scope = app.Services.CreateScope())
{
    var dbContext = scope.ServiceProvider.GetRequiredService<VoterRegistryDbContext>();
    await dbContext.Database.MigrateAsync();

    // Add polling stations data
    if (!await dbContext.PollingStations.AnyAsync())
    {
        var pollingStationsFile = builder.Configuration["PollingStationDataFile"]
            ?? throw new InvalidOperationException("PollingStationDataFile not configured");

        var pollingStationsText = await File.ReadAllTextAsync(pollingStationsFile);

        var pollingStations = JsonSerializer.Deserialize<List<PollingStation>>(pollingStationsText)
            ?? throw new InvalidOperationException("PollingStationDataFile is empty or invalid");

        await dbContext.PollingStations.AddRangeAsync(pollingStations);
        await dbContext.SaveChangesAsync();
    }

    // Add population data
    if (!await dbContext.RegisteredPersons.AnyAsync())
    {
        var populationFile = builder.Configuration["PopulationDataFile"]
            ?? throw new InvalidOperationException("PopulationDataFile not configured");

        var populationText = await File.ReadAllTextAsync(populationFile);

        var registeredPersons = JsonSerializer.Deserialize<List<RegisteredPerson>>(populationText)
            ?? throw new InvalidOperationException("PopulationDataFile is empty or invalid");

        await dbContext.RegisteredPersons.AddRangeAsync(registeredPersons);
        await dbContext.SaveChangesAsync();
    }
}

app.UseCors();

app.UseAuthentication();
app.UseAuthorization();

app.UseSwagger();
app.UseSwaggerUI();

app.MapControllers();

app.Run();
