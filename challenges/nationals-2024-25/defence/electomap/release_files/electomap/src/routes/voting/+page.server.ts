import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from '../$types';
import { db } from '$lib/server/database';
import { parties, districts } from '$lib/server/schema';

export const load: PageServerLoad = async ({ locals }) => {
	if (locals.session === null || locals.user === null) {
		return redirect(302, '/signin');
	}
	const partiesQuery = db.select().from(parties);
	const districtsQuery = db.select().from(districts);

	const [partiesResult, districtsResult] = await Promise.all([partiesQuery, districtsQuery]);
	return {
		parties: partiesResult,
		districts: districtsResult
	};
};
