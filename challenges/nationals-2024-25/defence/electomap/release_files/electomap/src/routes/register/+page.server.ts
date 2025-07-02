import { error, fail, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { db } from '$lib/server/database';
import { users } from '$lib/server/schema';
import { hash } from '@node-rs/argon2';
import { createSession, generateSessionToken, setSessionTokenCookie } from '$lib/server/auth';

export const actions: Actions = {
	default: async (event) => {
		const { cookies, request } = event;
		const data = await request.formData();
		const email = data.get('email')?.toString();
		const name = data.get('name')?.toString();
		const nationalId = data.get('nationalId')?.toString();
		const password = data.get('password')?.toString();
		if (!email || !name || !nationalId || !password) {
			return fail(400, { email, name, nationalId, password, missing: true });
		}
		const passwordHash = await hash(password);
		const insertedIdResult = await db
			.insert(users)
			.values({
				name,
				email,
				nationalId,
				passwordHash
			})
			.returning({ userId: users.id });

		const userId = insertedIdResult[0].userId;

		const sessionToken = generateSessionToken();
		const session = await createSession(sessionToken, userId);
		setSessionTokenCookie(event, sessionToken, session.expiresAt);
		return redirect(302, '/voting');
	}
};
