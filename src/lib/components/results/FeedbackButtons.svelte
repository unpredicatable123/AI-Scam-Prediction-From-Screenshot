<script>
	import { saveFeedback } from '$lib/stores/scanHistory';
	import ThumbsUp from '@lucide/svelte/icons/thumbs-up';
	import ThumbsDown from '@lucide/svelte/icons/thumbs-down';
	import Check from '@lucide/svelte/icons/check';

	// Stored locally against this scan's history record (see
	// scanHistory.js's saveFeedback). Genuinely useful for a future manual
	// retraining pass — not wired to any automatic retraining pipeline,
	// which doesn't exist and isn't claimed here.
	let { scanId = '', class: className = '' } = $props();

	let choice = $state(null);

	function submit(wasCorrect) {
		if (!scanId) return;
		saveFeedback(scanId, wasCorrect);
		choice = wasCorrect ? 'correct' : 'incorrect';
	}
</script>

<div class="mx-auto flex max-w-xl items-center justify-center gap-3 {className}">
	{#if choice}
		<span class="flex items-center gap-1.5 text-sm" style="color: var(--text-tertiary);">
			<Check size={14} style="color: var(--color-risk-safe)" aria-hidden="true" />
			Thanks for the feedback
		</span>
	{:else}
		<span class="text-sm" style="color: var(--text-tertiary);">Was this prediction correct?</span>
		<button
			type="button"
			onclick={() => submit(true)}
			class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium"
			style="background: var(--surface-overlay); color: var(--text-primary);"
		>
			<ThumbsUp size={14} aria-hidden="true" /> Yes
		</button>
		<button
			type="button"
			onclick={() => submit(false)}
			class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium"
			style="background: var(--surface-overlay); color: var(--text-primary);"
		>
			<ThumbsDown size={14} aria-hidden="true" /> No
		</button>
	{/if}
</div>
