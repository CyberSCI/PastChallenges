import type { RequestHandler } from './$types';
import { db } from '$lib/server/database';
import { parties } from '$lib/server/schema';

export const GET: RequestHandler = async ({}) => {
	const partiesResult = await db.select().from(parties);
	return new Response(JSON.stringify(partiesResult));
};
