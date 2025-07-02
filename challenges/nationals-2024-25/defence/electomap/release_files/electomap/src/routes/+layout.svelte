<script lang="ts">
	import '../app.css';
	import Navbar from '$lib/components/navbar.svelte';

	let { children } = $props();
</script>

<div class="flex flex-col gap-4">
	<Navbar />
	<div class="flex justify-center">
		<main>
			{@render children()}
		</main>
	</div>
</div>
