import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { browser } from '$app/environment';

if (browser) {
	gsap.registerPlugin(ScrollTrigger);
	gsap.defaults({ ease: 'power3.out', duration: 0.8 });
}

/**
 * Single source of truth for the reduced-motion check. GSAP timelines branch
 * on this explicitly rather than relying on the CSS-only safety net in
 * app.css, because a scroll-pinned sequence left at zero duration mid-tween
 * can strand the page in a broken visual state instead of a clean one.
 */
export function prefersReducedMotion() {
	return browser && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export { gsap, ScrollTrigger };
