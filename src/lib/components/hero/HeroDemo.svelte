<script>
	import RealisticGlobe from './RealisticGlobe.svelte';

	// The globe itself lives in RealisticGlobe.svelte (Three.js + real NASA
	// Blue Marble imagery). The HUD title panel and scanning bar that used to
	// frame it were removed — the globe carries the hero on its own.
</script>

<div class="flex flex-col items-center gap-7">
	<RealisticGlobe class="relative mx-auto aspect-square w-full max-w-md" />
</div>
