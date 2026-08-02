<script>
	import { onMount, onDestroy } from 'svelte';
	import { gsap, prefersReducedMotion } from '$lib/motion/gsap';
	import { scrollTimeline } from '$lib/motion/scroll';
	import { reveal } from '$lib/motion/actions';
	import Sparkles from '@lucide/svelte/icons/sparkles';
	import Gauge from '@lucide/svelte/icons/gauge';
	import ShieldX from '@lucide/svelte/icons/shield-x';

	const reasons = [
		{ label: 'Financial request', weight: 0.32, evidence: 'Asks for a $250 "registration fee" before any job starts.' },
		{ label: 'Urgency language', weight: 0.24, evidence: '"to avoid losing this offer" pressures a quick, unverified decision.' },
		{ label: 'Brand mismatch', weight: 0.19, evidence: 'Claims SBI Bank, but links to sbi-secure-payments.xyz.' },
		{ label: 'Contact-shift request', weight: 0.11, evidence: 'Asks to reply with bank details outside any verified channel.' }
	];
	const maxWeight = Math.max(...reasons.map((r) => r.weight));

	/** @type {HTMLElement} */
	let sectionEl;
	/** @type {HTMLElement[]} */
	let barEls = [];
	/** @type {HTMLElement[]} */
	let reasonEls = [];
	/** @type {HTMLElement} */
	let metersEl;
	let tween;

	onMount(() => {
		if (prefersReducedMotion()) {
			gsap.set(barEls, { width: (i) => `${(reasons[i].weight / maxWeight) * 100}%` });
			gsap.set(reasonEls, { opacity: 1, x: 0 });
			gsap.set(metersEl, { opacity: 1, y: 0 });
			return;
		}

		gsap.set(barEls, { width: '0%' });
		gsap.set(reasonEls, { opacity: 0, x: -10 });
		gsap.set(metersEl, { opacity: 0, y: 12 });

		const tl = scrollTimeline(sectionEl, { start: 'top 78%', end: 'bottom 28%', scrub: 0.6 });
		tween = tl;
		const D = 4;

		reasons.forEach((r, i) => {
			const t = 0.2 + i * 0.7;
			tl.to(barEls[i], { width: `${(r.weight / maxWeight) * 100}%`, duration: 0.5, ease: 'power2.out' }, t);
			tl.to(reasonEls[i], { opacity: 1, x: 0, duration: 0.5 }, t + 0.15);
		});
		tl.to(metersEl, { opacity: 1, y: 0, duration: 0.5 }, D - 0.4);
	});

	onDestroy(() => tween?.scrollTrigger?.kill());
</script>

<section bind:this={sectionEl} class="relative mx-auto max-w-5xl px-6 py-32">
	<div use:reveal={{ y: 24 }} class="mx-auto mb-16 max-w-2xl text-center">
		<div
			class="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-xl"
			style="background: color-mix(in oklch, var(--color-plum-400) 16%, transparent);"
		>
			<Sparkles size={20} style="color: var(--color-plum-400)" aria-hidden="true" />
		</div>
		<span class="text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
			05 · Explainable AI
		</span>
		<h2 class="mt-4 text-4xl font-semibold tracking-tight text-balance">Every verdict comes with a reason</h2>
		<p class="mt-3 text-base" style="color: var(--text-secondary);">
			Feature attributions are mapped to grounded, plain-language reasons — never a bare score.
		</p>
	</div>

	<div class="glass-panel mx-auto max-w-2xl rounded-2xl p-8">
		<div class="flex flex-col gap-5">
			{#each reasons as reason, i (reason.label)}
				<div>
					<div class="mb-1.5 flex items-center justify-between text-xs">
						<span class="font-medium" style="color: var(--text-primary);">{reason.label}</span>
						<span class="font-mono" style="color: var(--text-tertiary);">+{reason.weight.toFixed(2)}</span>
					</div>
					<div class="mb-2 h-1.5 overflow-hidden rounded-full" style="background: var(--surface-overlay);">
						<div bind:this={barEls[i]} class="h-full rounded-full" style="background: linear-gradient(90deg, var(--color-plum-500), var(--accent-secondary));"></div>
					</div>
					<p bind:this={reasonEls[i]} class="text-sm leading-relaxed" style="color: var(--text-secondary);">
						{reason.evidence}
					</p>
				</div>
			{/each}
		</div>

		<div bind:this={metersEl} class="mt-8 grid grid-cols-2 gap-3 border-t pt-6" style="border-color: var(--border-subtle);">
			<div class="glass-panel flex flex-col gap-1 rounded-xl p-4">
				<div class="flex items-center gap-1.5 text-xs" style="color: var(--text-tertiary);">
					<Gauge size={13} aria-hidden="true" /> Confidence
				</div>
				<span class="font-mono text-2xl font-semibold" style="color: var(--text-primary);">94%</span>
				<span class="text-[11px]" style="color: var(--text-tertiary);">How certain the model is</span>
			</div>
			<div class="glass-panel flex flex-col gap-1 rounded-xl p-4">
				<div class="flex items-center gap-1.5 text-xs" style="color: var(--color-risk-critical);">
					<ShieldX size={13} aria-hidden="true" /> Risk
				</div>
				<span class="font-mono text-2xl font-semibold" style="color: var(--color-risk-critical);">Critical</span>
				<span class="text-[11px]" style="color: var(--text-tertiary);">How dangerous this is for you</span>
			</div>
		</div>
		<p class="mt-3 text-xs leading-relaxed" style="color: var(--text-tertiary);">
			Confidence and risk are kept deliberately separate — a confident prediction about a
			catastrophic ask (like a credential request) still needs to read as critical, regardless of
			the probability attached to it.
		</p>
	</div>
</section>
