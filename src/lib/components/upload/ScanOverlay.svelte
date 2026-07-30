<script>
	// Shows the actual uploaded screenshot with a scan-line sweep + targeting
	// brackets while analysis is in flight. Purely atmospheric — there's no
	// bounding-box data from the backend to highlight real detected regions,
	// so this never claims to point at anything specific, only that the
	// image is being examined. Pure CSS animation (no GSAP needed for a
	// self-contained loop like this), which also means it's automatically
	// neutralized by app.css's global prefers-reduced-motion override.
	let { src = '', class: className = '' } = $props();
</script>

<div class="relative mx-auto aspect-video w-full max-w-md overflow-hidden rounded-2xl {className}" style="background: #05050a;">
	<img src={src} alt="" class="absolute inset-0 h-full w-full object-contain" style="filter: brightness(0.5) saturate(0.9);" />

	<div class="scan-grid pointer-events-none absolute inset-0"></div>

	<div class="scan-line pointer-events-none absolute inset-x-0 h-16"></div>

	<div class="pointer-events-none absolute inset-3 corner corner-tl"></div>
	<div class="pointer-events-none absolute inset-3 corner corner-tr"></div>
	<div class="pointer-events-none absolute inset-3 corner corner-bl"></div>
	<div class="pointer-events-none absolute inset-3 corner corner-br"></div>

	<div
		class="pointer-events-none absolute inset-0"
		style="background: linear-gradient(180deg, transparent 60%, rgba(5,5,10,0.85) 100%);"
	></div>
</div>

<style>
	.scan-line {
		top: -20%;
		background: linear-gradient(
			180deg,
			transparent 0%,
			color-mix(in oklch, var(--accent-secondary) 55%, transparent) 45%,
			color-mix(in oklch, var(--accent-secondary) 85%, white) 50%,
			color-mix(in oklch, var(--accent-secondary) 55%, transparent) 55%,
			transparent 100%
		);
		box-shadow: 0 0 24px 4px color-mix(in oklch, var(--accent-secondary) 55%, transparent);
		animation: scan-sweep 2.6s ease-in-out infinite alternate;
	}

	@keyframes scan-sweep {
		from {
			top: -20%;
		}
		to {
			top: 100%;
		}
	}

	.scan-grid {
		background-image: repeating-linear-gradient(
			0deg,
			color-mix(in oklch, var(--accent-secondary) 18%, transparent) 0px,
			transparent 1px,
			transparent 5px
		);
		opacity: 0.35;
		mix-blend-mode: screen;
	}

	.corner {
		width: 22px;
		height: 22px;
		border-color: var(--accent-primary-strong);
		opacity: 0.9;
		animation: corner-pulse 2.6s ease-in-out infinite;
	}
	.corner-tl {
		border-top: 2px solid;
		border-left: 2px solid;
		border-radius: 6px 0 0 0;
	}
	.corner-tr {
		right: 0.75rem;
		left: auto;
		border-top: 2px solid;
		border-right: 2px solid;
		border-radius: 0 6px 0 0;
	}
	.corner-bl {
		bottom: 0.75rem;
		top: auto;
		border-bottom: 2px solid;
		border-left: 2px solid;
		border-radius: 0 0 0 6px;
	}
	.corner-br {
		right: 0.75rem;
		left: auto;
		bottom: 0.75rem;
		top: auto;
		border-bottom: 2px solid;
		border-right: 2px solid;
		border-radius: 0 0 6px 0;
	}

	@keyframes corner-pulse {
		0%,
		100% {
			opacity: 0.55;
		}
		50% {
			opacity: 1;
		}
	}
</style>
