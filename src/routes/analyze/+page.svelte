<script>
	import { onDestroy } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import Dropzone from '$lib/components/upload/Dropzone.svelte';
	import ScanOverlay from '$lib/components/upload/ScanOverlay.svelte';
	import ScanSummaryCard from '$lib/components/results/ScanSummaryCard.svelte';
	import ResultCard from '$lib/components/results/ResultCard.svelte';
	import OcrDisclosure from '$lib/components/results/OcrDisclosure.svelte';
	import KeywordChips from '$lib/components/results/KeywordChips.svelte';
	import UrlIntelCard from '$lib/components/results/UrlIntelCard.svelte';
	import QrIntelCard from '$lib/components/results/QrIntelCard.svelte';
	import ThreatTimeline from '$lib/components/results/ThreatTimeline.svelte';
	import SafetyTips from '$lib/components/results/SafetyTips.svelte';
	import PrintReport from '$lib/components/results/PrintReport.svelte';
	import BrandGuardCard from '$lib/components/results/BrandGuardCard.svelte';
	import ConversationFlow from '$lib/components/results/ConversationFlow.svelte';
	import RiskBreakdown from '$lib/components/results/RiskBreakdown.svelte';
	import FeedbackButtons from '$lib/components/results/FeedbackButtons.svelte';
	import { saveScan } from '$lib/stores/scanHistory';
	import { prefersReducedMotion } from '$lib/motion/actions';
	import CircleAlert from '@lucide/svelte/icons/circle-alert';
	import RotateCw from '@lucide/svelte/icons/rotate-cw';
	import Download from '@lucide/svelte/icons/download';
	import UploadCloud from '@lucide/svelte/icons/upload-cloud';
	import ScanText from '@lucide/svelte/icons/scan-text';
	import ScanEye from '@lucide/svelte/icons/scan-eye';
	import Cpu from '@lucide/svelte/icons/cpu';
	import Sparkles from '@lucide/svelte/icons/sparkles';

	// Illustrative only — the backend is a single synchronous call, so this
	// cycles on a timer rather than tracking real pipeline progress. Real
	// per-stage timings are shown after the response arrives (ThreatTimeline).
	const STAGES = [
		{ icon: UploadCloud, label: 'Upload' },
		{ icon: ScanText, label: 'OCR + NLP' },
		{ icon: ScanEye, label: 'Visual analysis' },
		{ icon: Cpu, label: 'Classification' },
		{ icon: Sparkles, label: 'Explainable output' }
	];

	const TIMING_LABELS = {
		ocr_ms: 'OCR',
		text_features_ms: 'Text features',
		cv_features_ms: 'Visual features',
		inference_ms: 'Classify',
		explain_ms: 'Explain'
	};

	/** @type {'idle' | 'loading' | 'success' | 'error'} */
	let status = $state('idle');
	let result = $state(null);
	let errorMessage = $state('');
	let lastFile = $state(null);
	let activeStage = $state(0);
	let previewUrl = $state('');
	/** @type {ReturnType<typeof setInterval>} */
	let stageTimer;

	function buildTimingBreakdown(timings) {
		if (!timings) return [];
		return Object.entries(timings).map(([key, ms]) => ({ label: TIMING_LABELS[key] ?? key, ms: Math.round(ms) }));
	}

	// Reuses the exact words the model already quoted as evidence (nlg.py's
	// `_quote_first_match`) for OCR-panel highlighting, instead of keeping a
	// second copy of the scam lexicon in sync on the frontend.
	function extractHighlightTerms(reasons) {
		const terms = new Set();
		for (const r of reasons ?? []) {
			for (const m of r.text.matchAll(/"([^"]+)"/g)) terms.add(m[1]);
		}
		return [...terms];
	}

	async function handleAnalyze(file) {
		lastFile = file;
		if (previewUrl) URL.revokeObjectURL(previewUrl);
		previewUrl = URL.createObjectURL(file);
		status = 'loading';
		errorMessage = '';
		result = null;
		activeStage = 0;
		clearInterval(stageTimer);
		if (!prefersReducedMotion()) {
			stageTimer = setInterval(() => {
				activeStage = (activeStage + 1) % STAGES.length;
			}, 650);
		}

		const formData = new FormData();
		formData.append('file', file);

		try {
			const res = await fetch('/api/analyze', { method: 'POST', body: formData });
			if (!res.ok) {
				const body = await res.json().catch(() => ({}));
				throw new Error(body.message || `Analysis failed (${res.status})`);
			}
			result = await res.json();
			status = 'success';
			saveScan(result, file.name);
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'Something went wrong.';
			status = 'error';
		} finally {
			clearInterval(stageTimer);
		}
	}

	// Scroll-triggered `reveal` is the wrong primitive for content that pops
	// in via a fetch response while already on-screen (no scroll event ever
	// fires) — it left list items inside ResultCard stuck at opacity:0 with
	// their space still reserved. Plain mount-triggered transitions instead.
	const noMotion = prefersReducedMotion();
	const flyIn = (delayMs = 0) => (noMotion ? { duration: 0 } : { y: 14, duration: 400, delay: delayMs });

	onDestroy(() => {
		if (previewUrl) URL.revokeObjectURL(previewUrl);
	});

	function riskFromScore(score) {
		if (score < 20) return 'safe';
		if (score < 40) return 'low';
		if (score < 60) return 'medium';
		if (score < 80) return 'high';
		return 'critical';
	}
</script>

<svelte:head>
	<title>Analyze a screenshot — AI-Powered Scam Detection</title>
</svelte:head>

<div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
	<div class="absolute inset-0 bg-grid opacity-[0.15]"></div>
	<div
		class="absolute -top-32 -right-40 h-152 w-152 rounded-full blur-3xl"
		style="background: radial-gradient(circle, var(--accent-primary) 0%, transparent 70%); opacity: 0.14;"
	></div>
	<div
		class="absolute -bottom-48 -left-40 h-128 w-lg rounded-full blur-3xl"
		style="background: radial-gradient(circle, var(--accent-secondary) 0%, transparent 70%); opacity: 0.1;"
	></div>
</div>

<main class="mx-auto min-h-screen max-w-2xl px-6 pt-36 pb-32">
	<div class="mb-10 flex flex-col items-start gap-3">
		<span
			class="rounded-full border px-3 py-1 text-xs font-medium tracking-wide uppercase"
			style="border-color: var(--border-default); color: var(--text-tertiary);"
		>
			Upload
		</span>
		<h1 class="text-3xl font-semibold tracking-tight text-balance sm:text-4xl">Analyze a screenshot</h1>
		<p class="text-base" style="color: var(--text-secondary);">
			Upload a chat screenshot from WhatsApp, Telegram, SMS, Instagram, or email. Nothing leaves
			your browser except the file you submit.
		</p>
	</div>

	<Dropzone onAnalyze={handleAnalyze} />

	{#if status === 'loading'}
		<div in:fly={flyIn()} out:fade={{ duration: 150 }} class="glass-panel mt-10 flex flex-col gap-5 rounded-xl px-5 py-5">
			{#if previewUrl}
				<ScanOverlay src={previewUrl} />
			{/if}
			<span class="text-sm font-medium" style="color: var(--text-primary);">
				{STAGES[activeStage].label}…
			</span>
			<div class="flex items-center justify-between">
				{#each STAGES as stage, i (stage.label)}
					{@const isActive = i === activeStage}
					{@const isDone = i < activeStage}
					<div class="flex flex-1 flex-col items-center gap-2 text-center">
						<div
							class="flex h-9 w-9 items-center justify-center rounded-lg transition-colors duration-300"
							style={`background: ${isActive || isDone ? 'color-mix(in oklch, var(--accent-secondary) 20%, transparent)' : 'var(--surface-overlay)'};`}
						>
							<stage.icon
								size={16}
								style={`color: ${isActive || isDone ? 'var(--accent-secondary)' : 'var(--text-tertiary)'}`}
								aria-hidden="true"
							/>
						</div>
						<span
							class="hidden text-[10px] leading-tight sm:block"
							style={`color: ${isActive ? 'var(--text-primary)' : 'var(--text-tertiary)'};`}
						>
							{stage.label}
						</span>
					</div>
					{#if i < STAGES.length - 1}
						<div class="mx-1 mb-6 h-px flex-1" style="background: var(--border-subtle);"></div>
					{/if}
				{/each}
			</div>
		</div>
	{/if}

	{#if status === 'error'}
		<div
			in:fly={flyIn()}
			out:fade={{ duration: 150 }}
			class="mt-10 flex flex-wrap items-start gap-3 rounded-xl px-4 py-3.5 text-sm"
			style="background: color-mix(in oklch, var(--color-risk-high) 12%, transparent); color: var(--color-risk-high);"
		>
			<CircleAlert size={16} class="mt-0.5 shrink-0" aria-hidden="true" />
			<span class="flex-1">{errorMessage}</span>
			{#if lastFile}
				<button
					type="button"
					onclick={() => handleAnalyze(lastFile)}
					class="flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium"
					style="background: color-mix(in oklch, var(--color-risk-high) 18%, transparent); color: var(--color-risk-high);"
				>
					<RotateCw size={13} aria-hidden="true" />
					Try again
				</button>
			{/if}
		</div>
	{/if}

	{#if status === 'success' && result}
		<div in:fade={{ duration: 250 }} class="mt-10 flex flex-col gap-5">
			<div in:fly={flyIn()}>
				<ScanSummaryCard
					label={result.prediction.label}
					riskBand={result.prediction.riskBand ?? riskFromScore(result.prediction.riskScore)}
					riskScore={result.prediction.riskScore}
					category={result.prediction.category}
					confidence={result.prediction.confidence}
					scanDurationMs={result.scanDurationMs}
					scanTimestamp={result.scanTimestamp}
				/>
			</div>

			{#if result.ocr?.text}
				<div in:fly={flyIn(60)}>
					<OcrDisclosure
						text={result.ocr.text}
						confidence={result.ocr.confidence}
						highlightTerms={extractHighlightTerms(result.explanation.reasons)}
						insufficientConfidence={result.degraded?.includes('ocr_insufficient_confidence')}
					/>
				</div>
			{/if}

			<div in:fly={flyIn(90)}>
				<BrandGuardCard brandImpersonation={result.entities.brandImpersonation} />
			</div>

			<div in:fly={flyIn(100)}>
				<KeywordChips reasons={result.explanation.reasons} />
			</div>

			<div in:fly={flyIn(110)}>
				<ConversationFlow
					risk={result.conversationFlow.risk}
					stageCount={result.conversationFlow.stageCount}
					sequence={result.conversationFlow.sequence}
				/>
			</div>

			<div in:fly={flyIn(120)}>
				<UrlIntelCard
					hasUrl={result.entities.hasUrl}
					hasShortenerUrl={result.entities.hasShortenerUrl}
					hasIpUrl={result.entities.hasIpUrl}
					urlMaxRisk={result.entities.urlMaxRisk}
				/>
			</div>

			<div in:fly={flyIn(140)}>
				<QrIntelCard
					hasQr={result.entities.hasQr}
					qrIsPaymentIntent={result.entities.qrIsPaymentIntent}
					qrHasPrefilledAmount={result.entities.qrHasPrefilledAmount}
					qrIsUrl={result.entities.qrIsUrl}
					qrIsUrlRisky={result.entities.qrIsUrlRisky}
					qrPayloadPreview={result.entities.qrPayloadPreview}
				/>
			</div>

			<div in:fly={flyIn(160)}>
				<ResultCard
					label={result.prediction.label}
					riskBand={result.prediction.riskBand ?? riskFromScore(result.prediction.riskScore)}
					riskScore={result.prediction.riskScore}
					category={result.prediction.category}
					confidence={result.prediction.confidence}
					reasons={result.explanation.reasons}
					actions={result.recommendations}
					timingBreakdown={buildTimingBreakdown(result.timings)}
					footerNote={`Analyzed in ${(Object.values(result.timings).reduce((a, b) => a + b, 0) / 1000).toFixed(1)}s · model ${result.modelVersion} · feature schema ${result.featureSchemaVersion}`}
				/>
			</div>

			<div in:fly={flyIn(175)}>
				<RiskBreakdown breakdown={result.explanation.riskBreakdown} />
			</div>

			{#if result.prediction.label === 'fraudulent'}
				<div in:fly={flyIn(180)}>
					<SafetyTips category={result.prediction.category} />
				</div>
			{/if}

			<div in:fly={flyIn(200)}>
				<ThreatTimeline timings={result.timings} />
			</div>

			<div in:fly={flyIn(215)}>
				<FeedbackButtons scanId={result.requestId} />
			</div>

			<div in:fly={flyIn(220)} class="mx-auto flex max-w-xl justify-center">
				<button
					type="button"
					onclick={() => window.print()}
					class="flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium"
					style="background: var(--surface-overlay); color: var(--text-primary); border: 1px solid var(--border-default);"
				>
					<Download size={15} aria-hidden="true" />
					Download report
				</button>
			</div>
		</div>

		<PrintReport {result} {previewUrl} />
	{/if}
</main>
