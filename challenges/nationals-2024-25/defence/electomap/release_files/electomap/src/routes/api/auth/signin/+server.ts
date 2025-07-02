import { error, fail } from '@sveltejs/kit';
import { db } from '$lib/server/database';
import { users } from '$lib/server/schema';
import { eq } from 'drizzle-orm';
import { hash, verify } from '@node-rs/argon2';
import { createSession, generateSessionToken, setSessionTokenCookie } from '$lib/server/auth';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async (event) => {
	const { cookies, request } = event;
	const data = await request.json();
	const email = data.email;
	const password = data.password;
	if (!email || !password) {
		throw fail(400, { email, password, missing: true });
	}
	const userResult = await db.query.users.findFirst({
		where: eq(users.email, email),
		columns: { passwordHash: true, id: true }
	});

	if (!userResult) {
		return error(401, 'Invalid credentials.');
	}

	const { passwordHash, id: userId } = userResult;

	const validPassword = verify(passwordHash, password);

	if (!validPassword) {
		return error(401, 'Invalid credentials.');
	}

	const sessionToken = generateSessionToken();
	const session = await createSession(sessionToken, userId);
	setSessionTokenCookie(event, sessionToken, session.expiresAt);
	return new Response(null, { status: 200 });
};
