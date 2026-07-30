<script>
	import { reveal } from '$lib/motion/actions';
	import ResultCard from '$lib/components/results/ResultCard.svelte';
	import ListChecks from '@lucide/svelte/icons/list-checks';
</script>

<section class="relative mx-auto max-w-5xl px-6 py-32">
	<div use:reveal={{ y: 24 }} class="mx-auto mb-16 max-w-2xl text-center">
		<div
			class="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-xl"
			style="background: color-mix(in oklch, var(--color-risk-critical) 16%, transparent);"
		>
			<ListChecks size={20} style="color: var(--color-risk-critical)" aria-hidden="true" />
		</div>
		<span class="text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
			06 · The result
		</span>
		<h2 class="mt-4 text-4xl font-semibold tracking-tight text-balance">A verdict you can actually act on</h2>
		<p class="mt-3 text-base" style="color: var(--text-secondary);">
			Everything from the last three sections, assembled into one screen.
		</p>
	</div>

	<div use:reveal={{ y: 28, delay: 0.1 }}>
		<ResultCard />
	</div>
</section>
