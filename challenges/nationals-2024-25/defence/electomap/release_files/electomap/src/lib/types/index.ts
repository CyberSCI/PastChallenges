import type { District, Party } from '$lib/server/schema';

export type VoteCounts = Record<string, Record<string, number>>;

export interface VotePackage {
	party: string | null;
	district: string | null;
	voteKey: string | null;
}

export interface VoteCountUpdate {
	partyId: string;
	districtId: string;
}

export type PartyVoteCount = Party & { votes: number };

export type DistrictVoteCount = District & { parties: PartyVoteCount[] };

export interface User {
	name: string;
	nationalId: string;
	email: string;
}

export interface UserCreate extends User {
	password: string;
}

export interface UserInDb extends User {
	passwordHash: string;
}
