import { env } from '$env/dynamic/private';

const encoder = new TextEncoder();
export const JWT_SECRET = encoder.encode(env.AUTH_SECRET ?? 'default-jwt-secret');
