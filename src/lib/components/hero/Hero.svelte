<script>
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { reveal } from '$lib/motion/actions';
	import { prefersReducedMotion } from '$lib/motion/gsap';
	import { scrollTimeline } from '$lib/motion/scroll';
	import { magnetic } from '$lib/motion/magnetic';
	import HeroDemo from './HeroDemo.svelte';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';

	/** @type {HTMLElement} */
	let sectionEl;
	/** @type {HTMLElement} */
	let demoWrapEl;
	let tiltRaf;
	let handoffTween;
	let onMove;

	onMount(() => {
		// Pointer tilt on the demo panel — cheap CSS transform, communicating
		// the same "responsive, alive" quality the old WebGL parallax gave
		// without a render loop behind it.
		if (!prefersReducedMotion() && window.matchMedia('(pointer: fine)').matches) {
			onMove = (e) => {
				cancelAnimationFrame(tiltRaf);
				tiltRaf = requestAnimationFrame(() => {
					const rect = sectionEl.getBoundingClientRect();
					const nx = (e.clientX - rect.left) / rect.width - 0.5;
					const ny = (e.clientY - rect.top) / rect.height - 0.5;
					if (demoWrapEl) {
						demoWrapEl.style.transform = `perspective(1200px) rotateY(${nx * 6}deg) rotateX(${-ny * 6}deg)`;
					}
				});
			};
			sectionEl.addEventListener('pointermove', onMove, { passive: true });
		}

		// Scroll handoff into ProblemStatement — the demo settles and fades
		// rather than cutting hard as the next section arrives.
		const tl = scrollTimeline(sectionEl, { start: 'bottom 95%', end: 'bottom 35%', scrub: 0.6 });
		if (tl && demoWrapEl) {
			handoffTween = tl.to(demoWrapEl, { opacity: 0.25, scale: 0.94, y: -16, ease: 'none' }, 0);
		}
	});

	onDestroy(() => {
		// onDestroy fires during SSR teardown too (unlike onMount, which never
		// runs server-side) — cancelAnimationFrame/removeEventListener are
		// browser-only globals and crash the whole page render without this guard.
		if (!browser) return;
		cancelAnimationFrame(tiltRaf);
		if (onMove) sectionEl?.removeEventListener('pointermove', onMove);
		handoffTween?.scrollTrigger?.kill();
	});
</script>

<section bind:this={sectionEl} class="relative isolate flex min-h-svh items-center overflow-hidden pt-20">
	<!-- Static poster layer — this is the LCP content; renders instantly, no JS required. -->
	<div class="pointer-events-none absolute inset-0 -z-20">
		<div class="absolute inset-0 bg-grid opacity-30"></div>
		<div
			class="absolute top-1/2 -right-40 h-184 w-184 -translate-y-1/2 rounded-full blur-3xl"
			style="background: radial-gradient(circle, var(--accent-secondary) 0%, transparent 70%); opacity: 0.16;"
		></div>
		<div
			class="absolute top-1/3 left-0 h-120 w-120 -translate-x-1/2 rounded-full blur-3xl"
			style="background: radial-gradient(circle, var(--accent-primary) 0%, transparent 70%); opacity: 0.12;"
		></div>
		<div
			class="absolute inset-0"
			style="background: linear-gradient(180deg, transparent 55%, var(--surface-canvas) 96%);"
		></div>
	</div>

	<div class="mx-auto grid w-full max-w-7xl gap-10 px-6 lg:grid-cols-2 lg:items-center lg:gap-4">
		<div class="flex flex-col items-start gap-5" use:reveal={{ y: 28 }}>
			<span
				class="rounded-full border px-3 py-1 text-xs font-medium tracking-wide uppercase"
				style="border-color: var(--border-default); color: var(--text-tertiary);"
			>
				AI-powered detection
			</span>

			<h1 class="text-5xl leading-[1.05] font-semibold tracking-tight text-balance sm:text-6xl">
				Screenshot in. <span class="text-gradient-brand">Scam verdict</span> out.
			</h1>

			<p class="max-w-md text-lg" style="color: var(--text-secondary);">
				Powered by OCR, computer vision, and explainable AI.
			</p>

			<div class="flex flex-wrap items-center gap-3 pt-2">
				<a
					href="/analyze"
					use:magnetic
					class="group flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium text-white"
					style="background: linear-gradient(120deg, var(--color-plum-500), var(--color-plum-600)); box-shadow: var(--shadow-glow-plum);"
				>
					Analyze a screenshot
					<ArrowRight size={16} class="transition-transform duration-300 group-hover:translate-x-1" />
				</a>
				<a
					href="#how-it-works"
					use:magnetic={{ strength: 0.2 }}
					class="rounded-lg border px-5 py-2.5 text-sm font-medium transition-colors duration-300"
					style="border-color: var(--border-default); color: var(--text-primary);"
				>
					See how it works
				</a>
			</div>
		</div>

		<div bind:this={demoWrapEl} style="will-change: transform;">
			<HeroDemo />
		</div>
	</div>

	<a
		href="#problem"
		use:reveal={{ delay: 0.6 }}
		class="absolute bottom-8 left-1/2 flex -translate-x-1/2 flex-col items-center gap-1 text-xs"
		style="color: var(--text-tertiary);"
	>
		Scroll to see how it works
		<ChevronDown size={16} class="animate-bounce" style="animation-duration: 2s;" />
	</a>
</section>
