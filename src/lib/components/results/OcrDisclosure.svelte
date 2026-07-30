<script>
	import { slide } from 'svelte/transition';
	import { cn } from '$lib/utils/cn';
	import ScanText from '@lucide/svelte/icons/scan-text';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import Copy from '@lucide/svelte/icons/copy';
	import Check from '@lucide/svelte/icons/check';
	import Search from '@lucide/svelte/icons/search';
	import TriangleAlert from '@lucide/svelte/icons/triangle-alert';

	// highlightTerms: the exact words already quoted inside the real reasons
	// (nlg.py's `_quote_first_match` output) — reused here rather than
	// re-implementing a second copy of the scam lexicon in JS, so highlighting
	// can never drift out of sync with what the model actually matched on.
	//
	// insufficientConfidence: passed straight from the API's real `degraded`
	// array (apps/ai-service/app/ocr.py's MIN_AGGREGATE_CONFIDENCE gate) —
	// not re-derived from a second threshold guess here.
	let {
		text = '',
		confidence = 0,
		highlightTerms = [],
		insufficientConfidence = false,
		class: className = '',
		open = $bindable(false)
	} = $props();

	const URL_RE = /https?:\/\/[^\s]+|www\.[^\s]+/gi;
	const PHONE_RE = /\+?\d[\d\-.\s()]{7,}\d/g;

	let searchQuery = $state('');
	let copied = $state(false);

	function findAll(re, str) {
		const out = [];
		let m;
		re.lastIndex = 0;
		while ((m = re.exec(str))) {
			if (m[0].length === 0) {
				re.lastIndex++;
				continue;
			}
			out.push({ start: m.index, end: m.index + m[0].length });
		}
		return out;
	}

	function findTermMatches(str, terms) {
		const out = [];
		for (const term of terms) {
			if (!term || term.length < 2) continue;
			const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
			const re = new RegExp(`\\b${escaped}\\b`, 'gi');
			out.push(...findAll(re, str));
		}
		return out;
	}

	// Priority-ordered so an active search always wins visibility, and a
	// range already claimed by a higher-priority match is never re-claimed —
	// avoids nested/overlapping <mark> elements.
	const segments = $derived.by(() => {
		const claimed = new Array(text.length).fill(false);
		const accepted = [];

		const layers = [
			searchQuery.trim().length > 1
				? { type: 'search', ranges: findAll(new RegExp(searchQuery.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), text) }
				: null,
			{ type: 'suspicious', ranges: findTermMatches(text, highlightTerms) },
			{ type: 'url', ranges: findAll(URL_RE, text) },
			{ type: 'phone', ranges: findAll(PHONE_RE, text) }
		].filter(Boolean);

		for (const layer of layers) {
			for (const range of layer.ranges) {
				let free = true;
				for (let i = range.start; i < range.end; i++) {
					if (claimed[i]) {
						free = false;
						break;
					}
				}
				if (!free) continue;
				for (let i = range.start; i < range.end; i++) claimed[i] = true;
				accepted.push({ ...range, type: layer.type });
			}
		}

		accepted.sort((a, b) => a.start - b.start);

		const out = [];
		let cursor = 0;
		for (const m of accepted) {
			if (m.start > cursor) out.push({ text: text.slice(cursor, m.start), type: null });
			out.push({ text: text.slice(m.start, m.end), type: m.type });
			cursor = m.end;
		}
		if (cursor < text.length) out.push({ text: text.slice(cursor), type: null });
		return out;
	});

	const matchCount = $derived(
		searchQuery.trim().length > 1 ? segments.filter((s) => s.type === 'search').length : 0
	);

	async function copyText() {
		try {
			await navigator.clipboard.writeText(text);
			copied = true;
			setTimeout(() => (copied = false), 1600);
		} catch {
			// clipboard API unavailable (e.g. insecure context) — fail silently,
			// nothing else useful to do client-side
		}
	}

	const HIGHLIGHT_STYLES = {
		search: 'background: color-mix(in oklch, var(--accent-secondary) 45%, transparent); color: var(--text-primary); border-radius: 3px;',
		suspicious: 'background: color-mix(in oklch, var(--color-risk-high) 30%, transparent); color: var(--text-primary); border-radius: 3px; font-weight: 600;',
		url: 'color: var(--accent-secondary); text-decoration: underline; text-decoration-style: dotted;',
		phone: 'color: var(--accent-primary-strong); font-weight: 600;'
	};
</script>

<div class={cn('glass-panel mx-auto max-w-xl overflow-hidden rounded-xl', className)}>
	<button
		type="button"
		onclick={() => (open = !open)}
		class="flex w-full items-center gap-3 px-5 py-4 text-left"
		aria-expanded={open}
	>
		<ScanText size={15} style="color: var(--accent-secondary)" aria-hidden="true" />
		<span class="text-sm font-medium" style="color: var(--text-primary);">Extracted text</span>

		<span class="ml-auto flex items-center gap-2">
			<span class="h-1 w-16 overflow-hidden rounded-full" style="background: var(--surface-overlay);">
				<span
					class="block h-full rounded-full"
					style={`width: ${confidence}%; background: var(--accent-secondary); transition: width 0.6s var(--ease-out-expo);`}
				></span>
			</span>
			<span class="font-mono text-xs" style="color: var(--text-tertiary);">{confidence}%</span>
		</span>

		<ChevronDown
			size={15}
			class={cn('shrink-0 transition-transform duration-300', open && 'rotate-180')}
			style="color: var(--text-tertiary);"
			aria-hidden="true"
		/>
	</button>

	{#if insufficientConfidence}
		<div
			class="flex items-start gap-2.5 border-t px-5 py-3 text-sm"
			style="border-color: var(--border-subtle); background: color-mix(in oklch, var(--color-risk-medium) 10%, transparent); color: var(--color-risk-medium);"
		>
			<TriangleAlert size={15} class="mt-0.5 shrink-0" aria-hidden="true" />
			<span>Text extraction quality was low on this image — for a more reliable result, try re-uploading a clearer or higher-resolution screenshot.</span>
		</div>
	{/if}

	{#if open}
		<div transition:slide={{ duration: 300 }}>
			<div class="flex items-center gap-2 border-t px-5 py-3" style="border-color: var(--border-subtle);">
				<div class="relative flex-1">
					<Search size={13} class="pointer-events-none absolute top-1/2 left-2.5 -translate-y-1/2" style="color: var(--text-tertiary);" aria-hidden="true" />
					<input
						type="text"
						bind:value={searchQuery}
						placeholder="Search extracted text…"
						class="w-full rounded-lg py-1.5 pr-3 pl-7 text-xs outline-none"
						style="background: var(--surface-overlay); color: var(--text-primary); border: 1px solid var(--border-subtle);"
					/>
				</div>
				{#if searchQuery.trim().length > 1}
					<span class="font-mono text-[11px]" style="color: var(--text-tertiary);">{matchCount} match{matchCount === 1 ? '' : 'es'}</span>
				{/if}
				<button
					type="button"
					onclick={copyText}
					class="flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-medium"
					style="background: var(--surface-overlay); color: var(--text-secondary);"
					aria-label="Copy extracted text"
				>
					{#if copied}
						<Check size={12} style="color: var(--color-risk-safe)" aria-hidden="true" />
						Copied
					{:else}
						<Copy size={12} aria-hidden="true" />
						Copy
					{/if}
				</button>
			</div>

			<p class="px-5 pb-4 font-mono text-xs leading-relaxed whitespace-pre-wrap" style="color: var(--text-secondary);">
				{#each segments as seg, i (i)}
					{#if seg.type}
						<mark style={HIGHLIGHT_STYLES[seg.type]}>{seg.text}</mark>
					{:else}{seg.text}{/if}
				{/each}
			</p>
		</div>
	{/if}
</div>
