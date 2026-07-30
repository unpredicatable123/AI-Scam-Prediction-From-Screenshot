<script>
	import { reveal } from '$lib/motion/actions';
	import ShieldCheck from '@lucide/svelte/icons/shield-check';

	const year = new Date().getFullYear();

	const linkStyle =
		'color: var(--text-secondary); text-decoration-line: underline; text-decoration-color: transparent; text-underline-offset: 3px; transition: text-decoration-color 0.2s ease, color 0.2s ease;';
	function onLinkEnter(e) {
		e.currentTarget.style.textDecorationColor = 'var(--accent-secondary)';
		e.currentTarget.style.color = 'var(--text-primary)';
	}
	function onLinkLeave(e) {
		e.currentTarget.style.textDecorationColor = 'transparent';
		e.currentTarget.style.color = 'var(--text-secondary)';
	}
</script>

<footer
	use:reveal={{ y: 16 }}
	class="border-t px-6 py-12"
	style="border-color: var(--border-subtle); background: color-mix(in oklch, var(--surface-raised) 40%, transparent);"
>
	<div class="mx-auto flex max-w-7xl flex-col gap-10 sm:flex-row sm:items-start sm:justify-between">
		<div class="flex max-w-xs flex-col gap-3">
			<a href="/" class="flex items-center gap-2">
				<div
					class="flex h-7 w-7 items-center justify-center rounded-lg"
					style="background: color-mix(in oklch, var(--accent-secondary) 16%, transparent);"
				>
					<ShieldCheck size={15} style="color: var(--accent-secondary)" aria-hidden="true" />
				</div>
				<span class="text-sm font-semibold" style="color: var(--text-primary);">Scam Detector</span>
			</a>
			<p class="text-xs leading-relaxed" style="color: var(--text-tertiary);">
				A research project detecting scams directly from messaging-app screenshots using OCR,
				NLP, computer vision, and explainable AI.
			</p>
		</div>

		<div class="flex gap-12">
			<div class="flex flex-col gap-2.5">
				<span class="text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">Product</span>
				<a href="#how-it-works" class="w-fit text-sm" style={linkStyle} onmouseenter={onLinkEnter} onmouseleave={onLinkLeave}>
					How it works
				</a>
				<a href="/analyze" class="w-fit text-sm" style={linkStyle} onmouseenter={onLinkEnter} onmouseleave={onLinkLeave}>
					Analyze a screenshot
				</a>
			</div>
			<div class="flex flex-col gap-2.5">
				<span class="text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">Coverage</span>
				<span class="text-sm" style="color: var(--text-secondary);">WhatsApp · Telegram · SMS</span>
				<span class="text-sm" style="color: var(--text-secondary);">Instagram · Email</span>
			</div>
		</div>
	</div>

	<div
		class="mx-auto mt-10 flex max-w-7xl flex-col gap-2 border-t pt-6 text-xs sm:flex-row sm:items-center sm:justify-between"
		style="border-color: var(--border-subtle); color: var(--text-tertiary);"
	>
		<span>© {year} — a research project, not a substitute for professional or legal advice.</span>
		<span class="font-mono" style="color: var(--text-tertiary);">Local-first · Model v1 · No data stored</span>
	</div>
</footer>
