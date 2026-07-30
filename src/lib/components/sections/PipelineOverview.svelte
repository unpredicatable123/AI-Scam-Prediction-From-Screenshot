<script>
	import { onMount, onDestroy } from 'svelte';
	import { gsap, prefersReducedMotion } from '$lib/motion/gsap';
	import { scrollTimeline } from '$lib/motion/scroll';
	import UploadCloud from '@lucide/svelte/icons/upload-cloud';
	import SlidersHorizontal from '@lucide/svelte/icons/sliders-horizontal';
	import ScanText from '@lucide/svelte/icons/scan-text';
	import ScanEye from '@lucide/svelte/icons/scan-eye';
	import GitMerge from '@lucide/svelte/icons/git-merge';
	import Cpu from '@lucide/svelte/icons/cpu';
	import Sparkles from '@lucide/svelte/icons/sparkles';

	const nodes = [
		{ key: 'upload', label: 'Upload', sub: 'Screenshot received', icon: UploadCloud, x: 0, lane: 'center' },
		{ key: 'preprocess', label: 'Preprocess', sub: 'Denoise · deskew · contrast', icon: SlidersHorizontal, x: 0.2, lane: 'center' },
		{ key: 'text', label: 'OCR + NLP', sub: 'Text branch', icon: ScanText, x: 0.44, lane: 'top' },
		{ key: 'visual', label: 'Visual analysis', sub: 'QR · logo · layout', icon: ScanEye, x: 0.44, lane: 'bottom' },
		{ key: 'fusion', label: 'Feature fusion', sub: 'One feature vector', icon: GitMerge, x: 0.66, lane: 'center' },
		{ key: 'classify', label: 'Classification', sub: 'Random Forest · XGBoost', icon: Cpu, x: 0.84, lane: 'center' },
		{ key: 'explain', label: 'Explainable output', sub: 'Reasons · risk · actions', icon: Sparkles, x: 1, lane: 'center' }
	];

	/** @type {HTMLElement} */
	let sectionEl;
	/** @type {HTMLElement} */
	let dotEl;
	/** @type {HTMLElement[]} */
	let desktopCardEls = [];
	/** @type {HTMLElement[]} */
	let mobileCardEls = [];
	let mm;

	onMount(() => {
		mm = gsap.matchMedia();

		mm.add('(min-width: 1024px)', () => {
			if (prefersReducedMotion()) {
				gsap.set(dotEl, { left: '100%' });
				gsap.set(desktopCardEls, { opacity: 1, y: 0, scale: 1 });
				return;
			}
			gsap.set(desktopCardEls, { opacity: 0, scale: 0.92 });
			gsap.set(dotEl, { left: '0%' });

			const tl = scrollTimeline(sectionEl, { start: 'top 60%', end: 'bottom 25%', scrub: 0.6 });
			const D = 4;
			tl.to(dotEl, { left: '100%', duration: D, ease: 'none' }, 0);
			nodes.forEach((n, i) => {
				tl.to(desktopCardEls[i], { opacity: 1, scale: 1, duration: 0.35, ease: 'power2.out' }, n.x * D);
			});

			return () => tl.scrollTrigger?.kill();
		});

		mm.add('(max-width: 1023px)', () => {
			if (prefersReducedMotion()) {
				gsap.set(mobileCardEls, { opacity: 1, y: 0 });
				return;
			}
			gsap.set(mobileCardEls, { opacity: 0, y: 18 });
			const triggers = mobileCardEls.map((el) =>
				gsap.to(el, {
					opacity: 1,
					y: 0,
					duration: 0.7,
					ease: 'power3.out',
					scrollTrigger: { trigger: el, start: 'top 90%', once: true }
				})
			);
			return () => triggers.forEach((t) => t.scrollTrigger?.kill());
		});
	});

	onDestroy(() => mm?.revert());
</script>

<section id="how-it-works" bind:this={sectionEl} class="relative mx-auto max-w-6xl px-6 py-32">
	<div class="mx-auto mb-20 max-w-2xl text-center">
		<span
			class="rounded-full border px-3 py-1 text-xs font-medium tracking-wide uppercase"
			style="border-color: var(--border-default); color: var(--text-tertiary);"
		>
			The pipeline
		</span>
		<h2 class="mt-4 text-4xl font-semibold tracking-tight text-balance">How the AI detects a scam</h2>
		<p class="mt-3 text-base" style="color: var(--text-secondary);">
			Text and visual analysis run concurrently on the same image, then fuse into one decision.
		</p>
	</div>

	<!-- Desktop: scroll-scrubbed flow -->
	<div class="relative hidden h-72 lg:block">
		<div class="absolute top-1/2 right-0 left-0 h-px" style="background: var(--border-default);"></div>
		<div
			bind:this={dotEl}
			class="absolute top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full"
			style="background: var(--accent-secondary); box-shadow: var(--shadow-glow-lime);"
			aria-hidden="true"
		></div>

		{#each nodes as node, i (node.key)}
			{@const top = node.lane === 'top' ? '4%' : node.lane === 'bottom' ? '68%' : '50%'}
			<div
				bind:this={desktopCardEls[i]}
				class="glass-panel absolute flex w-36 -translate-x-1/2 flex-col items-center gap-2 rounded-xl px-3 py-4 text-center"
				style={`left: ${node.x * 100}%; top: ${top}; ${node.lane === 'center' ? 'transform: translate(-50%, -50%);' : 'transform: translateX(-50%);'}`}
			>
				<div
					class="flex h-9 w-9 items-center justify-center rounded-lg"
					style="background: color-mix(in oklch, var(--accent-secondary) 16%, transparent);"
				>
					<node.icon size={17} style="color: var(--accent-secondary)" aria-hidden="true" />
				</div>
				<span class="text-xs font-medium" style="color: var(--text-primary);">{node.label}</span>
				<span class="text-[10px] leading-tight" style="color: var(--text-tertiary);">{node.sub}</span>
			</div>
		{/each}
	</div>

	<!-- Mobile: vertical stacked list -->
	<div class="flex flex-col gap-3 lg:hidden">
		{#each nodes as node, i (node.key)}
			<div bind:this={mobileCardEls[i]} class="glass-panel flex items-center gap-4 rounded-xl px-4 py-3.5">
				<div
					class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
					style="background: color-mix(in oklch, var(--accent-secondary) 16%, transparent);"
				>
					<node.icon size={17} style="color: var(--accent-secondary)" aria-hidden="true" />
				</div>
				<div class="flex flex-col">
					<span class="text-sm font-medium" style="color: var(--text-primary);">{node.label}</span>
					<span class="text-xs" style="color: var(--text-tertiary);">{node.sub}</span>
				</div>
			</div>
		{/each}
	</div>
</section>
