<script>
	import { onMount, onDestroy } from 'svelte';
	import { gsap, prefersReducedMotion } from '$lib/motion/gsap';
	import { scrollTimeline } from '$lib/motion/scroll';
	import { reveal } from '$lib/motion/actions';
	import Split from '@lucide/svelte/icons/split';

	const categories = [
		{ label: 'Job scam', value: 94, hero: true },
		{ label: 'OTP fraud', value: 3 },
		{ label: 'Banking', value: 1 },
		{ label: 'QR code', value: 0.8 },
		{ label: 'Investment', value: 0.6 },
		{ label: 'Lottery', value: 0.4 },
		{ label: 'Delivery', value: 0.2 }
	];

	/** @type {HTMLElement} */
	let sectionEl;
	/** @type {HTMLElement} */
	let stage1FillEl;
	/** @type {HTMLElement} */
	let stage1ValueEl;
	/** @type {HTMLElement[]} */
	let barEls = [];
	/** @type {HTMLElement[]} */
	let barValueEls = [];
	/** @type {HTMLElement} */
	let modelsEl;
	let tween;

	onMount(() => {
		if (prefersReducedMotion()) {
			gsap.set(stage1FillEl, { width: '94%' });
			gsap.set(barEls, { width: (i) => `${categories[i].value}%` });
			gsap.set([modelsEl], { opacity: 1, y: 0 });
			return;
		}

		gsap.set(stage1FillEl, { width: '0%' });
		gsap.set(barEls, { width: '0%' });
		gsap.set(modelsEl, { opacity: 0, y: 12 });

		const tl = scrollTimeline(sectionEl, { start: 'top 78%', end: 'bottom 25%', scrub: 0.6 });
		tween = tl;
		const D = 4;

		tl.to(stage1FillEl, { width: '94%', duration: 1, ease: 'power2.out' }, 0.1);
		categories.forEach((cat, i) => {
			tl.to(barEls[i], { width: `${cat.value}%`, duration: 0.5, ease: 'power2.out' }, 1.3 + i * 0.25);
		});
		tl.to(modelsEl, { opacity: 1, y: 0, duration: 0.5 }, D - 0.5);
	});

	onDestroy(() => tween?.scrollTrigger?.kill());
</script>

<section bind:this={sectionEl} class="relative mx-auto max-w-5xl px-6 py-32">
	<div use:reveal={{ y: 24 }} class="mx-auto mb-16 max-w-2xl text-center">
		<div
			class="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-xl"
			style="background: color-mix(in oklch, var(--color-plum-400) 18%, transparent);"
		>
			<Split size={20} style="color: var(--color-plum-400)" aria-hidden="true" />
		</div>
		<span class="text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
			04 · Machine learning
		</span>
		<h2 class="mt-4 text-4xl font-semibold tracking-tight text-balance">Two stages, not a single guess</h2>
		<p class="mt-3 text-base" style="color: var(--text-secondary);">
			First: is this fraudulent at all? Then, only if so: which of seven categories is it?
		</p>
	</div>

	<div class="glass-panel mx-auto max-w-2xl rounded-2xl p-8">
		<div class="mb-8">
			<div class="mb-2 flex items-center justify-between text-xs" style="color: var(--text-tertiary);">
				<span>Stage 1 · Fraudulent?</span>
				<span bind:this={stage1ValueEl} class="font-mono">94%</span>
			</div>
			<div class="h-2.5 overflow-hidden rounded-full" style="background: var(--surface-overlay);">
				<div bind:this={stage1FillEl} class="h-full rounded-full" style="background: linear-gradient(90deg, var(--color-risk-high), var(--color-risk-critical));"></div>
			</div>
		</div>

		<div class="mb-2 text-xs" style="color: var(--text-tertiary);">Stage 2 · Category</div>
		<div class="flex flex-col gap-2.5">
			{#each categories as cat, i (cat.label)}
				<div class="flex items-center gap-3">
					<span class="w-24 shrink-0 text-xs sm:w-28" style={`color: ${cat.hero ? 'var(--text-primary)' : 'var(--text-tertiary)'}; font-weight: ${cat.hero ? 600 : 400};`}>
						{cat.label}
					</span>
					<div class="h-2 flex-1 overflow-hidden rounded-full" style="background: var(--surface-overlay);">
						<div
							bind:this={barEls[i]}
							class="h-full rounded-full"
							style={cat.hero
								? 'background: linear-gradient(90deg, var(--color-plum-500), var(--accent-secondary)); box-shadow: var(--shadow-glow-plum);'
								: 'background: var(--border-strong);'}
						></div>
					</div>
					<span class="w-10 shrink-0 text-right font-mono text-xs" style={`color: ${cat.hero ? 'var(--text-primary)' : 'var(--text-tertiary)'};`}>
						{cat.value}%
					</span>
				</div>
			{/each}
		</div>

		<div bind:this={modelsEl} class="mt-8 flex flex-wrap items-center gap-2 border-t pt-6 text-xs" style="border-color: var(--border-subtle); color: var(--text-tertiary);">
			<span class="rounded-full border px-2.5 py-1" style="border-color: var(--border-default);">Random Forest</span>
			<span class="rounded-full border px-2.5 py-1" style="border-color: var(--border-default);">XGBoost</span>
			<span>— both trained per stage; the higher macro-F1 model is promoted.</span>
		</div>
	</div>
</section>
