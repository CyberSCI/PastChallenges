import { error, fail } from '@sveltejs/kit';
import { db } from '$lib/server/database';
import { users } from '$lib/server/schema';
import { hash } from '@node-rs/argon2';
import { createSession, generateSessionToken, setSessionTokenCookie } from '$lib/server/auth';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async (event) => {
	const { cookies, request } = event;
	const data = await request.json();
	const email = data.email;
	const name = data.name;
	const nationalId = data.nationalId;
	const password = data.password;
	if (!email || !name || !nationalId || !password) {
		throw fail(400, { email, name, nationalId, password, missing: true });
	}
	const passwordHash = await hash(password);
	const insertedUserResult = await db
		.insert(users)
		.values({
			name,
			email,
			nationalId,
			passwordHash
		})
		.returning({ userId: users.id, email: users.email, name: users.name });

	const user = insertedUserResult[0];

	const userId = user.userId;

	const sessionToken = generateSessionToken();
	const session = await createSession(sessionToken, userId);
	setSessionTokenCookie(event, sessionToken, session.expiresAt);
	return new Response(JSON.stringify(user), { status: 201 });
};
