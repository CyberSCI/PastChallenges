<script lang="ts">
	import type { PageProps } from './$types';
	import type { VoteCounts, VoteCountUpdate } from '$lib/types';
	import { Mutex } from '$lib/client/concurrency';

	let { data }: PageProps = $props();
	const { currentVotesInit, districtVoteCounts, partiesResult, mqttClient } = data;

	const currentVoteCounts: VoteCounts = $state(currentVotesInit);
	const voteCountMutex = new Mutex();

	mqttClient.on('message', async (topic, message) => {
		const newVote: VoteCountUpdate = JSON.parse(message.toString());
		await voteCountMutex.dispatch(async () => {
			// This just initializes the counts in case anything is undefined
			currentVoteCounts[newVote.districtId] ??= {};
			currentVoteCounts[newVote.districtId][newVote.partyId] ??= 0;
			currentVoteCounts[newVote.districtId][newVote.partyId] += 1;
		});
	});

	function getVotes(districtId: string, partyId: string): number {
		return currentVoteCounts[districtId][partyId] ?? 0;
	}
</script>

<h1>Electomap</h1>

<article></article>
<table class="table-auto">
	<thead class="bg-amber-200">
		<tr>
			<th class="py-2 ps-2 pe-4 text-left"> District </th>

			{#each partiesResult as party}
				<th class="p-2"> {party.short_name} </th>
			{/each}
		</tr>
	</thead>
	<tbody>
		{#each districtVoteCounts as district}
			<tr>
				<td class="py-2 ps-2 pe-4 border-r-2 border-r-amber-100">{district.name}</td>
				{#each district.parties as party}
					<td class="p-2 text-center">{getVotes(district.id, party.id)}</td>
				{/each}
			</tr>
		{/each}
	</tbody>
</table>
