import type { ServerInit } from '@sveltejs/kit';
import { connectMqtt } from '$lib/server/mqtt';
import { seedDatabase } from '$lib/server/database';
import type { Handle } from '@sveltejs/kit';
import {
	validateSessionToken,
	setSessionTokenCookie,
	deleteSessionTokenCookie
} from '$lib/server/auth';
import { sequence } from '@sveltejs/kit/hooks';

export const init: ServerInit = async () => {
	const connections = Promise.all([connectMqtt(), seedDatabase()]);

	await connections;
};

const authHandle: Handle = async ({ event, resolve }) => {
	const token =
		event.cookies.get('session') ??
		event.request.headers.get('Authorization')?.split(' ')[1] ??
		null;
	if (token === null) {
		event.locals.user = null;
		event.locals.session = null;
		return resolve(event);
	}

	const { session, user } = await validateSessionToken(token);
	if (session !== null) {
		setSessionTokenCookie(event, token, session.expiresAt);
	} else {
		deleteSessionTokenCookie(event);
	}

	event.locals.session = session;
	event.locals.user = user;
	return resolve(event);
};

const logHandle: Handle = async ({ event, resolve }) => {
	const response = await resolve(event);
	console.info(`${event.request.method} ${event.request.url} (${response.status})`);

	return response;
};

export const handle = sequence(logHandle, authHandle);
