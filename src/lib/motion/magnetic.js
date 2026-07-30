import { browser } from '$app/environment';
import { prefersReducedMotion } from './gsap';

/**
 * Subtle "magnetic" pull toward the cursor within a small radius — a common
 * premium-feeling micro-interaction on primary CTAs (Linear, Vercel). Pure
 * `transform`, GPU-accelerated, no layout impact. No-ops under
 * prefers-reduced-motion or on touch (pointer never "hovers" on touch, so
 * the effect would just never reset without a matching leave event).
 *
 * Usage: <button use:magnetic={{ strength: 0.35 }}>
 */
export function magnetic(node, options = {}) {
	if (!browser || prefersReducedMotion() || !window.matchMedia('(pointer: fine)').matches) return {};

	let { strength = 0.3, radius = 80 } = options;

	function onMove(e) {
		const rect = node.getBoundingClientRect();
		const cx = rect.left + rect.width / 2;
		const cy = rect.top + rect.height / 2;
		const dx = e.clientX - cx;
		const dy = e.clientY - cy;
		const dist = Math.hypot(dx, dy);
		if (dist > radius) {
			node.style.transform = '';
			return;
		}
		node.style.transform = `translate(${dx * strength}px, ${dy * strength}px)`;
	}

	function onLeave() {
		node.style.transform = '';
	}

	node.style.transition = 'transform 0.2s var(--ease-out-expo)';
	window.addEventListener('pointermove', onMove, { passive: true });
	node.addEventListener('pointerleave', onLeave);

	return {
		update(next) {
			options = { ...options, ...next };
			strength = options.strength ?? 0.3;
			radius = options.radius ?? 80;
		},
		destroy() {
			window.removeEventListener('pointermove', onMove);
			node.removeEventListener('pointerleave', onLeave);
		}
	};
}
