<script>
	import { cn } from '$lib/utils/cn';
	import Link from '@lucide/svelte/icons/link';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';

	// Heuristic-only, deliberately: this project has no external threat-intel
	// integration (WHOIS, domain age, reputation, blacklist) — those would
	// need a real API and a cost/rate-limit decision, not a UI change. Every
	// row here maps 1:1 to a real regex-based signal already computed in
	// ml/src/features/text_features.py.
	let { hasUrl = false, hasShortenerUrl = false, hasIpUrl = false, urlMaxRisk = 0, class: className = '' } = $props();

	const riskPct = $derived(Math.round(urlMaxRisk * 100));
	const riskColor = $derived(riskPct >= 60 ? 'var(--color-risk-critical)' : riskPct >= 30 ? 'var(--color-risk-high)' : 'var(--color-risk-safe)');
</script>

{#if hasUrl}
	<div class={cn('glass-panel mx-auto max-w-xl rounded-xl px-5 py-4', className)}>
		<h3 class="mb-3 flex items-center gap-1.5 text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
			<Link size={13} aria-hidden="true" /> Link analysis
			<span class="ml-auto font-mono text-[10px] normal-case" style="color: var(--text-tertiary);">heuristic, not a reputation service</span>
		</h3>
		<div class="flex flex-col gap-2.5">
			<div class="flex items-center justify-between text-sm">
				<span style="color: var(--text-secondary);">Shortened link</span>
				{#if hasShortenerUrl}
					<span class="flex items-center gap-1 font-medium" style="color: var(--color-risk-high);"><X size={13} aria-hidden="true" /> Yes — hides real destination</span>
				{:else}
					<span class="flex items-center gap-1" style="color: var(--color-risk-safe);"><Check size={13} aria-hidden="true" /> No</span>
				{/if}
			</div>
			<div class="flex items-center justify-between text-sm">
				<span style="color: var(--text-secondary);">Raw IP address link</span>
				{#if hasIpUrl}
					<span class="flex items-center gap-1 font-medium" style="color: var(--color-risk-high);"><X size={13} aria-hidden="true" /> Yes — not a real domain</span>
				{:else}
					<span class="flex items-center gap-1" style="color: var(--color-risk-safe);"><Check size={13} aria-hidden="true" /> No</span>
				{/if}
			</div>
			<div class="flex flex-col gap-1.5">
				<div class="flex items-center justify-between text-sm">
					<span style="color: var(--text-secondary);">Heuristic risk score</span>
					<span class="font-mono font-medium" style={`color: ${riskColor}`}>{riskPct}%</span>
				</div>
				<span class="h-1.5 w-full overflow-hidden rounded-full" style="background: var(--surface-overlay);">
					<span class="block h-full rounded-full" style={`width: ${riskPct}%; background: ${riskColor}; transition: width 0.8s var(--ease-out-expo);`}></span>
				</span>
			</div>
		</div>
	</div>
{/if}
