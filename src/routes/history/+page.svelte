<script>
	import { onMount } from 'svelte';
	import { listScans, deleteScan, clearHistory, getStats } from '$lib/stores/scanHistory';
	import ShieldCheck from '@lucide/svelte/icons/shield-check';
	import ShieldQuestion from '@lucide/svelte/icons/shield-question';
	import ShieldAlert from '@lucide/svelte/icons/shield-alert';
	import ShieldMinus from '@lucide/svelte/icons/shield-minus';
	import ShieldX from '@lucide/svelte/icons/shield-x';
	import Search from '@lucide/svelte/icons/search';
	import Trash2 from '@lucide/svelte/icons/trash-2';
	import History from '@lucide/svelte/icons/history';

	const RISK_META = {
		safe: { icon: ShieldCheck, label: 'Safe', color: 'var(--color-risk-safe)' },
		low: { icon: ShieldQuestion, label: 'Low risk', color: 'var(--color-risk-low)' },
		medium: { icon: ShieldAlert, label: 'Suspicious', color: 'var(--color-risk-medium)' },
		high: { icon: ShieldMinus, label: 'High risk', color: 'var(--color-risk-high)' },
		critical: { icon: ShieldX, label: 'Scam', color: 'var(--color-risk-critical)' }
	};

	const PAGE_SIZE = 10;

	let scans = $state([]);
	let stats = $state(null);
	let query = $state('');
	let bandFilter = $state('all');
	let page = $state(1);

	onMount(() => {
		scans = listScans();
		stats = getStats();
	});

	function remove(id) {
		deleteScan(id);
		scans = listScans();
		stats = getStats();
	}

	function clearAll() {
		clearHistory();
		scans = listScans();
		stats = getStats();
	}

	const filtered = $derived.by(() => {
		let out = scans;
		if (bandFilter !== 'all') out = out.filter((s) => s.riskBand === bandFilter);
		const q = query.trim().toLowerCase();
		if (q) out = out.filter((s) => s.fileName.toLowerCase().includes(q) || s.ocrSnippet.toLowerCase().includes(q));
		return out;
	});

	const totalPages = $derived(Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)));
	const pageItems = $derived(filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE));

	$effect(() => {
		if (page > totalPages) page = totalPages;
	});
</script>

<svelte:head>
	<title>Scan history — AI-Powered Scam Detection</title>
</svelte:head>

<main class="mx-auto min-h-screen max-w-3xl px-6 pt-36 pb-32">
	<div class="mb-8 flex flex-col items-start gap-3">
		<span
			class="rounded-full border px-3 py-1 text-xs font-medium tracking-wide uppercase"
			style="border-color: var(--border-default); color: var(--text-tertiary);"
		>
			History
		</span>
		<h1 class="text-3xl font-semibold tracking-tight text-balance sm:text-4xl">Scan history</h1>
		<p class="text-base" style="color: var(--text-secondary);">
			Stored only in this browser — there's no account or server-side history yet, so this list
			won't follow you to another device.
		</p>
	</div>

	{#if scans.length === 0}
		<div class="glass-panel flex flex-col items-center gap-3 rounded-2xl px-6 py-16 text-center">
			<History size={28} style="color: var(--text-tertiary)" aria-hidden="true" />
			<p class="text-sm" style="color: var(--text-secondary);">No scans yet — analyze a screenshot to see it here.</p>
			<a href="/analyze" class="mt-2 text-sm font-medium underline" style="color: var(--accent-secondary);">Analyze a screenshot</a>
		</div>
	{:else}
		{#if stats}
			<div class="mb-6 grid grid-cols-2 gap-2.5 sm:grid-cols-5">
				<div class="glass-panel flex flex-col gap-0.5 rounded-xl px-4 py-3">
					<span class="font-mono text-lg font-semibold" style="color: var(--text-primary);">{stats.total}</span>
					<span class="text-[11px]" style="color: var(--text-tertiary);">Total scans</span>
				</div>
				<div class="glass-panel flex flex-col gap-0.5 rounded-xl px-4 py-3">
					<span class="font-mono text-lg font-semibold" style="color: var(--color-risk-high);">{stats.highRisk}</span>
					<span class="text-[11px]" style="color: var(--text-tertiary);">High risk</span>
				</div>
				<div class="glass-panel flex flex-col gap-0.5 rounded-xl px-4 py-3">
					<span class="font-mono text-lg font-semibold" style="color: var(--color-risk-safe);">{stats.safe}</span>
					<span class="text-[11px]" style="color: var(--text-tertiary);">Safe</span>
				</div>
				<div class="glass-panel flex flex-col gap-0.5 rounded-xl px-4 py-3">
					<span class="font-mono text-lg font-semibold" style="color: var(--text-primary);">{stats.scansThisWeek}</span>
					<span class="text-[11px]" style="color: var(--text-tertiary);">This week</span>
				</div>
				<div class="glass-panel flex flex-col gap-0.5 rounded-xl px-4 py-3">
					<span class="font-mono text-lg font-semibold" style="color: var(--accent-primary);">
						{stats.safetyScore ?? '—'}{stats.safetyScore != null ? '%' : ''}
					</span>
					<span class="text-[11px]" style="color: var(--text-tertiary);">Safety score</span>
				</div>
			</div>
			{#if stats.topCategories.length > 0}
				<div class="mb-6 flex flex-wrap items-center gap-2">
					<span class="text-xs" style="color: var(--text-tertiary);">Top categories:</span>
					{#each stats.topCategories as c (c.category)}
						<span class="rounded-full px-2.5 py-1 font-mono text-[11px]" style="background: var(--surface-overlay); color: var(--text-secondary);">
							{c.category} ({c.count})
						</span>
					{/each}
				</div>
			{/if}
		{/if}
		<div class="mb-5 flex flex-wrap items-center gap-2">
			<div class="relative flex-1" style="min-width: 200px;">
				<Search size={14} class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2" style="color: var(--text-tertiary);" aria-hidden="true" />
				<input
					type="text"
					bind:value={query}
					oninput={() => (page = 1)}
					placeholder="Search by filename or text…"
					class="w-full rounded-lg py-2 pr-3 pl-8 text-sm outline-none"
					style="background: var(--surface-overlay); color: var(--text-primary); border: 1px solid var(--border-subtle);"
				/>
			</div>
			<select
				bind:value={bandFilter}
				onchange={() => (page = 1)}
				class="rounded-lg px-3 py-2 text-sm outline-none"
				style="background: var(--surface-overlay); color: var(--text-primary); border: 1px solid var(--border-subtle);"
			>
				<option value="all">All risk levels</option>
				<option value="safe">Safe</option>
				<option value="low">Low risk</option>
				<option value="medium">Suspicious</option>
				<option value="high">High risk</option>
				<option value="critical">Scam</option>
			</select>
			<button
				type="button"
				onclick={clearAll}
				class="rounded-lg px-3 py-2 text-sm font-medium"
				style="background: color-mix(in oklch, var(--color-risk-high) 12%, transparent); color: var(--color-risk-high);"
			>
				Clear all
			</button>
		</div>

		<div class="flex flex-col gap-2.5">
			{#each pageItems as scan (scan.id)}
				{@const meta = RISK_META[scan.riskBand] ?? RISK_META.medium}
				<div class="glass-panel flex items-center gap-4 rounded-xl px-4 py-3.5">
					<div
						class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
						style={`background: color-mix(in oklch, ${meta.color} 20%, transparent);`}
					>
						<meta.icon size={16} style={`color: ${meta.color}`} aria-hidden="true" />
					</div>
					<div class="min-w-0 flex-1">
						<div class="flex items-center gap-2">
							<span class="truncate text-sm font-medium" style="color: var(--text-primary);">
								{scan.fileName || 'Untitled screenshot'}
							</span>
							<span class="shrink-0 font-mono text-[10px]" style={`color: ${meta.color}`}>{meta.label}</span>
						</div>
						<p class="truncate text-xs" style="color: var(--text-tertiary);">
							{new Date(scan.timestamp).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}
							{#if scan.ocrSnippet}· {scan.ocrSnippet}{/if}
						</p>
					</div>
					<span class="shrink-0 font-mono text-xs" style="color: var(--text-secondary);">{scan.confidence}%</span>
					<button
						type="button"
						onclick={() => remove(scan.id)}
						class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
						style="color: var(--text-tertiary);"
						aria-label="Delete this scan from history"
					>
						<Trash2 size={15} aria-hidden="true" />
					</button>
				</div>
			{/each}
		</div>

		{#if totalPages > 1}
			<div class="mt-6 flex items-center justify-center gap-3 text-sm">
				<button
					type="button"
					disabled={page === 1}
					onclick={() => (page = Math.max(1, page - 1))}
					class="rounded-lg px-3 py-1.5 disabled:opacity-40"
					style="background: var(--surface-overlay); color: var(--text-primary);"
				>
					Previous
				</button>
				<span style="color: var(--text-tertiary);">Page {page} of {totalPages}</span>
				<button
					type="button"
					disabled={page === totalPages}
					onclick={() => (page = Math.min(totalPages, page + 1))}
					class="rounded-lg px-3 py-1.5 disabled:opacity-40"
					style="background: var(--surface-overlay); color: var(--text-primary);"
				>
					Next
				</button>
			</div>
		{/if}
	{/if}
</main>
