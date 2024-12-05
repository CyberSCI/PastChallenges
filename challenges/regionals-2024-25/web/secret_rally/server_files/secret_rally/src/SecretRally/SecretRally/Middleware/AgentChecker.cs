namespace SecretRally.Middleware
{
    public class AgentChecker : IMiddleware
    {
        public Task InvokeAsync(HttpContext context, RequestDelegate next)
        {
            var validUserAgents = new[]
            {
                "Mozilla",
                "Firefox",
                "Chrome",
                "Safari",
                "Opera",
                "Edg"
            };
            
            if (!context.Request.Headers.TryGetValue("User-Agent", out var userAgent) ||
                validUserAgents.All(validUserAgent => !userAgent.ToString().Contains(validUserAgent + "/")))
            {
                context.Response.StatusCode = 403;

                return Task.CompletedTask;
            }

            return next(context);
        }
    }
}
