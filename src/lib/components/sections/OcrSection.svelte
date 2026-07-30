<script>
	import { onMount, onDestroy } from 'svelte';
	import { gsap, prefersReducedMotion } from '$lib/motion/gsap';
	import { scrollTimeline } from '$lib/motion/scroll';
	import { reveal } from '$lib/motion/actions';
	import PhoneMockup from '$lib/components/pipeline/PhoneMockup.svelte';
	import ScanText from '@lucide/svelte/icons/scan-text';
	import Link2 from '@lucide/svelte/icons/link-2';
	import DollarSign from '@lucide/svelte/icons/dollar-sign';
	import Phone from '@lucide/svelte/icons/phone';

	const lines = [
		{ parts: [{ t: 'text', v: "Congratulations! You've been shortlisted for a Work-From-Home position." }] },
		{
			parts: [
				{ t: 'text', v: 'Registration fee of ' },
				{ t: 'badge', v: '$250', conf: '98%', tone: 'high' },
				{ t: 'text', v: ' required to confirm your slot.' }
			]
		},
		{
			parts: [
				{ t: 'text', v: 'Pay immediately via ' },
				{ t: 'badge', v: 'secure-hr-portal.info', conf: '62%', tone: 'low' },
				{ t: 'text', v: ' to avoid losing this offer.' }
			]
		},
		{ parts: [{ t: 'text', v: 'Reply with your bank details to proceed.' }] }
	];

	const entities = [
		{ icon: Link2, label: 'URL detected' },
		{ icon: DollarSign, label: 'Amount: $250' },
		{ icon: Phone, label: 'Contact-shift request' }
	];

	/** @type {HTMLElement} */
	let phoneEl;
	/** @type {HTMLElement} */
	let scanLineEl;
	/** @type {HTMLElement[]} */
	let lineEls = [];
	/** @type {HTMLElement} */
	let entitiesEl;
	let tween;

	onMount(() => {
		if (prefersReducedMotion()) {
			gsap.set(scanLineEl, { top: '100%', opacity: 0 });
			gsap.set(lineEls, { opacity: 1, filter: 'blur(0px)' });
			gsap.set(entitiesEl, { opacity: 1, y: 0 });
			return;
		}

		gsap.set(lineEls, { opacity: 0.08, filter: 'blur(4px)' });
		gsap.set(entitiesEl, { opacity: 0, y: 16 });
		gsap.set(scanLineEl, { top: '0%' });

		const tl = scrollTimeline(phoneEl, { start: 'top 78%', end: 'bottom 45%', scrub: 0.6 });
		tween = tl;
		const D = 4;
		tl.to(scanLineEl, { top: '92%', duration: D, ease: 'none' }, 0);
		lines.forEach((_, i) => {
			tl.to(lineEls[i], { opacity: 1, filter: 'blur(0px)', duration: 0.4 }, (i + 0.4) * (D / lines.length));
		});
		tl.to(entitiesEl, { opacity: 1, y: 0, duration: 0.5 }, D - 0.4);
		tl.to(scanLineEl, { opacity: 0, duration: 0.3 }, D - 0.2);
	});

	onDestroy(() => tween?.scrollTrigger?.kill());
</script>

<section class="relative mx-auto max-w-6xl px-6 py-32">
	<div class="grid gap-16 lg:grid-cols-2 lg:items-center">
		<div use:reveal={{ y: 24 }} class="flex flex-col gap-5">
			<div
				class="flex h-11 w-11 items-center justify-center rounded-xl"
				style="background: color-mix(in oklch, var(--accent-secondary) 16%, transparent);"
			>
				<ScanText size={20} style="color: var(--accent-secondary)" aria-hidden="true" />
			</div>
			<span class="text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
				01 · Optical character recognition
			</span>
			<h2 class="text-4xl font-semibold tracking-tight text-balance">OCR reads what's actually in the image</h2>
			<p class="text-base leading-relaxed" style="color: var(--text-secondary);">
				Each message bubble is processed on its own — cleaner backgrounds, natural reading order,
				and per-token confidence instead of one blended guess for the whole screenshot.
			</p>
			<ul class="mt-2 flex flex-col gap-3 text-sm" style="color: var(--text-secondary);">
				<li class="flex items-start gap-2">
					<span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style="background: var(--accent-secondary);"></span>
					Uncertain text is flagged, not silently guessed — a 62% token stays visibly uncertain.
				</li>
				<li class="flex items-start gap-2">
					<span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style="background: var(--accent-secondary);"></span>
					URLs, amounts, and contact requests are extracted as structured entities, not just text.
				</li>
			</ul>
		</div>

		<div bind:this={phoneEl} class="relative">
			<PhoneMockup>
				{#snippet children()}
					<div class="flex flex-col gap-3">
						<div class="max-w-[85%] rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm leading-relaxed" style="background: var(--surface-overlay); color: var(--text-primary);">
							{#each lines as line, i (i)}
								<p bind:this={lineEls[i]} class="mb-2 last:mb-0">
									{#each line.parts as part}
										{#if part.t === 'text'}{part.v}{:else}<span
												class="rounded px-1 py-0.5 font-mono text-[13px]"
												style={`border-bottom: 1.5px dashed ${part.tone === 'low' ? 'var(--color-risk-medium)' : 'var(--accent-secondary)'};`}
												>{part.v}</span
											><sup
												class="ml-0.5 font-mono text-[9px]"
												style={`color: ${part.tone === 'low' ? 'var(--color-risk-medium)' : 'var(--accent-secondary)'};`}
												>{part.conf}</sup
											>{/if}
									{/each}
								</p>
							{/each}
						</div>

						<div bind:this={entitiesEl} class="mt-2 flex flex-wrap gap-2">
							{#each entities as entity (entity.label)}
								<span
									class="glass-panel flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs"
									style="color: var(--text-secondary);"
								>
									<entity.icon size={12} style="color: var(--accent-secondary)" aria-hidden="true" />
									{entity.label}
								</span>
							{/each}
						</div>
					</div>
				{/snippet}
				{#snippet overlay()}
					<div
						bind:this={scanLineEl}
						class="absolute right-0 left-0 h-px"
						style="background: linear-gradient(90deg, transparent, var(--accent-secondary), transparent); box-shadow: 0 0 12px 1px var(--accent-secondary);"
					></div>
				{/snippet}
			</PhoneMockup>
		</div>
	</div>
</section>
