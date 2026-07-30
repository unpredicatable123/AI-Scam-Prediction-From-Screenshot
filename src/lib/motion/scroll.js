import { gsap, ScrollTrigger, prefersReducedMotion } from './gsap';

/**
 * Scroll-scrubbed timeline factory — the mechanism behind every "story that
 * unfolds as you scroll" section (pipeline flow, OCR scan-line, fusion
 * convergence). Distinct from the `reveal` action in actions.js, which plays
 * once on enter; a scrub timeline's progress is bound 1:1 to scroll position.
 *
 * Returns null under prefers-reduced-motion. Callers must handle that by
 * calling gsap.set(...) directly to the scene's final state, since a
 * scroll-tied animation has no single "duration" to skip — there is no
 * partial-progress state that is both instant and non-jarring.
 */
export function scrollTimeline(trigger, { start = 'top 75%', end = 'bottom 60%', scrub = 0.8, pin = false } = {}) {
	if (prefersReducedMotion()) return null;
	return gsap.timeline({
		scrollTrigger: { trigger, start, end, scrub, pin }
	});
}

export { gsap, ScrollTrigger, prefersReducedMotion };
