<script>
	import Hero from '$lib/components/hero/Hero.svelte';
	import ProblemStatement from '$lib/components/sections/ProblemStatement.svelte';
	import PipelineOverview from '$lib/components/sections/PipelineOverview.svelte';
	import OcrSection from '$lib/components/sections/OcrSection.svelte';
	import ComputerVisionSection from '$lib/components/sections/ComputerVisionSection.svelte';
	import FeatureFusionSection from '$lib/components/sections/FeatureFusionSection.svelte';
	import MachineLearningSection from '$lib/components/sections/MachineLearningSection.svelte';
	import ExplainableAiSection from '$lib/components/sections/ExplainableAiSection.svelte';
	import PredictionResultsSection from '$lib/components/sections/PredictionResultsSection.svelte';
	import CtaSection from '$lib/components/sections/CtaSection.svelte';
</script>

<svelte:head>
	<title>AI-Powered Scam Detection</title>
	<meta
		name="description"
		content="Detect scams directly from messaging app screenshots using OCR, NLP, computer vision, and explainable AI."
	/>
</svelte:head>

<main class="min-h-screen">
	<Hero />
	<ProblemStatement />
	<PipelineOverview />
	<OcrSection />
	<ComputerVisionSection />
	<FeatureFusionSection />
	<MachineLearningSection />
	<ExplainableAiSection />
	<PredictionResultsSection />
	<CtaSection />
</main>
