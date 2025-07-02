<script lang="ts">
	import axios from 'axios';
	import type { PageProps } from './$types';
	import type { VotePackage } from '$lib/types';
	import { env } from '$env/dynamic/public';

	// Call the API to make a vote key, user uses that to vote along with their data

	let { data }: PageProps = $props();
	const { parties, districts } = data;

	let votePackage = $state<VotePackage>({
		party: null,
		district: null,
		voteKey: null
	});

	let readyForDownload = $derived(!!(votePackage.party && votePackage.district));

	async function makeVoteKey() {
		const res = await axios.post('/api/votekeys', null, { withCredentials: true });
		const { voteKey: newKey } = await res.data;
		votePackage.voteKey = newKey;
	}

	async function downloadVotePackage() {
		if (!readyForDownload) {
			alert('Please select a district and party.');
			return;
		}

		await makeVoteKey();

		console.info('Vote key created.');

		const filename = 'votePackage.json';
		const file = new Blob([JSON.stringify(votePackage, null, 2)], {
			type: 'application/json'
		});
		const downloadAnchor = document.createElement('a');
		downloadAnchor.href = URL.createObjectURL(file);
		downloadAnchor.download = filename;
		document.body.appendChild(downloadAnchor);
		downloadAnchor.click();
		document.body.removeChild(downloadAnchor);
		console.info('Download started.');
	}
</script>

<div class="container max-w-[600px] flex flex-col gap-2">
	<h1>Voters</h1>
	<p>
		We use an advanced REST API for our voting! Everything except the vote key is calculated on your
		computer only.
	</p>
	<p>
		Select your district and party of choice here. At the polls, have your vote package ready to go.
	</p>
	<p>
		<b>Note:</b> If you would like to vote as soon as you get your package, you can do so by making
		a POST request with your package to our API endpoint:
		<i class="block">{env.PUBLIC_ORIGIN}/api/votes</i>
	</p>
	<div class="grid grid-cols-3 gap-x-4 gap-y-2 container">
		<section>
			<h2>Parties</h2>
			<aside class="flex flex-col">
				{#each parties as party}
					<label>
						<input type="radio" name="party" value={party.id} bind:group={votePackage.party} />
						{party.name}
					</label>
				{/each}
			</aside>
		</section>
		<section>
			<h2>Districts</h2>
			<aside class="flex flex-col">
				{#each districts as district}
					<label>
						<input
							type="radio"
							name="district"
							value={district.id}
							bind:group={votePackage.district}
						/>
						{district.name}
					</label>
				{/each}
			</aside>
		</section>
		<section>
			<h2 class="text-xl text-center">Your Vote Package</h2>
			<aside class="flex justify-center items-center">
				<button onclick={downloadVotePackage}> Download Vote Package </button>
			</aside>
		</section>
	</div>
</div>
