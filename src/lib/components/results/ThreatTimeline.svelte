<script>
	import { scale, fade } from 'svelte/transition';
	import { cn } from '$lib/utils/cn';
	import { prefersReducedMotion } from '$lib/motion/actions';
	import UploadCloud from '@lucide/svelte/icons/upload-cloud';
	import ScanText from '@lucide/svelte/icons/scan-text';
	import Type from '@lucide/svelte/icons/type';
	import ScanEye from '@lucide/svelte/icons/scan-eye';
	import GitMerge from '@lucide/svelte/icons/git-merge';
	import Cpu from '@lucide/svelte/icons/cpu';
	import Sparkles from '@lucide/svelte/icons/sparkles';
	import FileCheck from '@lucide/svelte/icons/file-check';
	import Clock from '@lucide/svelte/icons/clock';

	// One classifier runs per prediction (whichever was promoted at training
	// time — see ml/src/training/train.py), not "Random Forest then XGBoost"
	// as sequential steps. Timings map 1:1 to apps/ai-service/app/pipeline.py's
	// real `timings` dict; steps with no independent timer (upload, fusion,
	// report assembly) show no fabricated duration.
	let { timings = {}, modelName = 'XGBoost', class: className = '' } = $props();

	const STAGES = $derived([
		{ key: null, icon: UploadCloud, label: 'Upload' },
		{ key: 'ocr_ms', icon: ScanText, label: 'OCR' },
		{ key: 'text_features_ms', icon: Type, label: 'NLP' },
		{ key: 'cv_features_ms', icon: ScanEye, label: 'Vision' },
		{ key: null, icon: GitMerge, label: 'Fusion' },
		{ key: 'inference_ms', icon: Cpu, label: modelName },
		{ key: 'explain_ms', icon: Sparkles, label: 'SHAP' },
		{ key: null, icon: FileCheck, label: 'Report' }
	]);

	const totalMs = $derived(Math.round(Object.values(timings).reduce((a, b) => a + b, 0)));
	const noMotion = prefersReducedMotion();
	const STEP_MS = 90;

	// One full left-to-right sweep of the light pulse. Each node's glow is
	// delayed by its fractional position along the track so the glow lands
	// exactly as the pulse reaches it.
	const WAVE_MS = 3600;
	// Nodes are equal-width flex children, so node i's centre sits at
	// (i + 0.5) / count across the row — used for both the track insets and
	// the per-node animation delay.
	const nodeCentre = (i, count) => (i + 0.5) / count;
</script>

<div class={cn('glass-panel mx-auto max-w-2xl overflow-hidden rounded-2xl px-7 py-6', className)}>
	<div class="mb-7 flex items-center justify-between">
		<h3 class="flex items-center gap-2 text-sm font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
			<Clock size={15} aria-hidden="true" /> Analysis timeline
		</h3>
		{#if totalMs > 0}
			<span
				class="rounded-full px-3 py-1 font-mono text-xs font-medium"
				style="background: color-mix(in oklch, var(--accent-primary) 12%, transparent); color: var(--accent-primary);"
				in:fade={noMotion ? { duration: 0 } : { duration: 400, delay: STAGES.length * STEP_MS }}
			>
				{totalMs}ms total
			</span>
		{/if}
	</div>

	<div class="relative flex items-start justify-between">
		<!-- Animated wave connector. The whole track is masked to a sine path,
		     so the dim base and the travelling neon pulse are both clipped to
		     the wave shape — the pulse itself only ever animates `transform`. -->
		<div
			class="wave-track pointer-events-none absolute top-0 h-11"
			style={`left: ${nodeCentre(0, STAGES.length) * 100}%; right: ${nodeCentre(0, STAGES.length) * 100}%;`}
			aria-hidden="true"
		>
			<div class="wave-base"></div>
			{#if !noMotion}
				<div class="wave-pulse" style={`animation-duration: ${WAVE_MS}ms;`}></div>
			{/if}
		</div>

		{#each STAGES as stage, i (stage.label)}
			{@const ms = stage.key && timings[stage.key] != null ? Math.round(timings[stage.key]) : null}
			{@const glowDelay = nodeCentre(i, STAGES.length) * WAVE_MS}
			<div class="relative z-10 flex flex-1 flex-col items-center gap-3 text-center" title={stage.label}>
				<div in:scale={noMotion ? { duration: 0 } : { duration: 380, delay: i * STEP_MS, start: 0.3 }}>
					<div class="node-shell relative flex h-11 w-11 shrink-0 items-center justify-center">
						{#if !noMotion}
							<span
								class="node-glow"
								style={`animation-duration: ${WAVE_MS}ms; animation-delay: ${glowDelay}ms;`}
							></span>
						{/if}
						<span
							class="node-circle flex h-11 w-11 items-center justify-center rounded-full"
							style={noMotion
								? ''
								: `animation-duration: ${WAVE_MS}ms; animation-delay: ${glowDelay}ms;`}
						>
							<stage.icon size={17} style="color: var(--accent-primary)" aria-hidden="true" />
							<span class="sr-only">{stage.label}</span>
						</span>
					</div>
				</div>
				<span
					class="rounded-md px-2 py-0.5 font-mono text-xs leading-tight font-semibold"
					style={ms != null
						? `color: var(--accent-primary); background: color-mix(in oklch, var(--accent-primary) 10%, transparent);`
						: 'color: var(--text-tertiary);'}
					class:fade-up={!noMotion}
					style:animation-delay={noMotion ? undefined : `${i * STEP_MS + 150}ms`}
				>
					{ms != null ? `${ms}ms` : 'instant'}
				</span>
			</div>
		{/each}
	</div>
</div>

<style>
	/* ---- wave connector -------------------------------------------------- */
	.wave-track {
		--wave-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 44' preserveAspectRatio='none'%3E%3Cpath d='M0,22Q25,9,50,22T100,22T150,22T200,22T250,22T300,22T350,22T400,22T450,22T500,22T550,22T600,22T650,22T700,22T750,22T800,22' fill='none' stroke='%23fff' stroke-width='3'/%3E%3C/svg%3E");
		-webkit-mask-image: var(--wave-mask);
		mask-image: var(--wave-mask);
		-webkit-mask-size: 100% 100%;
		mask-size: 100% 100%;
		-webkit-mask-repeat: no-repeat;
		mask-repeat: no-repeat;
		overflow: hidden;
	}

	.wave-base {
		position: absolute;
		inset: 0;
		background: color-mix(in oklch, var(--accent-primary) 26%, transparent);
	}

	.wave-pulse {
		position: absolute;
		top: 0;
		bottom: 0;
		left: 0;
		width: 34%;
		background: linear-gradient(
			90deg,
			transparent 0%,
			color-mix(in oklch, var(--accent-primary) 55%, transparent) 35%,
			var(--accent-primary) 50%,
			color-mix(in oklch, var(--accent-primary) 55%, transparent) 65%,
			transparent 100%
		);
		will-change: transform;
		animation-name: wave-travel;
		animation-timing-function: linear;
		animation-iteration-count: infinite;
	}
	/* Percentages in `transform` resolve against the element's own box, not
	   its container — so travelling from fully-before to fully-after the
	   track (which is ~2.94x this element's own 34% width) just needs
	   self-relative percentages, no container-query units required. */
	@keyframes wave-travel {
		from {
			transform: translate3d(-150%, 0, 0);
		}
		to {
			transform: translate3d(450%, 0, 0);
		}
	}

	/* ---- nodes ------------------------------------------------------------ */
	.node-circle {
		background: color-mix(in oklch, var(--accent-primary) 12%, var(--surface-raised));
		border: 1px solid color-mix(in oklch, var(--accent-primary) 32%, transparent);
		box-shadow: 0 0 0 4px var(--surface-raised);
		will-change: transform;
		animation-name: node-bump;
		animation-timing-function: cubic-bezier(0.3, 0.8, 0.3, 1);
		animation-iteration-count: infinite;
	}
	@keyframes node-bump {
		0%,
		12%,
		100% {
			transform: scale(1);
		}
		4% {
			transform: scale(1.14);
		}
	}

	/* Separate blurred halo so the glow animates `opacity` (compositor-only)
	   rather than `box-shadow`, which would force a repaint every frame. */
	.node-glow {
		position: absolute;
		inset: -8px;
		border-radius: 999px;
		background: radial-gradient(circle, color-mix(in oklch, var(--accent-primary) 70%, transparent) 0%, transparent 68%);
		opacity: 0;
		will-change: opacity;
		animation-name: node-halo;
		animation-timing-function: ease-out;
		animation-iteration-count: infinite;
	}
	@keyframes node-halo {
		0%,
		14%,
		100% {
			opacity: 0;
		}
		4% {
			opacity: 0.85;
		}
	}

	.fade-up {
		opacity: 0;
		animation: fade-up-kf 0.4s ease forwards;
	}
	@keyframes fade-up-kf {
		from {
			opacity: 0;
			transform: translateY(4px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@media (max-width: 640px) {
		.wave-track,
		.node-glow {
			display: none;
		}
	}
</style>
