<script>
	import { prefersReducedMotion } from '$lib/motion/actions';

	let { value = 0, decimals = 0, suffix = '', duration = 900, class: className = '' } = $props();

	let displayed = $state(0);
	let raf;

	$effect(() => {
		const target = value;
		if (prefersReducedMotion()) {
			displayed = target;
			return;
		}
		cancelAnimationFrame(raf);
		const start = performance.now();
		const from = displayed;
		const tick = (now) => {
			const t = Math.min(1, (now - start) / duration);
			const eased = 1 - Math.pow(1 - t, 3);
			displayed = from + (target - from) * eased;
			if (t < 1) raf = requestAnimationFrame(tick);
			else displayed = target;
		};
		raf = requestAnimationFrame(tick);
		return () => cancelAnimationFrame(raf);
	});
</script>

<span class={className}>{displayed.toFixed(decimals)}{suffix}</span>
