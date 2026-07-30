<script>
	import { cn } from '$lib/utils/cn';
	import QrCode from '@lucide/svelte/icons/qr-code';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';

	let {
		hasQr = false,
		qrIsPaymentIntent = false,
		qrHasPrefilledAmount = false,
		qrIsUrl = false,
		qrIsUrlRisky = false,
		qrPayloadPreview = null,
		class: className = ''
	} = $props();
</script>

{#if hasQr}
	<div class={cn('glass-panel mx-auto max-w-xl rounded-xl px-5 py-4', className)}>
		<h3 class="mb-3 flex items-center gap-1.5 text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
			<QrCode size={13} aria-hidden="true" /> QR code analysis
		</h3>
		<div class="flex flex-col gap-2.5">
			<div class="flex items-center justify-between text-sm">
				<span style="color: var(--text-secondary);">Payment request</span>
				{#if qrIsPaymentIntent}
					<span class="flex items-center gap-1 font-medium" style="color: var(--color-risk-high);">
						<X size={13} aria-hidden="true" /> Yes{qrHasPrefilledAmount ? ' — amount pre-filled' : ''}
					</span>
				{:else}
					<span class="flex items-center gap-1" style="color: var(--color-risk-safe);"><Check size={13} aria-hidden="true" /> No</span>
				{/if}
			</div>
			<div class="flex items-center justify-between text-sm">
				<span style="color: var(--text-secondary);">Links to a website</span>
				{#if qrIsUrl}
					<span class="flex items-center gap-1 font-medium" style={`color: ${qrIsUrlRisky ? 'var(--color-risk-high)' : 'var(--text-primary)'}`}>
						{qrIsUrlRisky ? 'Yes — looks risky' : 'Yes'}
					</span>
				{:else}
					<span style="color: var(--text-tertiary);">No</span>
				{/if}
			</div>
			{#if qrPayloadPreview}
				<div class="flex flex-col gap-1 border-t pt-2.5" style="border-color: var(--border-subtle);">
					<span class="text-xs" style="color: var(--text-tertiary);">Decoded content</span>
					<span class="truncate font-mono text-xs" style="color: var(--text-secondary);" title={qrPayloadPreview}>{qrPayloadPreview}</span>
				</div>
			{/if}
		</div>
	</div>
{/if}
