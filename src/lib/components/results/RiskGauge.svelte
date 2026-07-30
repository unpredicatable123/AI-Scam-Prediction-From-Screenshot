<script>
	import { onMount } from 'svelte';
	import { cn } from '$lib/utils/cn';

	const RISK_COLORS = {
		safe: 'var(--color-risk-safe)',
		low: 'var(--color-risk-low)',
		medium: 'var(--color-risk-medium)',
		high: 'var(--color-risk-high)',
		critical: 'var(--color-risk-critical)'
	};

	let { score = 0, band = 'medium', size = 96, class: className = '' } = $props();

	const radius = 40;
	const circumference = 2 * Math.PI * radius;

	// Paint the 0%-filled state first, then transition to the real value on the
	// next frame — CSS handles the tween so prefers-reduced-motion (app.css's
	// global transition-duration override) degrades it for free.
	let filled = $state(false);
	onMount(() => {
		requestAnimationFrame(() => (filled = true));
	});

	const color = $derived(RISK_COLORS[band] ?? RISK_COLORS.medium);
	const clamped = $derived(Math.round(Math.max(0, Math.min(100, score))));
	const offset = $derived(circumference - (filled ? clamped / 100 : 0) * circumference);
</script>

<div
	class={cn('relative inline-flex shrink-0 items-center justify-center', className)}
	style={`width:${size}px;height:${size}px;`}
	role="meter"
	aria-valuenow={clamped}
	aria-valuemin={0}
	aria-valuemax={100}
	aria-label={`Risk score ${clamped} out of 100, ${band}`}
>
	<svg viewBox="0 0 96 96" width={size} height={size} class="-rotate-90">
		<circle cx="48" cy="48" r={radius} fill="none" stroke="var(--border-default)" stroke-width="8" />
		<circle
			cx="48"
			cy="48"
			r={radius}
			fill="none"
			stroke={color}
			stroke-width="8"
			stroke-linecap="round"
			stroke-dasharray={circumference}
			stroke-dashoffset={offset}
			style="transition: stroke-dashoffset 1s var(--ease-out-expo), stroke 0.3s ease;"
		/>
	</svg>
	<div class="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
		<span class="font-mono text-lg leading-none font-semibold" style={`color: ${color}`}>{clamped}</span>
		<span class="text-[9px] leading-none font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
			risk
		</span>
	</div>
</div>
