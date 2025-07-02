import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import * as jose from 'jose';
import { JWT_SECRET } from '$lib/server/secrets';
import { validateSessionToken } from '$lib/server/auth';
import type { VotePackage } from '$lib/types';
import { connectMqtt } from '$lib/client/mqtt';

export const POST: RequestHandler = async ({ request }) => {
	const votePackage: VotePackage = await request.json();

	const voteKey = votePackage.voteKey;
	const partyId = votePackage.party;
	const districtId = votePackage.district;
	if (!(voteKey && partyId && districtId)) {
		return error(400, {
			message: 'Missing field: ' + JSON.stringify({ voteKey, partyId, districtId })
		});
	}

	const { sub } = jose.decodeJwt(voteKey);

	const mqttClient = await connectMqtt();

	await mqttClient.publishAsync('votes', JSON.stringify(votePackage));

	return new Response(null, { status: 204 });
};
