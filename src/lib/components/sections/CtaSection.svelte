<script>
	import { reveal } from '$lib/motion/actions';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
</script>

<section class="relative isolate overflow-hidden px-6 py-40">
	<div class="pointer-events-none absolute inset-0 -z-10">
		<div class="absolute inset-0 bg-grid opacity-20"></div>
		<div
			class="absolute top-1/2 left-1/2 h-[36rem] w-[36rem] -translate-x-1/2 -translate-y-1/2 rounded-full blur-3xl"
			style="background: radial-gradient(circle, var(--accent-primary) 0%, transparent 70%); opacity: 0.14;"
		></div>
	</div>

	<div use:reveal={{ y: 24 }} class="mx-auto flex max-w-2xl flex-col items-center gap-6 text-center">
		<span
			class="rounded-full border px-3 py-1 text-xs font-medium tracking-wide uppercase"
			style="border-color: var(--border-default); color: var(--text-tertiary);"
		>
			Stop guessing. Start checking.
		</span>

		<h2 class="text-4xl leading-tight font-semibold tracking-tight text-balance sm:text-5xl">
			If you have a <span class="text-gradient-brand">screenshot</span>, you already have enough.
		</h2>

		<p class="max-w-lg text-lg" style="color: var(--text-secondary);">
			No copying text, no pasting links. Upload the screenshot as it is and get a verdict you can
			understand — and act on — in seconds.
		</p>

		<div class="flex flex-wrap items-center justify-center gap-3 pt-2">
			<a
				href="/analyze"
				class="group flex items-center gap-2 rounded-lg px-6 py-3 text-sm font-medium text-white transition-transform duration-300 ease-out-expo hover:-translate-y-0.5"
				style="background: linear-gradient(120deg, var(--color-plum-500), var(--color-plum-600)); box-shadow: var(--shadow-glow-plum);"
			>
				Analyze a screenshot
				<ArrowRight size={16} class="transition-transform duration-300 group-hover:translate-x-1" />
			</a>
			<a
				href="#how-it-works"
				class="rounded-lg border px-6 py-3 text-sm font-medium transition-colors duration-300"
				style="border-color: var(--border-default); color: var(--text-primary);"
			>
				Revisit how it works
			</a>
		</div>

		<dl class="flex flex-wrap justify-center gap-8 pt-10 font-mono text-sm" style="color: var(--text-tertiary);">
			<div>
				<dt class="text-2xl font-semibold" style="color: var(--text-primary);">7</dt>
				<dd>scam categories</dd>
			</div>
			<div>
				<dt class="text-2xl font-semibold" style="color: var(--text-primary);">5</dt>
				<dd>platforms covered</dd>
			</div>
			<div>
				<dt class="text-2xl font-semibold" style="color: var(--text-primary);">&lt;8s</dt>
				<dd>p95 analysis time</dd>
			</div>
		</dl>

		<p class="max-w-md pt-8 text-xs" style="color: var(--text-tertiary);">
			A research project exploring screenshot-native scam detection across WhatsApp, Telegram, SMS,
			Instagram, and email — with a fused text-and-visual pipeline and explainable output.
		</p>
	</div>
</section>
