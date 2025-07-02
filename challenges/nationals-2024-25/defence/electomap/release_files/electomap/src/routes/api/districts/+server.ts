import type { RequestHandler } from './$types';
import { db } from '$lib/server/database';
import { districts } from '$lib/server/schema';

export const GET: RequestHandler = async ({}) => {
	const districtsResult = await db.select().from(districts);
	return new Response(JSON.stringify(districtsResult));
};
