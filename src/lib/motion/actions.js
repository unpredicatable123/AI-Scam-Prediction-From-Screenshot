import { browser } from '$app/environment';
import { gsap, ScrollTrigger, prefersReducedMotion } from './gsap';

/**
 * Scroll-reveal primitive used throughout the marketing page to make every
 * section animate into the next rather than appearing abruptly. Falls back
 * to a static, fully-opaque end state under prefers-reduced-motion instead
 * of playing the tween at zero duration.
 *
 * Usage: <section use:reveal={{ y: 32, delay: 0.1 }}>
 */
export function reveal(node, options = {}) {
	if (!browser) return {};

	const { y = 24, x = 0, duration = 0.9, delay = 0, once = true, start = 'top 85%' } = options;

	if (prefersReducedMotion()) {
		gsap.set(node, { opacity: 1, x: 0, y: 0 });
		return {};
	}

	gsap.set(node, { opacity: 0, x, y });
	const tween = gsap.to(node, {
		opacity: 1,
		x: 0,
		y: 0,
		duration,
		delay,
		ease: 'power3.out',
		scrollTrigger: { trigger: node, start, once }
	});

	return {
		update(next) {
			options = { ...options, ...next };
		},
		destroy() {
			tween.scrollTrigger?.kill();
			tween.kill();
		}
	};
}

/**
 * Lazy-mount primitive for heavy visual components (the OGL globe/particle
 * canvases). Fires `onEnter` once the node approaches the viewport so a
 * dynamic import() can be triggered from the component, keeping WebGL code
 * out of the initial JS bundle entirely (see docs/BLUEPRINT.md §3.1).
 *
 * Usage: <div use:inView={{ onEnter: () => (mounted = true) }}>
 */
export function inView(node, { onEnter, rootMargin = '200px', once = true } = {}) {
	if (!browser || typeof IntersectionObserver === 'undefined') {
		onEnter?.();
		return {};
	}

	const observer = new IntersectionObserver(
		(entries) => {
			for (const entry of entries) {
				if (entry.isIntersecting) {
					onEnter?.();
					if (once) observer.disconnect();
				}
			}
		},
		{ rootMargin }
	);
	observer.observe(node);

	return { destroy: () => observer.disconnect() };
}

export { gsap, ScrollTrigger, prefersReducedMotion };
