<script>
	import { cn } from '$lib/utils/cn';
	import Lightbulb from '@lucide/svelte/icons/lightbulb';

	// A curated lookup by detected category, not a separate AI system —
	// labeled as such below rather than implied to be model-generated.
	const TIPS_BY_CATEGORY = {
		credential_harvesting: [
			'No legitimate bank, app, or service will ever ask for your OTP, PIN, or password over chat, call, or email.',
			'Type banking URLs in yourself rather than tapping a link — never log in from a link you were sent.'
		],
		phishing: [
			'Hover over or long-press a link before tapping it to see where it actually goes.',
			'Contact the organization directly using a number or address you already know — not one from the message.'
		],
		generic_phishing: [
			'Hover over or long-press a link before tapping it to see where it actually goes.',
			'Contact the organization directly using a number or address you already know — not one from the message.'
		],
		financial_scam: [
			"Never pay an upfront fee to receive money, a job, or a prize — legitimate payouts don't work that way.",
			'Verify any request for money through a second, independent channel before sending anything.'
		],
		banking: [
			'Your bank will never ask you to move money to a "safe account" over chat.',
			'Call your bank using the number on your card or their official site, not a number from the message.'
		],
		romance_dating: [
			"Be cautious if someone you've only met online asks for money, gift cards, or financial details.",
			'A reluctance to video call or meet in person is a common warning sign.'
		],
		tech_support: [
			'Real tech support never cold-contacts you asking for remote access to your device.',
			"If you didn't initiate the contact, treat any \"your device is infected\" message as false."
		],
		authority_scam: [
			'Government agencies do not demand immediate payment over chat or threaten arrest by message.',
			'Verify by calling the agency directly using a number from their official website.'
		],
		social_engineering: [
			'Slow down — urgency and pressure are deliberately used to stop you from thinking it through.',
			'Verify unusual requests from known contacts through a second channel — accounts get compromised.'
		],
		social_engineering_advanced: [
			'Slow down — urgency and pressure are deliberately used to stop you from thinking it through.',
			'Verify unusual requests from known contacts through a second channel — accounts get compromised.'
		],
		urgency: [
			'Legitimate organizations rarely require an immediate, unverified decision.',
			'Take the time to verify independently — a real opportunity or warning will still be real in an hour.'
		],
		threats: [
			'Legal or account action is never threatened and demanded to be resolved only by immediate payment.',
			'Verify any legal or account threat directly with the organization involved, independently.'
		],
		investment: [
			'Guaranteed high returns with no risk is the single most common sign of an investment scam.',
			'Verify any investment platform or advisor through an official regulator, not the platform itself.'
		]
	};

	const DEFAULT_TIPS = [
		'Verify the sender through a channel you already trust, not one provided in the message itself.',
		"If a message pressures you to act immediately, that pressure is itself a warning sign."
	];

	let { category = null, class: className = '' } = $props();
	const tips = $derived(TIPS_BY_CATEGORY[category] ?? DEFAULT_TIPS);
</script>

<div class={cn('glass-panel mx-auto max-w-xl rounded-xl px-5 py-4', className)}>
	<h3 class="mb-3 flex items-center gap-1.5 text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
		<Lightbulb size={13} aria-hidden="true" /> Safety tips
		<span class="ml-auto font-mono text-[10px] normal-case" style="color: var(--text-tertiary);">curated guidance</span>
	</h3>
	<ul class="flex flex-col gap-2 text-sm" style="color: var(--text-secondary);">
		{#each tips as tip (tip)}
			<li class="flex items-start gap-2">
				<span class="mt-1.5 h-1 w-1 shrink-0 rounded-full" style="background: var(--accent-secondary);"></span>
				{tip}
			</li>
		{/each}
	</ul>
</div>
