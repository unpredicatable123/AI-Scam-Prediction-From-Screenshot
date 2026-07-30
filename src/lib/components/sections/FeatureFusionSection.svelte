<script>
	import { onMount, onDestroy } from 'svelte';
	import { fly } from 'svelte/transition';
	import { reveal, prefersReducedMotion } from '$lib/motion/actions';
	import Combine from '@lucide/svelte/icons/combine';
	import ArrowDown from '@lucide/svelte/icons/arrow-down';
	import Cpu from '@lucide/svelte/icons/cpu';
	import Type from '@lucide/svelte/icons/type';
	import ScanEye from '@lucide/svelte/icons/scan-eye';

	// Real feature/entity names from the actual 67-feature schema (ml/src/features/) —
	// illustrative values, same register as ResultCard's default demo, but every
	// name here corresponds to a field the pipeline genuinely computes. No visual
	// logo-matching or "impersonation mismatch" field exists, so those don't appear.
	const textFeatures = ['urgency_count: 3', 'has_financial_request: true', 'has_credential_request: true', 'conversation_risk: critical'];
	const visualFeatures = ['qr_is_payment_intent: true', 'qr_is_url_risky: true', 'possible_editing_signal: false', 'is_unknown_number: true'];

	// Illustrative demo cycle only — same register as ResultCard's default
	// "Job scam · 94%" prop, not a live classification feed. Categories mirror
	// the real stage-2 labels the pipeline actually trains on/reports.
	const demoClassifications = [
		{ category: 'Job scam', confidence: 94 },
		{ category: 'OTP fraud', confidence: 91 },
		{ category: 'Phishing link', confidence: 97 },
		{ category: 'Romance scam', confidence: 89 },
		{ category: 'Tech support scam', confidence: 93 },
		{ category: 'Investment scam', confidence: 90 }
	];
	let classIndex = $state(0);
	let intervalId;
	const reduceMotion = prefersReducedMotion();

	onMount(() => {
		intervalId = setInterval(() => {
			classIndex = (classIndex + 1) % demoClassifications.length;
		}, 2600);
	});
	onDestroy(() => clearInterval(intervalId));
</script>

<section class="relative mx-auto max-w-5xl px-6 py-32">
	<div use:reveal={{ y: 24 }} class="mx-auto mb-20 max-w-2xl text-center">
		<div
			class="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-xl"
			style="background: color-mix(in oklch, var(--accent-secondary) 16%, transparent);"
		>
			<Combine size={20} style="color: var(--accent-secondary)" aria-hidden="true" />
		</div>
		<span class="text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
			03 · Feature fusion
		</span>
		<h2 class="mt-4 text-4xl font-semibold tracking-tight text-balance">Two branches, one decision</h2>
		<p class="mt-3 text-base" style="color: var(--text-secondary);">
			Text and visual signals merge into a single, ordered feature vector before anything gets classified.
		</p>
	</div>

	<div use:reveal={{ y: 32, delay: 0.05 }} class="flex flex-col items-center gap-0 md:flex-row md:justify-center md:gap-0">
		<div class="branch-panel branch-panel-plum">
			<div class="branch-header">
				<Type size={13} style="color: var(--color-plum-400)" aria-hidden="true" />
				<span>Text branch</span>
			</div>
			{#each textFeatures as feature (feature)}
				<div class="feature-chip">{feature}</div>
			{/each}
		</div>

		<div class="connector connector-vertical md:hidden" aria-hidden="true">
			<div class="connector-runner connector-runner-y"></div>
		</div>
		<div class="connector connector-horizontal hidden md:flex" aria-hidden="true">
			<div class="connector-runner connector-runner-x"></div>
		</div>

		<div class="fusion-node">
			<Combine size={22} style="color: var(--accent-secondary)" aria-hidden="true" />
			<span class="fusion-label">Fused vector</span>
		</div>

		<div class="connector connector-vertical md:hidden" aria-hidden="true">
			<div class="connector-runner connector-runner-y"></div>
		</div>
		<div class="connector connector-horizontal hidden md:flex" aria-hidden="true">
			<div class="connector-runner connector-runner-x"></div>
		</div>

		<div class="branch-panel branch-panel-lime">
			<div class="branch-header">
				<ScanEye size={13} style="color: var(--color-lime-500)" aria-hidden="true" />
				<span>Visual branch</span>
			</div>
			{#each visualFeatures as feature (feature)}
				<div class="feature-chip">{feature}</div>
			{/each}
		</div>
	</div>

	<div use:reveal={{ y: 16, delay: 0.1 }} class="mx-auto mt-14 flex w-fit flex-col items-center gap-3">
		<ArrowDown size={18} style="color: var(--text-tertiary)" aria-hidden="true" />
		<div
			class="classification-badge glass-panel flex items-center gap-3 rounded-full px-5 py-2.5"
			style="box-shadow: var(--shadow-glow-plum);"
		>
			<Cpu size={16} style="color: var(--color-plum-400)" aria-hidden="true" />
			<span class="classification-text-wrap">
				{#key classIndex}
					<span
						class="classification-text text-sm"
						style="color: var(--text-primary);"
						in:fly={reduceMotion ? { duration: 0 } : { y: 12, duration: 350 }}
						out:fly={reduceMotion ? { duration: 0 } : { y: -12, duration: 350 }}
					>
						Classification: <strong>{demoClassifications[classIndex].category}</strong> ·
						<span class="font-mono">{demoClassifications[classIndex].confidence}%</span>
					</span>
				{/key}
			</span>
		</div>
	</div>
</section>

<style>
	.branch-panel {
		display: flex;
		flex-direction: column;
		gap: 10px;
		width: 100%;
		max-width: 260px;
		padding: 18px;
		border-radius: 16px;
		background: color-mix(in oklch, var(--surface-raised) 45%, transparent);
		border: 1px solid var(--border-subtle);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		transition: box-shadow 0.3s ease, border-color 0.3s ease;
	}
	.branch-panel-plum {
		border-color: color-mix(in oklch, var(--color-plum-500) 45%, var(--border-subtle));
		box-shadow: var(--shadow-glow-plum);
	}
	.branch-panel-lime {
		border-color: color-mix(in oklch, var(--color-lime-500) 45%, var(--border-subtle));
		box-shadow: var(--shadow-glow-lime);
	}
	.branch-header {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 2px;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--text-tertiary);
	}
	.feature-chip {
		width: 100%;
		border-radius: 10px;
		padding: 8px 12px;
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-secondary);
		background: color-mix(in oklch, var(--surface-overlay) 70%, transparent);
		border: 1px solid var(--border-subtle);
	}

	.connector {
		position: relative;
		flex-shrink: 0;
		overflow: hidden;
	}
	.connector-horizontal {
		width: 56px;
		height: 2px;
		border-radius: 999px;
		background: var(--border-subtle);
	}
	.connector-vertical {
		width: 2px;
		height: 32px;
		border-radius: 999px;
		background: var(--border-subtle);
	}
	.connector-runner {
		position: absolute;
		inset: 0;
	}
	.connector-runner-x {
		width: 40%;
		height: 100%;
		background: linear-gradient(90deg, transparent, var(--accent-secondary), transparent);
		animation: run-x 2.4s linear infinite;
	}
	.connector-runner-y {
		width: 100%;
		height: 40%;
		background: linear-gradient(180deg, transparent, var(--accent-secondary), transparent);
		animation: run-y 2.4s linear infinite;
	}
	@keyframes run-x {
		from {
			transform: translateX(-100%);
			opacity: 0;
		}
		15% {
			opacity: 1;
		}
		85% {
			opacity: 1;
		}
		to {
			transform: translateX(350%);
			opacity: 0;
		}
	}
	@keyframes run-y {
		from {
			transform: translateY(-100%);
			opacity: 0;
		}
		15% {
			opacity: 1;
		}
		85% {
			opacity: 1;
		}
		to {
			transform: translateY(350%);
			opacity: 0;
		}
	}

	.fusion-node {
		display: flex;
		flex-shrink: 0;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 4px;
		width: 96px;
		height: 96px;
		border-radius: 20px;
		background: color-mix(in oklch, var(--surface-raised) 65%, transparent);
		border: 1px solid var(--border-subtle);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		box-shadow: var(--shadow-glow-lime);
		animation: fusion-pulse 3.2s ease-in-out infinite;
	}
	.fusion-label {
		text-align: center;
		font-size: 9px;
		line-height: 1.2;
		font-weight: 500;
		color: var(--text-tertiary);
	}
	@keyframes fusion-pulse {
		0%,
		100% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.06);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.fusion-node {
			animation: none;
		}
		.connector-runner-x,
		.connector-runner-y {
			animation: none;
			opacity: 0.5;
		}
	}

	.classification-badge {
		min-height: 44px;
	}
	.classification-text-wrap {
		position: relative;
		display: inline-block;
		height: 20px;
		min-width: 260px;
		overflow: hidden;
	}
	.classification-text {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		white-space: nowrap;
		line-height: 20px;
	}
</style>
