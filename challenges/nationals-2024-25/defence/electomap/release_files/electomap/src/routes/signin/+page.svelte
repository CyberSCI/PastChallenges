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
					console.log(userState);
				}

				await applyAction(result);
			};
		}}
	>
		<h1 class="text-2xl">Sign In</h1>
		<label>
			Email
			<input name="email" type="email" class="input-field block w-full" />
		</label>
		<label>
			Password
			<input name="password" type="password" class="input-field block w-full" />
		</label>
		<button> Log in </button>
	</form>
</div>
