<script>
	import { onMount, onDestroy } from 'svelte';
	import { cn } from '$lib/utils/cn';
	import UploadCloud from '@lucide/svelte/icons/upload-cloud';
	import CircleAlert from '@lucide/svelte/icons/circle-alert';
	import Trash2 from '@lucide/svelte/icons/trash-2';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';

	let { onAnalyze = () => {} } = $props();

	const MAX_BYTES = 10 * 1024 * 1024;
	const ACCEPTED = ['image/png', 'image/jpeg', 'image/webp'];

	let dragging = $state(false);
	let file = $state(null);
	let previewUrl = $state('');
	let dimensions = $state(null);
	let error = $state('');
	/** @type {HTMLInputElement} */
	let inputEl;

	function formatSize(bytes) {
		if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function validate(f) {
		if (!ACCEPTED.includes(f.type)) return 'Unsupported file type — use PNG, JPG, or WebP.';
		if (f.size > MAX_BYTES) return 'File is larger than 10 MB.';
		return '';
	}

	function handleFile(f) {
		if (!f) return;
		const err = validate(f);
		if (err) {
			error = err;
			return;
		}
		error = '';
		if (previewUrl) URL.revokeObjectURL(previewUrl);
		file = f;
		dimensions = null;
		previewUrl = URL.createObjectURL(f);
		const img = new Image();
		img.onload = () => (dimensions = { width: img.naturalWidth, height: img.naturalHeight });
		img.src = previewUrl;
	}

	function onDrop(e) {
		e.preventDefault();
		dragging = false;
		handleFile(e.dataTransfer?.files?.[0]);
	}

	function onPaste(e) {
		const item = [...(e.clipboardData?.items || [])].find((i) => i.type.startsWith('image/'));
		if (item) handleFile(item.getAsFile());
	}

	function clear() {
		if (previewUrl) URL.revokeObjectURL(previewUrl);
		file = null;
		previewUrl = '';
		dimensions = null;
		error = '';
		if (inputEl) inputEl.value = '';
	}

	onMount(() => {
		window.addEventListener('paste', onPaste);
		return () => window.removeEventListener('paste', onPaste);
	});

	onDestroy(() => {
		if (previewUrl) URL.revokeObjectURL(previewUrl);
	});
</script>

<div class="flex flex-col gap-4">
	{#if !file}
		<label
			for="screenshot-input"
			class="flex min-h-64 cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-colors duration-200"
			style={`border-color: ${dragging ? 'var(--accent-secondary)' : 'var(--border-default)'}; background: ${dragging ? 'color-mix(in oklch, var(--accent-secondary) 6%, transparent)' : 'var(--surface-raised)'};`}
			ondragover={(e) => {
				e.preventDefault();
				dragging = true;
			}}
			ondragleave={() => (dragging = false)}
			ondrop={onDrop}
		>
			<input
				bind:this={inputEl}
				id="screenshot-input"
				type="file"
				accept="image/png,image/jpeg,image/webp"
				class="sr-only"
				onchange={(e) => handleFile(e.currentTarget.files?.[0])}
			/>
			<div
				class="flex h-14 w-14 items-center justify-center rounded-xl"
				style="background: color-mix(in oklch, var(--accent-secondary) 16%, transparent);"
			>
				<UploadCloud size={26} style="color: var(--accent-secondary)" aria-hidden="true" />
			</div>
			<div>
				<p class="text-sm font-medium" style="color: var(--text-primary);">
					Drop a screenshot here, click to browse, or paste it
				</p>
				<p class="mt-1 text-xs" style="color: var(--text-tertiary);">PNG, JPG, or WebP — up to 10 MB</p>
			</div>
		</label>
	{:else}
		<div class="glass-panel flex items-center gap-4 rounded-2xl p-4">
			<img
				src={previewUrl}
				alt="Selected screenshot preview"
				class="h-20 w-20 shrink-0 rounded-lg object-cover"
				style="background: var(--surface-overlay);"
			/>
			<div class="flex min-w-0 flex-1 flex-col gap-0.5">
				<span class="truncate text-sm font-medium" style="color: var(--text-primary);">{file.name}</span>
				<span class="font-mono text-xs" style="color: var(--text-tertiary);">
					{formatSize(file.size)}{#if dimensions}
						· {dimensions.width}×{dimensions.height}{/if}
				</span>
			</div>
			<button
				type="button"
				onclick={clear}
				class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors hover:opacity-80"
				style="color: var(--text-tertiary);"
				aria-label="Remove file"
			>
				<Trash2 size={16} aria-hidden="true" />
			</button>
		</div>

		<button
			type="button"
			onclick={() => onAnalyze(file)}
			class={cn(
				'group flex items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-medium text-white transition-transform duration-300 ease-out-expo hover:-translate-y-0.5'
			)}
			style="background: linear-gradient(120deg, var(--color-plum-500), var(--color-plum-600)); box-shadow: var(--shadow-glow-plum);"
		>
			Analyze screenshot
			<ArrowRight size={16} class="transition-transform duration-300 group-hover:translate-x-1" />
		</button>
	{/if}

	{#if error}
		<div
			class="flex items-center gap-2 rounded-lg px-3.5 py-2.5 text-sm"
			style="background: color-mix(in oklch, var(--color-risk-high) 14%, transparent); color: var(--color-risk-high);"
		>
			<CircleAlert size={16} class="shrink-0" aria-hidden="true" />
			{error}
		</div>
	{/if}
</div>
