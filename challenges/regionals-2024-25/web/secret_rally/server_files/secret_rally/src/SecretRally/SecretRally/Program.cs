using Microsoft.AspNetCore.Authorization;
using Microsoft.EntityFrameworkCore;
using SecretRally.Auth;
using SecretRally.Database;
using SecretRally.Middleware;
using SecretRally.Models;
using System.Security.Cryptography;

var builder = WebApplication.CreateBuilder(args);

var jsonPath = Environment.GetEnvironmentVariable("SECRET_RALLY_CONFIG_PATH");

if (!string.IsNullOrEmpty(jsonPath))
{
    builder.Configuration.AddJsonFile(jsonPath);
}


builder.Services.AddRazorPages();

builder.Services.AddDbContext<SecretRallyDbContext>(options =>
{
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"));
});

builder.Services
    .AddSingleton<IHttpContextAccessor, HttpContextAccessor>()
    .AddSingleton<AgentChecker>()
    .AddSingleton<TokenHandler>();

builder.Services.AddAuthentication()
    .AddScheme<JwtAuthOptions, JwtAuthHandler>(JwtAuthHandler.SchemeName, _ => { });

builder.Services.AddAuthorization(options =>
{
    options.DefaultPolicy = new AuthorizationPolicyBuilder()
        .AddAuthenticationSchemes(JwtAuthHandler.SchemeName)
        .RequireAuthenticatedUser()
        .Build();
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();
app.UseMiddleware<AgentChecker>();

app.UseHttpsRedirection();

app.UseAuthentication();
app.UseAuthorization();

app.MapRazorPages();

using (var scope = app.Services.CreateScope())
{
    var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();
    var dbContext = scope.ServiceProvider.GetRequiredService<SecretRallyDbContext>();

    await dbContext.Database.MigrateAsync();

    if (!await dbContext.Users.AnyAsync())
    {
        var username = "admin" + new Random().Next(1000, 2000);
        var password = RandomNumberGenerator.GetHexString(32);
        logger.LogInformation("Adding default user '{Username}' with password '{Password}' to database.", username, password);
        dbContext.Users.Add(new User { Username = username, Password = password });
    }

    var existingNames = await dbContext.Rallies.Select(r => r.Name).ToListAsync();

    foreach (var secretRally in app.Configuration.GetSection("SecretRallies").GetChildren())
    {
        if (existingNames.Contains(secretRally["Name"] ?? ""))
        {
            continue;
        }

        dbContext.Rallies.Add(new Rally
        {
            Name = secretRally["Name"] ?? "",
            Description = secretRally["Description"] ?? "",
            Location = secretRally["Location"] ?? "",
            Hidden = secretRally.GetValue("Hidden", false)
        });
    }

    dbContext.SaveChanges();
}

app.Run();
