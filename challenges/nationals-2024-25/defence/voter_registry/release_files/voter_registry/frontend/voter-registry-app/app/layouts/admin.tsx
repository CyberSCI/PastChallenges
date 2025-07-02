import { AuthProvider } from "react-oidc-context";
import { Outlet, useNavigate } from "react-router";
import { OIDC_CONFIG } from "~/oidc";
import RequireAuth from "~/components/RequireAuth";

export default function AdminLayout() {
    const navigate = useNavigate();
    
    const onSigninCallback = () => {
        window.history.replaceState(
            {},
            document.title,
            window.location.pathname
        );

        navigate("/admin");
    };

    return (
        <AuthProvider {...OIDC_CONFIG} onSigninCallback={onSigninCallback}>
            <RequireAuth>
                <Outlet />
            </RequireAuth>
        </AuthProvider>
    );
}