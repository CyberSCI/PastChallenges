import { fail, error, redirect } from '@sveltejs/kit';
import type { Actions } from './$types';
import { db } from '$lib/server/database';
import { users } from '$lib/server/schema';
import { eq } from 'drizzle-orm';
import { verify } from '@node-rs/argon2';
import { createSession, generateSessionToken, setSessionTokenCookie } from '$lib/server/auth';

import type { PageServerLoad } from '../$types';
export const load: PageServerLoad = ({ locals }) => {
	if (locals.session === null || locals.user === null) {
		return {};
	}
	return redirect(302, '/');
};

export const actions: Actions = {
	default: async (event) => {
		const { request } = event;
		const data = await request.formData();
		const email = data.get('email')?.toString();
		const password = data.get('password')?.toString();
		if (!email || !password) {
			return fail(400, { email, password, missing: true });
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

		return redirect(302, '/voting');
	}
};
