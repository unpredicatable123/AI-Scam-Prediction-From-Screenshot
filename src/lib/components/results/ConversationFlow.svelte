<script>
	import { cn } from '$lib/utils/cn';
	import GitBranch from '@lucide/svelte/icons/git-branch';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';

	const RISK_COLOR = {
		low: 'var(--color-risk-safe)',
		medium: 'var(--color-risk-medium)',
		high: 'var(--color-risk-high)',
		critical: 'var(--color-risk-critical)'
	};

	// A real heuristic over where each existing signal category first
	// appears in the text (ml/src/features/conversation_flow.py) — not a
	// separate AI system. Only shown when at least two stages are present;
	// a single isolated category isn't a "flow."
	let { risk = 'low', stageCount = 0, sequence = [], class: className = '' } = $props();

	const color = $derived(RISK_COLOR[risk] ?? RISK_COLOR.low);
</script>

{#if stageCount >= 2}
	<div class={cn('glass-panel mx-auto max-w-xl rounded-xl px-5 py-4', className)}>
		<div class="mb-3 flex items-center justify-between">
			<h3 class="flex items-center gap-1.5 text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
				<GitBranch size={13} aria-hidden="true" /> Conversation pattern
			</h3>
			<span
				class="rounded-full px-2.5 py-0.5 text-[11px] font-semibold capitalize"
				style={`background: color-mix(in oklch, ${color} 20%, transparent); color: ${color};`}
			>
				{risk} risk
			</span>
		</div>
		<div class="flex flex-wrap items-center gap-1.5">
			{#each sequence as stage, i (stage + i)}
				<span
					class="rounded-full px-2.5 py-1 text-xs font-medium"
					style="background: var(--surface-overlay); color: var(--text-primary);"
				>
					{stage}
				</span>
				{#if i < sequence.length - 1}
					<ChevronRight size={13} style="color: var(--text-tertiary)" aria-hidden="true" />
				{/if}
			{/each}
		</div>
	</div>
{/if}
