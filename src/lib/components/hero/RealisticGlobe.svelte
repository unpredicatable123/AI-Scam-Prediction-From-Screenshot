<script>
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { prefersReducedMotion } from '$lib/motion/gsap';

	// Photoreal Earth: real NASA Blue Marble satellite imagery + city-lights
	// night texture + topology bump + ocean specular mask. The images are
	// vendored into static/textures/ (originally shipped as examples in the
	// `three-globe` package; NASA Visible Earth imagery is public domain) and
	// served locally — no CDN, no runtime network fetch, so the hero still
	// works offline like the rest of this local-first project.
	//
	// They live in static/ rather than being import()ed because three-globe's
	// package.json `exports` map has no subpath entries, so deep asset imports
	// are blocked by the resolver — and it keeps ~8 MB of imagery out of the
	// bundler entirely.
	//
	// Three.js is loaded via dynamic import() inside onMount, so it is
	// code-split out of the initial bundle and never touches SSR.

	const TEX = {
		day: '/textures/earth-blue-marble.jpg',
		night: '/textures/earth-night.jpg',
		bump: '/textures/earth-topology.png',
		water: '/textures/earth-water.png',
		clouds: '/textures/earth-clouds.png'
	};

	let { class: className = '' } = $props();

	/** @type {HTMLDivElement} */
	let containerEl;
	let cleanup = () => {};

	// Real cities across many countries — markers sit on land rather than
	// truly random lat/lon, which would drop half of them in open ocean.
	const HOTSPOT_POOL = [
		{ lat: 40.71, lon: -74.01, city: 'New York' },
		{ lat: 51.51, lon: -0.13, city: 'London' },
		{ lat: 19.08, lon: 72.88, city: 'Mumbai' },
		{ lat: 6.52, lon: 3.38, city: 'Lagos' },
		{ lat: -23.55, lon: -46.63, city: 'São Paulo' },
		{ lat: 1.35, lon: 103.82, city: 'Singapore' },
		{ lat: -33.87, lon: 151.21, city: 'Sydney' },
		{ lat: 35.68, lon: 139.69, city: 'Tokyo' },
		{ lat: 55.75, lon: 37.62, city: 'Moscow' },
		{ lat: 28.61, lon: 77.21, city: 'Delhi' },
		{ lat: 39.9, lon: 116.4, city: 'Beijing' },
		{ lat: 48.86, lon: 2.35, city: 'Paris' },
		{ lat: 52.52, lon: 13.41, city: 'Berlin' },
		{ lat: 25.2, lon: 55.27, city: 'Dubai' },
		{ lat: -26.2, lon: 28.05, city: 'Johannesburg' },
		{ lat: 19.43, lon: -99.13, city: 'Mexico City' },
		{ lat: 41.01, lon: 28.98, city: 'Istanbul' },
		{ lat: 13.76, lon: 100.5, city: 'Bangkok' },
		{ lat: -34.6, lon: -58.38, city: 'Buenos Aires' },
		{ lat: 37.57, lon: 126.98, city: 'Seoul' },
		{ lat: 30.04, lon: 31.24, city: 'Cairo' },
		{ lat: 43.65, lon: -79.38, city: 'Toronto' }
	];

	onMount(() => {
		let disposed = false;

		(async () => {
			const THREE = await import('three');
			if (disposed || !containerEl) return;

			const reduced = prefersReducedMotion();
			const RADIUS = 1;

			const scene = new THREE.Scene();
			const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
			camera.position.set(0, 0.35, 3.05);
			camera.lookAt(0, 0, 0);

			const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
			renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
			renderer.setClearColor(0x000000, 0);
			containerEl.appendChild(renderer.domElement);
			renderer.domElement.style.display = 'block';
			renderer.domElement.style.width = '100%';
			renderer.domElement.style.height = '100%';

			const loader = new THREE.TextureLoader();
			const load = (url) =>
				new Promise((res) => loader.load(url, (t) => res(t), undefined, () => res(null)));

			const [dayTex, nightTex, bumpTex, waterTex] = await Promise.all([
				load(TEX.day),
				load(TEX.night),
				load(TEX.bump),
				load(TEX.water)
			]);
			if (disposed) return;

			for (const t of [dayTex, nightTex, bumpTex, waterTex]) {
				if (t) t.colorSpace = THREE.SRGBColorSpace;
			}

			// ---- Earth: day/night terminator shader ---------------------------
			// Standard equirectangular day/night blend — the night side shows
			// real city lights instead of going flat black.
			const earthGroup = new THREE.Group();
			earthGroup.rotation.z = (23.4 * Math.PI) / 180; // real axial tilt
			scene.add(earthGroup);

			// Camera-facing-ish rather than physically arbitrary: with the
			// camera fixed near +z, a sun vector dominated by x/y (as this was)
			// puts the bright side edge-on much of the rotation, so the visible
			// hemisphere reads as night far more often than not. Biasing z
			// higher keeps the lit side facing the viewer through more of the
			// spin — a deliberate "always looks good" choice over physical
			// accuracy, which is the right tradeoff for a decorative hero.
			const sunDirection = new THREE.Vector3(0.45, 0.25, 1.0).normalize();

			const earthMat = new THREE.ShaderMaterial({
				uniforms: {
					dayTexture: { value: dayTex },
					nightTexture: { value: nightTex },
					bumpTexture: { value: bumpTex },
					waterTexture: { value: waterTex },
					sunDirection: { value: sunDirection }
				},
				vertexShader: `
					varying vec2 vUv;
					varying vec3 vNormal;
					void main() {
						vUv = uv;
						vNormal = normalize(normalMatrix * normal);
						gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
					}
				`,
				fragmentShader: `
					uniform sampler2D dayTexture;
					uniform sampler2D nightTexture;
					uniform sampler2D bumpTexture;
					uniform sampler2D waterTexture;
					uniform vec3 sunDirection;
					varying vec2 vUv;
					varying vec3 vNormal;

					void main() {
						vec3 normal = normalize(vNormal);
						float intensity = dot(normal, normalize(sunDirection));

						vec3 dayColor = texture2D(dayTexture, vUv).rgb;
						vec3 nightColor = texture2D(nightTexture, vUv).rgb;
						float water = texture2D(waterTexture, vUv).r;
						float relief = texture2D(bumpTexture, vUv).r;

						// subtle land relief shading, oceans stay smooth
						dayColor *= mix(1.0, 0.88 + relief * 0.30, 1.0 - water);
						// cool the oceans slightly toward the cyber-blue theme
						dayColor = mix(dayColor, dayColor * vec3(0.72, 0.88, 1.18), water * 0.45);

						// Wide terminator (was -0.18..0.32, now -0.7..0.1) so most of
						// the sphere reads as lit day-side at any given rotation,
						// rather than a narrow crescent. The "night" side isn't
						// pure city-lights-on-black either — it's washed with a
						// dim tint of the real day texture, so continents stay
						// legible instead of vanishing into the ocean-black of the
						// raw night-lights texture.
						float dayMix = smoothstep(-0.7, 0.1, intensity);
						vec3 nightLit = nightColor * 2.3 + dayColor * 0.3;
						vec3 color = mix(nightLit, dayColor * 1.08, dayMix);

						// Hard brightness floor: no pixel can go below 22% of its
						// own day-texture brightness, so nothing on the visible
						// hemisphere ever reads as "can't see it."
						color = max(color, dayColor * 0.22);

						// A tight, dim edge only — enough to keep the sphere from
						// reading as a flat disc, without the halo/bloom look.
						float rim = 1.0 - max(dot(normal, vec3(0.0, 0.0, 1.0)), 0.0);
						color += vec3(0.20, 0.34, 0.62) * pow(rim, 9.0) * 0.14;

						gl_FragColor = vec4(color, 1.0);
					}
				`
			});
			const earth = new THREE.Mesh(new THREE.SphereGeometry(RADIUS, 96, 96), earthMat);
			earthGroup.add(earth);

			// Atmosphere glow shell intentionally removed — the additive fresnel
			// halo read as a heavy blue bloom around the planet. The tight rim
			// term in the earth shader above is all that remains.

			// ---- Starfield ------------------------------------------------------
			const starCount = 1400;
			const starPos = new Float32Array(starCount * 3);
			for (let i = 0; i < starCount; i++) {
				const r = 18 + Math.random() * 24;
				const theta = Math.random() * Math.PI * 2;
				const phi = Math.acos(2 * Math.random() - 1);
				starPos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
				starPos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
				starPos[i * 3 + 2] = r * Math.cos(phi);
			}
			const starGeo = new THREE.BufferGeometry();
			starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
			const stars = new THREE.Points(
				starGeo,
				new THREE.PointsMaterial({ color: 0xc8d4ff, size: 0.09, sizeAttenuation: true, transparent: true, opacity: 0.85 })
			);
			scene.add(stars);

			// ---- Orbital rings ---------------------------------------------------
			const ringGroup = new THREE.Group();
			scene.add(ringGroup);
			// Kept deliberately faint — at higher opacity these read as decorative
			// sci-fi clutter rather than premium restraint.
			const ringSpecs = [
				{ r: 1.44, tilt: 0.42, color: 0x8f9bd0, op: 0.16 },
				{ r: 1.66, tilt: -0.55, color: 0x7d8ab8, op: 0.1 }
			];
			const rings = ringSpecs.map((s) => {
				const ring = new THREE.Mesh(
					new THREE.TorusGeometry(s.r, 0.0035, 8, 180),
					new THREE.MeshBasicMaterial({ color: s.color, transparent: true, opacity: s.op })
				);
				ring.rotation.x = Math.PI / 2 + s.tilt;
				ringGroup.add(ring);
				return ring;
			});

			// ---- Hotspot markers -------------------------------------------------
			function latLonToVec3(lat, lon, radius) {
				const phi = ((90 - lat) * Math.PI) / 180;
				const theta = ((lon + 180) * Math.PI) / 180;
				return new THREE.Vector3(
					-radius * Math.sin(phi) * Math.cos(theta),
					radius * Math.cos(phi),
					radius * Math.sin(phi) * Math.sin(theta)
				);
			}

			// Red "!" badge drawn once to a canvas, reused by every sprite.
			const badgeCanvas = document.createElement('canvas');
			badgeCanvas.width = badgeCanvas.height = 128;
			const bctx = badgeCanvas.getContext('2d');
			const g = bctx.createRadialGradient(64, 64, 4, 64, 64, 62);
			g.addColorStop(0, 'rgba(255,90,80,1)');
			g.addColorStop(0.42, 'rgba(235,45,45,0.92)');
			g.addColorStop(1, 'rgba(235,45,45,0)');
			bctx.fillStyle = g;
			bctx.beginPath();
			bctx.arc(64, 64, 62, 0, Math.PI * 2);
			bctx.fill();
			bctx.fillStyle = '#fff';
			bctx.font = 'bold 62px sans-serif';
			bctx.textAlign = 'center';
			bctx.textBaseline = 'middle';
			bctx.fillText('!', 64, 66);
			const badgeTex = new THREE.CanvasTexture(badgeCanvas);
			badgeTex.colorSpace = THREE.SRGBColorSpace;

			// Random subset each load, so it differs between visits.
			const picked = [...HOTSPOT_POOL].sort(() => Math.random() - 0.5).slice(0, 9);

			const markers = picked.map((h, i) => {
				const pos = latLonToVec3(h.lat, h.lon, RADIUS * 1.012);
				const sprite = new THREE.Sprite(
					new THREE.SpriteMaterial({ map: badgeTex, transparent: true, depthTest: true, depthWrite: false })
				);
				sprite.position.copy(pos);
				sprite.scale.setScalar(0.115);
				// Parented to earthGroup, so markers rotate with the planet and
				// stay locked to their real geographic coordinates.
				earthGroup.add(sprite);

				// radar ping ring, laid flat against the sphere surface
				const ring = new THREE.Mesh(
					new THREE.RingGeometry(0.035, 0.045, 48),
					new THREE.MeshBasicMaterial({
						color: 0xff4040,
						transparent: true,
						opacity: 0.85,
						side: THREE.DoubleSide,
						depthWrite: false
					})
				);
				ring.position.copy(latLonToVec3(h.lat, h.lon, RADIUS * 1.006));
				ring.lookAt(pos.clone().multiplyScalar(2));
				earthGroup.add(ring);

				return { sprite, ring, pos, phase: Math.random() * Math.PI * 2, pingOffset: (i / 9) * 3.2 };
			});

			// ---- Scam-network arcs between a few hotspots ------------------------
			const arcs = [];
			for (let i = 0; i < 5 && i + 1 < markers.length; i++) {
				const a = markers[i].pos;
				const b = markers[(i * 3 + 2) % markers.length].pos;
				const mid = a.clone().add(b).multiplyScalar(0.5).setLength(RADIUS * (1.18 + a.distanceTo(b) * 0.14));
				const curve = new THREE.QuadraticBezierCurve3(a.clone().multiplyScalar(1.01), mid, b.clone().multiplyScalar(1.01));
				const pts = curve.getPoints(64);
				const geo = new THREE.BufferGeometry().setFromPoints(pts);
				const mat = new THREE.LineBasicMaterial({ color: 0xff5a5a, transparent: true, opacity: 0.34 });
				const line = new THREE.Line(geo, mat);
				earthGroup.add(line);

				// a travelling packet dot along the arc
				const dot = new THREE.Mesh(
					new THREE.SphereGeometry(0.012, 10, 10),
					new THREE.MeshBasicMaterial({ color: 0xff8a6a })
				);
				earthGroup.add(dot);
				arcs.push({ curve, dot, offset: Math.random() });
			}

			// ---- Clouds (deferred: 4.9 MB, must not block first paint) ----------
			let clouds = null;
			if (!reduced) {
				loader.load(TEX.clouds, (tex) => {
					if (disposed) return;
					tex.colorSpace = THREE.SRGBColorSpace;
					clouds = new THREE.Mesh(
						new THREE.SphereGeometry(RADIUS * 1.015, 64, 64),
						new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0.34, depthWrite: false })
					);
					earthGroup.add(clouds);
				});
			}

			// ---- Sizing ----------------------------------------------------------
			function resize() {
				const w = containerEl.clientWidth;
				const h = containerEl.clientHeight;
				if (!w || !h) return;
				renderer.setSize(w, h, false);
				camera.aspect = w / h;
				camera.updateProjectionMatrix();
			}
			resize();
			const ro = new ResizeObserver(resize);
			ro.observe(containerEl);

			// ---- Render loop -----------------------------------------------------
			let visible = true;
			const io = new IntersectionObserver(([e]) => (visible = e.isIntersecting), { threshold: 0 });
			io.observe(containerEl);

			let raf = 0;
			const start = performance.now();

			function frame(now) {
				raf = requestAnimationFrame(frame);
				if (!visible) return; // don't burn GPU while scrolled away
				const t = (now - start) / 1000;

				earthGroup.rotation.y = t * 0.075;
				if (clouds) clouds.rotation.y = t * 0.021;
				rings[0].rotation.z = t * 0.12;
				rings[1].rotation.z = -t * 0.09;
				stars.rotation.y = t * 0.004;

				for (const m of markers) {
					const pulse = 0.85 + Math.sin(t * 2.4 + m.phase) * 0.18;
					m.sprite.scale.setScalar(0.115 * pulse);
					// radar ping: expand + fade, then restart
					const p = ((t + m.pingOffset) % 3.2) / 3.2;
					m.ring.scale.setScalar(1 + p * 3.4);
					m.ring.material.opacity = 0.75 * (1 - p);
				}

				for (const a of arcs) {
					const p = (t * 0.22 + a.offset) % 1;
					a.dot.position.copy(a.curve.getPoint(p));
				}

				renderer.render(scene, camera);
			}

			if (reduced) {
				renderer.render(scene, camera);
			} else {
				raf = requestAnimationFrame(frame);
			}

			cleanup = () => {
				disposed = true;
				if (raf) cancelAnimationFrame(raf);
				ro.disconnect();
				io.disconnect();
				scene.traverse((obj) => {
					if (obj.geometry) obj.geometry.dispose();
					if (obj.material) {
						const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
						for (const m of mats) {
							for (const k of Object.keys(m)) {
								const v = m[k];
								if (v && v.isTexture) v.dispose();
							}
							m.dispose();
						}
					}
				});
				renderer.dispose();
				renderer.domElement.remove();
			};
		})();

		return () => cleanup();
	});

	onDestroy(() => {
		if (!browser) return;
		cleanup();
	});
</script>

<div bind:this={containerEl} class={className} aria-hidden="true"></div>
