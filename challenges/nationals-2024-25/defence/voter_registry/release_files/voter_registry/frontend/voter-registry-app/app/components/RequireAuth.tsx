import { useEffect, useState } from 'react';
import { hasAuthParams, useAuth } from 'react-oidc-context';
import { useNavigate } from 'react-router';

export default function RequireAuth({ children }: { children: React.ReactNode }) {
    const auth = useAuth();
    const [hasTriedSignin, setHasTriedSignin] = useState(false);
    const navigate = useNavigate();

    // automatically sign-in
    useEffect(() => {
        if (!hasAuthParams() &&
            !auth.isAuthenticated && !auth.activeNavigator && !auth.isLoading &&
            !hasTriedSignin
        ) {
            auth.signinRedirect();
            setHasTriedSignin(true);
        }
    }, [auth, hasTriedSignin]);

    if (!auth.isAuthenticated && (auth.isLoading || !hasTriedSignin)) {
        return null;
    }

    if (!auth.isAuthenticated || auth.error) {
        if (auth.error) {
            console.log('Auth error:', auth.error);
        }
        // Redirect to /unauthorized
        navigate('/unauthorized');
        return null;
    }

    return <>{children}</>;
}
