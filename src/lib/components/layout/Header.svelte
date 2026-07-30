<script>
	import { onMount } from 'svelte';
	import { cn } from '$lib/utils/cn';
	import ShieldCheck from '@lucide/svelte/icons/shield-check';
	import Menu from '@lucide/svelte/icons/menu';
	import X from '@lucide/svelte/icons/x';

	let scrolled = $state(false);
	let mobileOpen = $state(false);

	const links = [
		{ href: '#how-it-works', label: 'How it works' },
		{ href: '#problem', label: 'Why it matters' },
		{ href: '/history', label: 'History' }
	];

	onMount(() => {
		let ticking = false;
		const onScroll = () => {
			if (ticking) return;
			ticking = true;
			requestAnimationFrame(() => {
				scrolled = window.scrollY > 32;
				ticking = false;
			});
		};
		window.addEventListener('scroll', onScroll, { passive: true });
		onScroll();
		return () => window.removeEventListener('scroll', onScroll);
	});
</script>

<header
	class={cn('fixed inset-x-0 top-0 z-50 transition-[background-color,border-color] duration-300', scrolled && 'glass-panel')}
	style={!scrolled ? 'border-bottom: 1px solid transparent;' : ''}
>
	<div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
		<a href="/" class="flex items-center gap-2">
			<ShieldCheck size={20} style="color: var(--accent-secondary)" aria-hidden="true" />
			<span class="text-sm font-semibold tracking-tight" style="color: var(--text-primary);">Scam Detector</span>
		</a>

		<nav class="hidden items-center gap-8 md:flex">
			{#each links as link (link.href)}
				<a href={link.href} class="text-sm transition-colors duration-200 hover:opacity-80" style="color: var(--text-secondary);">
					{link.label}
				</a>
			{/each}
		</nav>

		<div class="hidden md:block">
			<a
				href="/analyze"
				class="rounded-lg px-4 py-2 text-sm font-medium text-white transition-transform duration-300 ease-out-expo hover:-translate-y-0.5"
				style="background: linear-gradient(120deg, var(--color-plum-500), var(--color-plum-600)); box-shadow: var(--shadow-glow-plum);"
			>
				Analyze a screenshot
			</a>
		</div>

		<button
			type="button"
			class="flex h-9 w-9 items-center justify-center rounded-lg md:hidden"
			style="color: var(--text-primary);"
			onclick={() => (mobileOpen = !mobileOpen)}
			aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
			aria-expanded={mobileOpen}
		>
			{#if mobileOpen}
				<X size={20} aria-hidden="true" />
			{:else}
				<Menu size={20} aria-hidden="true" />
			{/if}
		</button>
	</div>

	{#if mobileOpen}
		<div class="glass-panel mx-4 mb-4 flex flex-col gap-1 rounded-xl p-3 md:hidden">
			{#each links as link (link.href)}
				<a
					href={link.href}
					onclick={() => (mobileOpen = false)}
					class="rounded-lg px-3 py-2.5 text-sm"
					style="color: var(--text-secondary);"
				>
					{link.label}
				</a>
			{/each}
			<a
				href="/analyze"
				onclick={() => (mobileOpen = false)}
				class="mt-1 rounded-lg px-3 py-2.5 text-center text-sm font-medium text-white"
				style="background: linear-gradient(120deg, var(--color-plum-500), var(--color-plum-600));"
			>
				Analyze a screenshot
			</a>
		</div>
	{/if}
</header>
