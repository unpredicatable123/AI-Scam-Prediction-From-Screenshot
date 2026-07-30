<script>
	import { cn } from '$lib/utils/cn';
	import Tags from '@lucide/svelte/icons/tags';

	// Reasons already carry the real matched term inside quotes (nlg.py's
	// `_quote_first_match`) — chips are derived from that, never a separate
	// keyword list, so a chip can never appear without genuine evidence.
	const GROUP_EXPLANATIONS = {
		urgency: 'Urgency language pressures a fast decision before you can verify anything.',
		authority: 'Claiming an official identity is a common way to make demands feel legitimate.',
		reward: 'Promising a prize or reward is used to lower your guard before the ask.',
		threat: 'Threatening a consequence pressures action through fear rather than fact.',
		secrecy: 'Asking you to keep something secret prevents you from checking with someone else.',
		financial_request: 'A request for money, especially upfront, is the core mechanic of most scams.',
		credential_request: 'Legitimate services never ask you to send an OTP, PIN, or password like this.',
		contact_shift: 'Moving off-platform removes the safety checks the original app provides.',
		url_risk: 'This link has characteristics — like a shortener or raw IP — designed to hide its destination.',
		qr_risk: 'A QR code can request a payment or send you somewhere without a visible URL to check first.',
		scarcity: 'Manufactured scarcity pressures a decision before you have time to check.',
		greed: 'Unrealistic earnings promises exploit the appeal of easy money.',
		romance: 'Emotional or romantic language builds trust that gets exploited for a later ask.',
		investment_pitch: 'Investment pitches with guaranteed returns are a classic red flag — no legitimate investment is risk-free.',
		lottery: "You can't win a lottery you never entered — this is the setup for an advance-fee scam.",
		job_offer: 'Vague, too-easy job offers are a common front for advance-fee or money-mule scams.',
		payment_identifier: 'A real payment identifier means this message is actively trying to move money, not just talking about it.',
		brand_impersonation: 'A near-miss spelling of a real brand name is a deliberate attempt to look legitimate at a glance.'
	};

	let { reasons = [], class: className = '' } = $props();

	const chips = $derived.by(() => {
		const seen = new Set();
		const out = [];
		for (const r of reasons) {
			for (const m of r.text.matchAll(/"([^"]+)"/g)) {
				const term = m[1];
				const key = term.toLowerCase();
				if (seen.has(key)) continue;
				seen.add(key);
				out.push({ term, group: r.group, explanation: GROUP_EXPLANATIONS[r.group] ?? r.text });
			}
		}
		return out;
	});
</script>

{#if chips.length > 0}
	<div class={cn('glass-panel mx-auto max-w-xl rounded-xl px-5 py-4', className)}>
		<h3 class="mb-3 flex items-center gap-1.5 text-xs font-medium tracking-wide uppercase" style="color: var(--text-tertiary);">
			<Tags size={13} aria-hidden="true" /> Suspicious terms detected
		</h3>
		<div class="flex flex-wrap gap-2">
			{#each chips as chip (chip.term)}
				<div class="group relative">
					<span
						class="inline-flex cursor-default items-center rounded-full px-3 py-1 font-mono text-xs font-medium"
						style="background: color-mix(in oklch, var(--color-risk-high) 18%, transparent); color: var(--color-risk-high);"
					>
						{chip.term}
					</span>
					<div
						role="tooltip"
						class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 w-56 -translate-x-1/2 rounded-lg px-3 py-2 text-[11px] leading-relaxed opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100"
						style="background: var(--surface-overlay); color: var(--text-secondary); border: 1px solid var(--border-default);"
					>
						{chip.explanation}
					</div>
				</div>
			{/each}
		</div>
	</div>
{/if}
