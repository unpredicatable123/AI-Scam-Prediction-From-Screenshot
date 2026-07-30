<script>
	import { cn } from '$lib/utils/cn';

	let { class: className = '', children, overlay } = $props();
</script>

<div
	class={cn('relative mx-auto w-full max-w-sm overflow-hidden rounded-[2rem] border', className)}
	style="border-color: var(--border-default); background: var(--surface-base); box-shadow: var(--shadow-panel);"
>
	<div class="flex items-center gap-3 border-b px-4 py-3.5" style="border-color: var(--border-subtle);">
		<div
			class="h-8 w-8 shrink-0 rounded-full"
			style="background: linear-gradient(135deg, var(--color-plum-500), var(--accent-secondary));"
		></div>
		<div class="flex flex-col">
			<span class="text-sm font-medium" style="color: var(--text-primary);">Unknown sender</span>
			<span class="font-mono text-[11px]" style="color: var(--text-tertiary);">+1 (555) 019-2839</span>
		</div>
	</div>

	<div class="relative min-h-[23rem] px-4 py-5">
		{@render children?.()}
		{#if overlay}
			<div class="pointer-events-none absolute inset-0">
				{@render overlay()}
			</div>
		{/if}
	</div>
</div>
