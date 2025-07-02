<script lang="ts">
	import { goto } from '$app/navigation';
	import { userState } from '$lib/client/state.svelte';
	import axios from 'axios';

	async function logout() {
		const res = await axios.post('/api/auth/signout', null, { withCredentials: true });
		if (res.status !== 204) {
			alert('Something went wrong.');
			return;
		}
		userState.authenticated = false;
		goto('/');
	}
</script>

<nav class="flex justify-between gap-2 w-full">
	<div class="flex gap-2">
		<a href="/" class="p-2">Home</a>
		{#if userState.authenticated}
			<a href="/voting" class="p-2">Voters</a>
		{/if}
	</div>
	<div class="flex gap-2">
		{#if userState.authenticated}
			<button onclick={logout}>Log Out</button>
		{:else}
			<a href="/register" class="p-2">Register</a>
			<a href="/signin" class="p-2">Sign In</a>
		{/if}
	</div>
</nav>
