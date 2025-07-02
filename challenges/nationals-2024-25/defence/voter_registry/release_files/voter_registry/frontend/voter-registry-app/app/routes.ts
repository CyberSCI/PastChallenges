import {
    type RouteConfig,
    route,
    index,
    layout,
    prefix,
} from "@react-router/dev/routes";

export default [
    layout("layouts/main.tsx", [
        index("routes/index.tsx"),

        route("register", "routes/register.tsx"),
        route("lookup", "routes/lookup.tsx"),
        route("stations/:station", "routes/station.tsx"),

        ...prefix("admin", [
            layout("layouts/admin.tsx", [
                index("./routes/admin/index.tsx"),
                route("callback", "./routes/admin/callback.tsx"),
                ...prefix("stations", [
                    route(":station", "./routes/admin/stations/station.tsx"),
                ]),
            ])
        ]),

        route("unauthorized", "routes/unauthorized.tsx"),
    ])
] satisfies RouteConfig;