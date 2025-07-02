// Load in party data
// Single view
// Group by districts, sum each party's vote counts
import { db } from '$lib/server/database';
import { districtVotes, districts, parties } from '$lib/server/schema';
import { count, eq } from 'drizzle-orm';
import type { PageServerLoad } from './$types';
import type { VoteCounts } from '$lib/types';

export const load: PageServerLoad = async ({ params }) => {
	const votesQuery = db
		.select({
			districtId: districts.id,
			partyId: parties.id,
			district: districts.name,
			party: parties.name,
			votes: count()
		})
		.from(districtVotes)
		.leftJoin(districts, eq(districts.id, districtVotes.districtId))
		.leftJoin(parties, eq(parties.id, districtVotes.partyId))
		.groupBy(districts.id, parties.id);

	const partiesQuery = db.select().from(parties);
	const districtsQuery = db.select().from(districts);

	const [voteResult, partiesResult, districtsResult] = await Promise.all([
		votesQuery,
		partiesQuery,
		districtsQuery
	]);

	const voteCounts = voteResult.reduce<VoteCounts>((accumulator, currentVoteResult) => {
		const districtId = currentVoteResult.districtId;
		const partyId = currentVoteResult.partyId;
		if (!districtId) return accumulator;
		if (!partyId) return accumulator;
		if (!Object.hasOwn(accumulator, districtId)) {
			accumulator[districtId] = {};
		}
		accumulator[districtId][partyId] = currentVoteResult.votes;
		return accumulator;
	}, {});

	const districtVoteCounts = districtsResult.map((district) => ({
		...district,
		parties: partiesResult.map((party) => {
			if (!Object.hasOwn(voteCounts, district.id)) return { ...party, votes: 0 };
			return { ...party, votes: voteCounts[district.id][party.id] ?? 0 };
		})
	}));

	return { districtVoteCounts, partiesResult };
};
