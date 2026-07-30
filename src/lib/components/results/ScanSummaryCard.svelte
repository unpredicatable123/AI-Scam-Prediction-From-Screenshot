<script>
	import { cn } from '$lib/utils/cn';
	import ShieldCheck from '@lucide/svelte/icons/shield-check';
	import ShieldQuestion from '@lucide/svelte/icons/shield-question';
	import ShieldAlert from '@lucide/svelte/icons/shield-alert';
	import ShieldMinus from '@lucide/svelte/icons/shield-minus';
	import ShieldX from '@lucide/svelte/icons/shield-x';
	import AnimatedNumber from './AnimatedNumber.svelte';

	const RISK_META = {
		safe: { icon: ShieldCheck, label: 'Safe', color: 'var(--color-risk-safe)' },
		low: { icon: ShieldQuestion, label: 'Low risk', color: 'var(--color-risk-low)' },
		medium: { icon: ShieldAlert, label: 'Suspicious', color: 'var(--color-risk-medium)' },
		high: { icon: ShieldMinus, label: 'High risk', color: 'var(--color-risk-high)' },
		critical: { icon: ShieldX, label: 'Scam', color: 'var(--color-risk-critical)' }
	};

	const CATEGORY_LABELS = {
		scam: 'General scam',
		phishing: 'Phishing',
		financial_scam: 'Financial scam',
		credential_harvesting: 'Credential harvesting',
		romance_dating: 'Romance / dating scam',
		tech_support: 'Tech support scam',
		authority_scam: 'Authority impersonation',
		social_engineering: 'Social engineering',
		social_engineering_advanced: 'Social engineering',
		urgency: 'Urgency-pressure scam',
		email: 'Suspicious email',
		generic_phishing: 'Phishing',
		threats: 'Threat / extortion',
		banking: 'Banking scam',
		investment: 'Investment scam',
		legitimate: 'No scam category'
	};

	let {
		label = 'fraudulent',
		riskBand = 'critical',
		riskScore = 86,
		category = null,
		confidence = 94,
		scanDurationMs = 0,
		scanTimestamp = null,
		class: className = ''
	} = $props();

	const isGenuine = $derived(label === 'genuine');
	const meta = $derived(RISK_META[riskBand] ?? RISK_META.medium);
	const categoryLabel = $derived(category ? (CATEGORY_LABELS[category] ?? category) : null);
	const timestampLabel = $derived(
		scanTimestamp
			? new Date(scanTimestamp).toLocaleString(undefined, {
					dateStyle: 'medium',
					timeStyle: 'medium'
				})
			: '—'
	);
</script>

<div class={cn('glass-panel mx-auto max-w-xl overflow-hidden rounded-2xl', className)}>
	<div
		class="flex items-center gap-3 px-6 py-5"
		style={`background: linear-gradient(120deg, color-mix(in oklch, ${meta.color} 16%, transparent), transparent);`}
	>
		<div
			class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
			style={`background: color-mix(in oklch, ${meta.color} 22%, transparent);`}
		>
			<meta.icon size={20} style={`color: ${meta.color}`} aria-hidden="true" />
		</div>
		<div>
			<div class="text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">Scan status</div>
			<div class="text-lg font-semibold" style={`color: ${meta.color}`}>{isGenuine ? 'Safe' : meta.label}</div>
		</div>
	</div>

	<div class="grid grid-cols-2 gap-px sm:grid-cols-3" style="background: var(--border-subtle);">
		{#if categoryLabel}
			<div class="flex flex-col gap-1 px-5 py-4" style="background: var(--surface-raised);">
				<span class="text-[10px] font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">Category</span>
				<span class="truncate text-sm font-semibold" style="color: var(--text-primary);">{categoryLabel}</span>
			</div>
		{/if}
		<div class="flex flex-col gap-1 px-5 py-4" style="background: var(--surface-raised);">
			<span class="text-[10px] font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">Confidence</span>
			<span class="font-mono text-sm font-semibold" style="color: var(--text-primary);">
				<AnimatedNumber value={confidence} decimals={1} suffix="%" />
			</span>
		</div>
		<div class="flex flex-col gap-1 px-5 py-4" style="background: var(--surface-raised);">
			<span class="text-[10px] font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">Risk score</span>
			<span class="font-mono text-sm font-semibold" style={`color: ${meta.color}`}>
				<AnimatedNumber value={riskScore} decimals={0} suffix="/100" />
			</span>
		</div>
		<div class="flex flex-col gap-1 px-5 py-4" style="background: var(--surface-raised);">
			<span class="text-[10px] font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">Scan duration</span>
			<span class="font-mono text-sm font-semibold" style="color: var(--text-primary);">
				<AnimatedNumber value={scanDurationMs / 1000} decimals={2} suffix="s" duration={600} />
			</span>
		</div>
		<div class="col-span-2 flex flex-col gap-1 px-5 py-4 sm:col-span-3" style="background: var(--surface-raised);">
			<span class="text-[10px] font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">Scanned at</span>
			<span class="font-mono text-sm" style="color: var(--text-secondary);">{timestampLabel}</span>
		</div>
	</div>
</div>
