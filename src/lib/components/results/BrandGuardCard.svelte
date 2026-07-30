<script>
	import { cn } from '$lib/utils/cn';
	import ShieldAlert from '@lucide/svelte/icons/shield-alert';

	// entities.brandImpersonation is null unless brand_guard.py's fuzzy match
	// actually found a distance-1 typosquat (see ml/src/features/brand_guard.py)
	// — this card simply doesn't render rather than showing an empty/false state.
	let { brandImpersonation = null, class: className = '' } = $props();
</script>

{#if brandImpersonation}
	<div
		class={cn('mx-auto flex max-w-xl items-start gap-3 rounded-xl px-5 py-4', className)}
		style="background: color-mix(in oklch, var(--color-risk-high) 10%, var(--surface-raised)); border: 1px solid color-mix(in oklch, var(--color-risk-high) 30%, transparent);"
	>
		<ShieldAlert size={18} class="mt-0.5 shrink-0" style="color: var(--color-risk-high)" aria-hidden="true" />
		<div class="flex flex-col gap-1">
			<span class="text-sm font-semibold" style="color: var(--color-risk-high);">Possible brand impersonation</span>
			<p class="text-sm" style="color: var(--text-secondary);">
				The name "<span class="font-mono font-semibold" style="color: var(--text-primary);">{brandImpersonation.suspicious_token}</span>"
				closely resembles the real brand "<span class="font-medium" style="color: var(--text-primary);">{brandImpersonation.matched_brand}</span>"
				— a common way to look legitimate at a glance.
			</p>
			<span class="mt-0.5 font-mono text-[11px]" style="color: var(--text-tertiary);">
				Confidence: {Math.round(brandImpersonation.confidence * 100)}%
			</span>
		</div>
	</div>
{/if}
