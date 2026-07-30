<script>
	import { onMount, onDestroy } from 'svelte';
	import { gsap, prefersReducedMotion } from '$lib/motion/gsap';
	import { scrollTimeline } from '$lib/motion/scroll';
	import { reveal } from '$lib/motion/actions';
	import PhoneMockup from '$lib/components/pipeline/PhoneMockup.svelte';
	import ScanEye from '@lucide/svelte/icons/scan-eye';
	import QrCode from '@lucide/svelte/icons/qr-code';
	import Building2 from '@lucide/svelte/icons/building-2';
	import TriangleAlert from '@lucide/svelte/icons/triangle-alert';
	import MoveRight from '@lucide/svelte/icons/move-right';

	/** @type {HTMLElement} */
	let phoneEl;
	/** @type {HTMLElement} */
	let qrBoxEl;
	/** @type {HTMLElement} */
	let qrDecodingEl;
	/** @type {HTMLElement} */
	let qrResultEl;
	/** @type {HTMLElement} */
	let brandBoxEl;
	/** @type {HTMLElement} */
	let mismatchEl;
	/** @type {HTMLElement} */
	let flagsEl;
	let tween;

	onMount(() => {
		const finalState = () => {
			gsap.set([qrBoxEl, brandBoxEl, mismatchEl, flagsEl], { opacity: 1, y: 0, scale: 1 });
			gsap.set(qrDecodingEl, { opacity: 0 });
			gsap.set(qrResultEl, { opacity: 1 });
		};

		if (prefersReducedMotion()) {
			finalState();
			return;
		}

		gsap.set([qrBoxEl, brandBoxEl], { opacity: 0, scale: 0.94 });
		gsap.set([mismatchEl, flagsEl], { opacity: 0, y: 10 });
		gsap.set(qrDecodingEl, { opacity: 1 });
		gsap.set(qrResultEl, { opacity: 0 });

		const tl = scrollTimeline(phoneEl, { start: 'top 78%', end: 'bottom 40%', scrub: 0.6 });
		tween = tl;
		const D = 4;
		tl.to(qrBoxEl, { opacity: 1, scale: 1, duration: 0.4 }, 0.3);
		tl.to(qrDecodingEl, { opacity: 0, duration: 0.3 }, 1.1);
		tl.to(qrResultEl, { opacity: 1, duration: 0.3 }, 1.15);
		tl.to(brandBoxEl, { opacity: 1, scale: 1, duration: 0.4 }, 1.7);
		tl.to(mismatchEl, { opacity: 1, y: 0, duration: 0.4 }, 2.5);
		tl.to(flagsEl, { opacity: 1, y: 0, duration: 0.4 }, 3.1);
	});

	onDestroy(() => tween?.scrollTrigger?.kill());
</script>

<section class="relative mx-auto max-w-6xl px-6 py-32">
	<div class="grid gap-16 lg:grid-cols-2 lg:items-center">
		<div bind:this={phoneEl} class="relative lg:order-1">
			<PhoneMockup>
				{#snippet children()}
					<div class="flex flex-col gap-4">
						<div class="max-w-[85%] rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm leading-relaxed" style="background: var(--surface-overlay); color: var(--text-primary);">
							Scan to confirm your delivery has been rescheduled.
						</div>

						<div class="relative flex items-center gap-3">
							<div
								bind:this={qrBoxEl}
								class="relative flex h-20 w-20 items-center justify-center rounded-lg border-2 border-dashed"
								style="border-color: var(--accent-secondary);"
							>
								<QrCode size={40} style="color: var(--text-primary)" aria-hidden="true" />
							</div>
							<div class="relative h-10 flex-1">
								<span bind:this={qrDecodingEl} class="absolute font-mono text-xs" style="color: var(--text-tertiary);">
									Decoding payload…
								</span>
								<span bind:this={qrResultEl} class="absolute font-mono text-xs" style="color: var(--color-risk-medium);">
									UPI payment request · ₹2,000
								</span>
							</div>
						</div>

						<div
							bind:this={brandBoxEl}
							class="flex items-center gap-2 rounded-lg border-2 border-dashed px-3 py-2"
							style="border-color: var(--color-plum-400);"
						>
							<Building2 size={16} style="color: var(--text-primary)" aria-hidden="true" />
							<span class="text-xs" style="color: var(--text-secondary);">Claims to be: <strong style="color: var(--text-primary);">SBI Bank</strong></span>
						</div>

						<div bind:this={mismatchEl} class="flex flex-wrap items-center gap-2 text-xs">
							<span class="rounded-full px-2.5 py-1 font-mono" style="background: color-mix(in oklch, var(--color-risk-high) 18%, transparent); color: var(--color-risk-high);">
								sbi-secure-payments.xyz
							</span>
							<MoveRight size={13} style="color: var(--color-risk-high)" aria-hidden="true" />
							<span class="flex items-center gap-1" style="color: var(--color-risk-high);">
								<TriangleAlert size={13} aria-hidden="true" /> brand mismatch
							</span>
						</div>
					</div>
				{/snippet}
			</PhoneMockup>

			<div bind:this={flagsEl} class="mt-4 flex flex-wrap gap-2 font-mono text-[11px]" style="color: var(--text-tertiary);">
				<span class="glass-panel rounded-full px-3 py-1.5">qr_payment_intent: true</span>
				<span class="glass-panel rounded-full px-3 py-1.5">impersonation_mismatch: true</span>
			</div>
		</div>

		<div use:reveal={{ y: 24 }} class="flex flex-col gap-5 lg:order-2">
			<div
				class="flex h-11 w-11 items-center justify-center rounded-xl"
				style="background: color-mix(in oklch, var(--accent-secondary) 18%, transparent);"
			>
				<ScanEye size={20} style="color: var(--accent-secondary)" aria-hidden="true" />
			</div>
			<span class="text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
				02 · Computer vision
			</span>
			<h2 class="text-4xl font-semibold tracking-tight text-balance">The same image, read for what text can't show</h2>
			<p class="text-base leading-relaxed" style="color: var(--text-secondary);">
				QR payloads are decoded and risk-scored — a code that asks you to pay is a very different
				signal from one that asks you to receive. Logos aren't just detected; they're checked
				against the links and IDs actually present in the message.
			</p>
			<ul class="mt-2 flex flex-col gap-3 text-sm" style="color: var(--text-secondary);">
				<li class="flex items-start gap-2">
					<span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style="background: var(--accent-secondary);"></span>
					A logo alone means little — legitimate messages have logos too.
				</li>
				<li class="flex items-start gap-2">
					<span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style="background: var(--accent-secondary);"></span>
					A claimed brand whose links point elsewhere is the actual signal.
				</li>
			</ul>
		</div>
	</div>
</section>
