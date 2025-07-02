import { KEYCLOAK_URL } from "config";
import { User, WebStorageStateStore } from "oidc-client-ts";
import type { AuthProviderProps } from "react-oidc-context";


export const OIDC_CONFIG = {
  authority: KEYCLOAK_URL + '/realms/voter-registry',
  client_id: 'voter-registry-app',
  redirect_uri: 'https://register.valverde.vote/admin/callback',
} satisfies AuthProviderProps;


export function getUser() {
    const oidcStorage = sessionStorage.getItem(`oidc.user:${OIDC_CONFIG.authority}:${OIDC_CONFIG.client_id}`);
    if (!oidcStorage) {
        return null;
    }
    return User.fromStorageString(oidcStorage);
}


export function getAccessToken() {
    const user = getUser();
    return user?.access_token;
}