import { connectMqtt } from '$lib/client/mqtt';
import type { DistrictVoteCount, VoteCounts } from '$lib/types';
import type { PageLoad } from './$types';

function initializeCurrentVotes(districtVoteCounts: DistrictVoteCount[]): VoteCounts {
	const currentVotes: VoteCounts = {};

	for (const district of districtVoteCounts) {
		currentVotes[district.id] = {};
		for (const party of district.parties) {
			currentVotes[district.id][party.id] = party.votes;
		}
	}
	return currentVotes;
}

export const load: PageLoad = async ({ data }) => {
	const mqttClient = await connectMqtt();
	const topic = 'vote-counts';
	await mqttClient.subscribeAsync(topic);

	mqttClient.on('error', async (err) => {
		console.error('MQTT Error: ' + err.message);
	});

	const districtVoteCounts: DistrictVoteCount[] = data.districtVoteCounts;

	const currentVotes = initializeCurrentVotes(districtVoteCounts);

	return {
		currentVotesInit: currentVotes,
		districtVoteCounts: data.districtVoteCounts,
		partiesResult: data.partiesResult,
		mqttClient
	};
};
