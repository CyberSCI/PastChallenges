<script lang="ts">
	import { enhance, applyAction } from '$app/forms';
	import { userState } from '$lib/client/state.svelte';
	import type { PageProps } from './$types';

	let { form }: PageProps = $props();
</script>

<div class="flex justify-center">
	<form
		method="POST"
		class="flex flex-col gap-2 w-[400px]"
		use:enhance={({ formElement, formData, action, cancel }) => {
			return async ({ result }) => {
				// `result` is an `ActionResult` object
				if (result.type === 'redirect') {
					userState.authenticated = true;
					console.debug('Authenticated.');
				}

				await applyAction(result);
			};
		}}
	>
		<h1 class="text-2xl">Register</h1>
		<label for="name">
			Name
			<input name="name" class="input-field block w-full" />
		</label>
		<label for="email">
			Email
			<input name="email" type="email" class="input-field block w-full" />
		</label>
		<label for="nationalId">
			National ID
			<input name="nationalId" class="input-field block w-full" />
		</label>
		<label for="password">
			Password
			<input name="password" type="password" class="input-field block w-full" />
		</label>
		<button> Register </button>
	</form>
</div>
