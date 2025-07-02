import { error, redirect } from '@sveltejs/kit';
import { invalidateSession, deleteSessionTokenCookie } from '$lib/server/auth';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async (event) => {
	const { cookies, locals, request } = event;
	if (locals.session === null || locals.user == null) {
		return error(401, { message: 'Not authenticated.' });
	}

	deleteSessionTokenCookie(event);
	await invalidateSession(locals.session.id);
	return new Response(null, { status: 204 });
};
