# Voter Registry Solution

## Vulnerability Overview

1. Keycloak registration is allowed. Authentication on the app side checks if the user is logged in, but not if they're in the admin group.
   Solution: Disable anonymous registration OR configure app to check if user is in voter admin group.
2. Invalid JWT signature validation.
3. Missing authorization on certain endpoints (`GET /Files/GetFile`, `POST /PollingStation/{id}/advisory`).
4. Local file inclusion on `GET /Files/GetFile` endpoint.
5. Command injection via file name parameter when registering to vote.

## Vuln #1 Solution

Modify `voter_registry/keycloak/voter-registry-realm.json`:

```diff
  "sslRequired" : "external",
- "registrationAllowed" : true,
+ "registrationAllowed" : false,
  "registrationEmailAsUsername" : false,
```

Spin down Keycloak, delete `voter_registry/instance/keycloak_db`, and spin it back up.

## Vuln #2 Solution

Modify `voter_registry/backend/VoterRegistry/VoterRegistryApi/appsettings.json`:

```diff
...
    "Authentication": {
+     "Authority": "https://auth.register.valverde.vote/realms/voter-registry",
      "Audience": "voter-registry-app"
    },
...
```

Modify `voter_registry/backend/VoterRegistry/VoterRegistryApi/Extensions/CustomExtensions.cs`:

```diff
  .AddJwtBearer("Bearer", options =>
  {
+     options.Authority = builder.Configuration["Authentication:Authority"];
      options.Audience = builder.Configuration["Authentication:Audience"];
  
      // Trust self-signed certificate
-     options.TokenValidationParameters = new TokenValidationParameters
-     {
-         ValidateIssuer = false,
-         SignatureValidator = (token, _) => new JsonWebToken(token),
-     };
      options.BackchannelHttpHandler = new HttpClientHandler
      {
          ServerCertificateCustomValidationCallback = (message, cert, chain, errors) => true
      };
  });
```

## Vuln #3 Solution

Modify `voter_registry/backend/VoterRegistry/VoterRegistryApi/Controllers/FilesController.cs`:

```diff
+ using Microsoft.AspNetCore.Authorization;
  using Microsoft.AspNetCore.Mvc;
  ...
          [HttpGet("")]
+         [Authorize]
          public async Task<IActionResult> GetFile([FromQuery] string path)
```

Modify `voter_registry/backend/VoterRegistry/VoterRegistryApi/Controllers/PollingStationController.cs`:

```diff
          [HttpGet("")]
+         [Authorize]
          public async Task<IActionResult> GetAll(int offset = 0, int limit = 100)
  ...
          [HttpPost("{id}/advisory")]
+         [Authorize]
          public async Task<IActionResult> AddAdvisory(int id, [FromBody] AdvisoryDto advisory)
```

## Vuln #4 Solution


Modify `voter_registry/backend/VoterRegistry/VoterRegistryApi/Controllers/FilesController.cs`:

```diff
          public async Task<IActionResult> GetFile([FromQuery] string path)
          {
-             var fullPath = Path.Combine(_configuration["RegistrationFilePath"] ?? ".", path);
+             var fullPath = Path.Combine(_configuration["RegistrationFilePath"] ?? ".", Path.GetFileName(path));
```

## Vuln #5 Solution

Modify `voter_registry/backend/VoterRegistry/VoterRegistryApi/Controllers/RegistrationController.cs`:

```diff
-             string? fileName = null;
-             string? filePath = null;
-             try
-             {
-                 fileName = $"{Guid.NewGuid()}_{registrationDto.AddressProof.FileName}";
-                 filePath = Path.Combine(_configuration.GetValue("RegistrationFilePath", "./"), fileName);
-                 using (var stream = new FileStream(filePath, FileMode.Create))
-                 {
-                     await registrationDto.AddressProof.CopyToAsync(stream);
-                 }
-             }
-             catch { }
+             var fileName = Guid.NewGuid().ToString() + Path.GetExtension(registrationDto.AddressProof.FileName);
+             var filePath = Path.Combine(_configuration.GetValue("RegistrationFilePath", "./"), fileName);
+
+             using (var stream = new FileStream(filePath, FileMode.Create))
+             {
+                 await registrationDto.AddressProof.CopyToAsync(stream);
+             }
  ...
                  StartInfo = new ProcessStartInfo
                  {
-                     FileName = "bash",
+                     FileName = "python3",
-                     Arguments = $"-c \"python3 documentscanner.py '{filePath}'\"",
+                     ArgumentList = { "documentscanner.py", filePath },
```