<script>
	import { fly } from 'svelte/transition';
	import { cn } from '$lib/utils/cn';
	import { prefersReducedMotion } from '$lib/motion/actions';
	import ShieldCheck from '@lucide/svelte/icons/shield-check';
	import ShieldQuestion from '@lucide/svelte/icons/shield-question';
	import ShieldAlert from '@lucide/svelte/icons/shield-alert';
	import ShieldMinus from '@lucide/svelte/icons/shield-minus';
	import ShieldX from '@lucide/svelte/icons/shield-x';
	import CircleCheckBig from '@lucide/svelte/icons/circle-check-big';
	import CircleHelp from '@lucide/svelte/icons/circle-help';
	import RiskGauge from './RiskGauge.svelte';

	const RISK_META = {
		safe: { icon: ShieldCheck, label: 'Safe', verdict: 'Looks safe', color: 'var(--color-risk-safe)' },
		low: { icon: ShieldQuestion, label: 'Low risk', verdict: 'Probably safe', color: 'var(--color-risk-low)' },
		medium: { icon: ShieldAlert, label: 'Medium risk', verdict: 'Possibly a scam', color: 'var(--color-risk-medium)' },
		high: { icon: ShieldMinus, label: 'High risk', verdict: 'Likely a scam', color: 'var(--color-risk-high)' },
		critical: { icon: ShieldX, label: 'Critical risk', verdict: 'Likely a scam', color: 'var(--color-risk-critical)' }
	};

	let {
		class: className = '',
		label = 'fraudulent',
		riskBand = 'critical',
		riskScore = 86,
		category = 'Job scam',
		confidence = 94,
		reasons = [
			{ text: 'Financial request — a $250 fee before any job starts', contribution: 0.31 },
			{ text: 'Urgency language pressuring an immediate decision', contribution: 0.22 },
			{ text: 'Brand mismatch — claimed bank, unrelated domain', contribution: 0.15 },
			{ text: 'Asked to share bank details outside any verified channel', contribution: 0.09 }
		],
		actions = [
			"Don't pay any upfront fee or “registration charge.”",
			'Verify the company independently — search for it, never via a link in the message.',
			'Report and block this sender.'
		],
		timingBreakdown = [],
		footerNote = 'Analyzed in 2.1s · model v1.0 · feature schema v3'
	} = $props();

	const meta = $derived(RISK_META[riskBand] ?? RISK_META.medium);
	const isGenuine = $derived(label === 'genuine');
	const maxContribution = $derived(Math.max(...reasons.map((r) => r.contribution ?? 0), 0.0001));

	// This card is inserted fresh once a fetch resolves, usually while already
	// on-screen — no scroll ever happens, so the scroll-triggered `reveal`
	// action (built for the marketing page's scroll narrative) can leave
	// items stuck at opacity:0 with their layout space still reserved. Plain
	// mount-triggered Svelte transitions are the correct primitive here.
	const noMotion = prefersReducedMotion();
	const flyIn = (delayMs) => (noMotion ? { duration: 0 } : { y: 10, duration: 400, delay: delayMs });
</script>

<div class={cn('glass-panel mx-auto max-w-xl overflow-hidden rounded-2xl', className)}>
	<div
		class="flex flex-wrap items-center gap-4 px-7 py-6"
		style={`background: linear-gradient(120deg, color-mix(in oklch, ${meta.color} 14%, transparent), transparent);`}
	>
		<div
			class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
			style={`background: color-mix(in oklch, ${meta.color} 20%, transparent);`}
		>
			<meta.icon size={24} style={`color: ${meta.color}`} aria-hidden="true" />
		</div>
		<div class="flex min-w-0 flex-1 flex-col gap-1">
			<div class="flex flex-wrap items-center gap-2">
				<span class="text-lg font-semibold" style="color: var(--text-primary);">
					{isGenuine ? 'Looks safe' : meta.verdict}
				</span>
				<span
					class="rounded-full px-2 py-0.5 text-[11px] font-medium"
					style={`background: color-mix(in oklch, ${meta.color} 22%, transparent); color: ${meta.color};`}
				>
					{meta.label}
				</span>
			</div>
			<span class="text-sm" style="color: var(--text-secondary);">
				{#if !isGenuine && category}{category} · {/if}<span class="font-mono">{confidence}%</span> model confidence
			</span>
		</div>

		<RiskGauge score={riskScore} band={riskBand} size={72} />
	</div>

	<div class="flex flex-col gap-6 px-7 py-6">
		{#if !isGenuine && reasons.length === 0}
			<div
				in:fly={flyIn(0)}
				class="flex items-start gap-2.5 rounded-lg px-3.5 py-3 text-sm"
				style="background: var(--surface-overlay); color: var(--text-secondary);"
			>
				<CircleHelp size={16} class="mt-0.5 shrink-0" style="color: var(--text-tertiary)" aria-hidden="true" />
				Flagged by writing style and structural patterns that don't map to one specific listed reason.
			</div>
		{:else if reasons.length > 0}
			<div>
				<h3 class="mb-3 text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">Why</h3>
				<ul class="flex flex-col gap-3">
					{#each reasons as reason, i (reason.text)}
						{@const pct = Math.max(8, Math.round(((reason.contribution ?? 0) / maxContribution) * 100))}
						<li in:fly={flyIn(i * 80)} class="flex flex-col gap-1.5">
							<span class="text-sm" style="color: var(--text-secondary);">{reason.text}</span>
							<span class="h-1 w-full overflow-hidden rounded-full" style="background: var(--surface-overlay);">
								<span
									class="block h-full rounded-full"
									style={`width: ${pct}%; background: ${meta.color}; transition: width 0.8s var(--ease-out-expo) ${i * 0.08}s;`}
								></span>
							</span>
						</li>
					{/each}
				</ul>
			</div>
		{/if}

		{#if actions.length > 0}
			<div class="border-t pt-6" style="border-color: var(--border-subtle);">
				<h3 class="mb-3 text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">What to do</h3>
				<ul class="flex flex-col gap-2.5">
					{#each actions as action, i (action)}
						<li in:fly={flyIn(200 + i * 60)} class="flex items-start gap-2.5 text-sm" style="color: var(--text-primary);">
							<CircleCheckBig size={16} class="mt-0.5 shrink-0" style="color: var(--accent-secondary)" aria-hidden="true" />
							{action}
						</li>
					{/each}
				</ul>
			</div>
		{/if}
	</div>

	{#if footerNote || timingBreakdown.length > 0}
		<div
			class="flex flex-col gap-1.5 border-t px-7 py-3"
			style="border-color: var(--border-subtle); background: var(--surface-overlay);"
		>
			{#if footerNote}
				<span class="font-mono text-[11px]" style="color: var(--text-tertiary);">{footerNote}</span>
			{/if}
			{#if timingBreakdown.length > 0}
				<div class="flex flex-wrap gap-x-3 gap-y-1 font-mono text-[10px]" style="color: var(--text-tertiary);">
					{#each timingBreakdown as t (t.label)}
						<span>{t.label} <span style="color: var(--text-secondary);">{t.ms}ms</span></span>
					{/each}
				</div>
			{/if}
		</div>
	{/if}
</div>
