<script>
	import { cn } from '$lib/utils/cn';
	import { prefersReducedMotion } from '$lib/motion/actions';
	import PieChart from '@lucide/svelte/icons/pie-chart';

	// Real percentages, not fabricated category weights — each value is the
	// group's actual positive SHAP contribution as a share of the total
	// positive contribution (computed in pipeline.py's _risk_breakdown,
	// same evidence-gated groups generate_reasons uses). A group only
	// appears here if it genuinely moved this specific prediction.
	let { breakdown = [], class: className = '' } = $props();

	const noMotion = prefersReducedMotion();

	// Sets the bar's width one tick after mount so the CSS transition has
	// something to animate from — setting the final width directly in the
	// initial markup leaves nothing for `transition: width` to animate.
	function growTo(node, { target, delay = 0 }) {
		if (noMotion) {
			node.style.width = `${target}%`;
			return {};
		}
		const t = setTimeout(() => (node.style.width = `${target}%`), 20 + delay);
		return { destroy: () => clearTimeout(t) };
	}
</script>

{#if breakdown.length > 0}
	<div class={cn('glass-panel mx-auto max-w-xl rounded-xl px-5 py-4', className)}>
		<h3 class="mb-3.5 flex items-center gap-1.5 text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
			<PieChart size={13} aria-hidden="true" /> Risk breakdown
		</h3>
		<div class="flex flex-col gap-3">
			{#each breakdown as item, i (item.group)}
				<div class="flex flex-col gap-1">
					<div class="flex items-center justify-between text-sm">
						<span style="color: var(--text-primary);">{item.label}</span>
						<span class="font-mono text-xs font-semibold" style="color: var(--accent-primary);">{item.percentage}%</span>
					</div>
					<span class="h-1.5 w-full overflow-hidden rounded-full" style="background: var(--surface-overlay);">
						<span
							class="block h-full rounded-full"
							style="width: 0%; background: var(--accent-primary); transition: width 0.8s var(--ease-out-expo);"
							use:growTo={{ target: item.percentage, delay: i * 80 }}
						></span>
					</span>
				</div>
			{/each}
		</div>
	</div>
{/if}
