<script>
	import { reveal } from '$lib/motion/actions';
	import ImageOff from '@lucide/svelte/icons/image-off';
	import LayersIcon from '@lucide/svelte/icons/layers';
	import EyeOff from '@lucide/svelte/icons/eye-off';

	const points = [
		{
			icon: ImageOff,
			title: 'The evidence is a picture, not text',
			body: 'A forwarded chat, a job offer, an OTP request — victims have a screenshot, not copyable text. Every existing scam checker asks for text or a link, so the screenshot never gets analyzed.'
		},
		{
			icon: LayersIcon,
			title: 'Detection is split across narrow verticals',
			body: 'SMS-only spam filters. Single-domain job-scam detectors. Webpage phishing scanners that read browser screenshots, not chat UIs. None of them fuse text and visuals for messaging apps.'
		},
		{
			icon: EyeOff,
			title: 'A bare probability changes nothing',
			body: '"85% spam" does not change behaviour. A grounded reason — what was asked, why it’s dangerous, what to do next — is what actually stops someone from paying a scammer.'
		}
	];
</script>

<section id="problem" class="relative mx-auto max-w-6xl px-6 py-32">
	<div use:reveal={{ y: 24, start: 'top 92%' }} class="mx-auto mb-16 max-w-2xl text-center">
		<span
			class="rounded-full border px-3 py-1 text-xs font-medium tracking-wide uppercase"
			style="border-color: var(--border-default); color: var(--text-tertiary);"
		>
			The gap
		</span>
		<h2 class="mt-4 text-4xl font-semibold tracking-tight text-balance">
			Scam detection was built for text. Fraud arrives as a picture.
		</h2>
	</div>

	<div class="grid gap-5 md:grid-cols-3">
		{#each points as point, i (point.title)}
			<div
				use:reveal={{ y: 32, delay: i * 0.12 }}
				class="glass-panel flex flex-col gap-4 rounded-2xl p-7"
			>
				<div
					class="flex h-11 w-11 items-center justify-center rounded-xl"
					style="background: color-mix(in oklch, var(--accent-secondary) 16%, transparent);"
				>
					<point.icon size={20} style="color: var(--accent-secondary)" aria-hidden="true" />
				</div>
				<h3 class="text-lg font-medium" style="color: var(--text-primary);">{point.title}</h3>
				<p class="text-sm leading-relaxed" style="color: var(--text-secondary);">{point.body}</p>
			</div>
		{/each}
	</div>
</section>
