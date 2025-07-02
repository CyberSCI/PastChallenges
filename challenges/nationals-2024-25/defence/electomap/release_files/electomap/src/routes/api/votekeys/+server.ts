import { error } from '@sveltejs/kit';
import * as jose from 'jose';
import { JWT_SECRET } from '$lib/server/secrets';
import type { RequestHandler } from './$types';
import { db } from '$lib/server/database';
import { users } from '$lib/server/schema';
import { eq } from 'drizzle-orm';

export const POST: RequestHandler = async ({ locals, request }) => {
	if (locals.session === null || locals.user == null) {
		return error(401);
	}

	const voteKey = await new jose.SignJWT({ sub: locals.user.nationalId })
		.setProtectedHeader({ alg: 'HS256' })
		.sign(JWT_SECRET);

	await db.update(users).set({ voteKey }).where(eq(users.nationalId, locals.user.nationalId));
	return new Response(JSON.stringify({ voteKey }), { status: 201 });
};
