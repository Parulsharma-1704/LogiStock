/**
 * LogiStock — Landing Page 3D & Interactive Effects
 * Features: Three.js Glossy Emerald Crates, Multi-tone Rim Lighting, CSS 3D Fallback, Tilt & Count-up
 */

(function () {
  'use strict';

  // Check prefers-reduced-motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isMobile = window.innerWidth < 768;

  // ── WebGL Capability Check ─────────────────────────────────────
  function isWebGLAvailable() {
    try {
      const canvas = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
    } catch (e) {
      return false;
    }
  }

  // ── CSS 3D Cube Fallback ───────────────────────────────────────
  function injectCSS3DFallback(container) {
    if (!container) return;
    container.innerHTML = `
      <div class="d-flex align-items-center justify-content-center h-100">
        <div class="css-3d-fallback">
          <div class="cube-face face-front"></div>
          <div class="cube-face face-back"></div>
          <div class="cube-face face-right"></div>
          <div class="cube-face face-left"></div>
          <div class="cube-face face-top"></div>
          <div class="cube-face face-bottom"></div>
        </div>
      </div>
    `;
  }

  // ── 1. Three.js Hero 3D Emerald Shipping Crate ────────────────
  const canvasContainer = document.getElementById('threejs-hero-canvas');
  let scene, camera, renderer, crateGroup, starPoints;
  let isTabVisible = true;
  let animationFrameId = null;

  // Mouse parallax
  let mouseX = 0;
  let mouseY = 0;
  let targetRotationX = 0;
  let targetRotationY = 0;

  function initThreeJS() {
    if (!canvasContainer) return;

    if (!isWebGLAvailable() || typeof THREE === 'undefined') {
      injectCSS3DFallback(canvasContainer);
      return;
    }

    try {
      const width = canvasContainer.clientWidth || 500;
      const height = canvasContainer.clientHeight || 450;

      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
      camera.position.set(0, 0, 7.5);

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1.5 : 2));
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.35;
      canvasContainer.appendChild(renderer.domElement);

      // ── Emerald, Cyan & Amber Multi-Color Rim Lighting ──
      const ambientLight = new THREE.AmbientLight(0x07211b, 2.6);
      scene.add(ambientLight);

      // Mint Rim Light
      const mintLight = new THREE.PointLight(0x34d399, 4.5, 25);
      mintLight.position.set(4, 3, 4);
      scene.add(mintLight);

      // Electric Cyan Rim Light
      const cyanLight = new THREE.PointLight(0x06b6d4, 4, 25);
      cyanLight.position.set(-4, -2, 3);
      scene.add(cyanLight);

      // Warm Amber Accent Light
      const amberLight = new THREE.PointLight(0xf59e0b, 3.5, 20);
      amberLight.position.set(2, -4, 2);
      scene.add(amberLight);

      // Emerald Key Light
      const emeraldLight = new THREE.DirectionalLight(0x10b981, 2.5);
      emeraldLight.position.set(0, 6, 2);
      scene.add(emeraldLight);

      // ── Crate Group ──
      crateGroup = new THREE.Group();

      // Main Glossy Emerald Shipping Crate
      const crateGeo = new THREE.BoxGeometry(2.4, 2.2, 2.4);
      const crateMat = new THREE.MeshPhysicalMaterial({
        color: 0x063126,
        metalness: 0.82,
        roughness: 0.18,
        clearcoat: 1.0,
        clearcoatRoughness: 0.08,
        reflectivity: 0.95,
        emissive: 0x052e24,
        emissiveIntensity: 0.45,
      });
      const mainCrate = new THREE.Mesh(crateGeo, crateMat);
      crateGroup.add(mainCrate);

      // Mint Wireframe Edges
      const edgesGeo = new THREE.EdgesGeometry(crateGeo);
      const edgesMat = new THREE.LineBasicMaterial({
        color: 0x34d399,
        linewidth: 2,
        transparent: true,
        opacity: 0.85,
      });
      const wireframe = new THREE.LineSegments(edgesGeo, edgesMat);
      crateGroup.add(wireframe);

      // Stacked Upper Crate (Deep Teal & Electric Cyan)
      const smallCrateGeo = new THREE.BoxGeometry(1.3, 1.1, 1.3);
      const smallCrateMat = new THREE.MeshPhysicalMaterial({
        color: 0x083344,
        metalness: 0.88,
        roughness: 0.22,
        clearcoat: 0.9,
        emissive: 0x0e7490,
        emissiveIntensity: 0.35,
      });
      const smallCrate = new THREE.Mesh(smallCrateGeo, smallCrateMat);
      smallCrate.position.set(0.4, 1.65, -0.2);
      smallCrate.rotation.y = 0.35;
      crateGroup.add(smallCrate);

      const smallEdgesGeo = new THREE.EdgesGeometry(smallCrateGeo);
      const smallEdgesMat = new THREE.LineBasicMaterial({
        color: 0x22d3ee,
        linewidth: 2,
        transparent: true,
        opacity: 0.9,
      });
      const smallWireframe = new THREE.LineSegments(smallEdgesGeo, smallEdgesMat);
      smallWireframe.position.copy(smallCrate.position);
      smallWireframe.rotation.copy(smallCrate.rotation);
      crateGroup.add(smallWireframe);

      // Orbiting Hologram Ring (Aqua/Cyan)
      const ringGeo = new THREE.TorusGeometry(2.3, 0.025, 16, 100);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x06b6d4,
        transparent: true,
        opacity: 0.7,
      });
      const orbitRing = new THREE.Mesh(ringGeo, ringMat);
      orbitRing.rotation.x = Math.PI / 2.8;
      crateGroup.add(orbitRing);

      scene.add(crateGroup);

      // ── Multi-tone Particle Starfield (Mint, Cyan & Warm Gold) ──
      const starCount = isMobile ? 120 : 280;
      const starGeo = new THREE.BufferGeometry();
      const starPositions = new Float32Array(starCount * 3);
      const starColors = new Float32Array(starCount * 3);

      const colorPalette = [
        new THREE.Color(0x34d399), // Mint
        new THREE.Color(0x06b6d4), // Cyan
        new THREE.Color(0xfbbf24), // Gold/Amber
        new THREE.Color(0x6ee7b7), // Light Mint
      ];

      for (let i = 0; i < starCount; i++) {
        const i3 = i * 3;
        starPositions[i3] = (Math.random() - 0.5) * 16;
        starPositions[i3 + 1] = (Math.random() - 0.5) * 16;
        starPositions[i3 + 2] = (Math.random() - 0.5) * 12;

        const c = colorPalette[Math.floor(Math.random() * colorPalette.length)];
        starColors[i3] = c.r;
        starColors[i3 + 1] = c.g;
        starColors[i3 + 2] = c.b;
      }
      starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
      starGeo.setAttribute('color', new THREE.BufferAttribute(starColors, 3));

      const starMat = new THREE.PointsMaterial({
        size: 0.05,
        transparent: true,
        opacity: 0.8,
        vertexColors: true,
      });
      starPoints = new THREE.Points(starGeo, starMat);
      scene.add(starPoints);

      // Event Listeners
      window.addEventListener('resize', onWindowResize, false);
      if (!isMobile) {
        window.addEventListener('mousemove', onMouseMove, false);
      }

      animate();
    } catch (err) {
      console.warn('Three.js initialization failed, using CSS 3D fallback:', err);
      injectCSS3DFallback(canvasContainer);
    }
  }

  function onMouseMove(e) {
    if (prefersReducedMotion) return;
    const halfX = window.innerWidth / 2;
    const halfY = window.innerHeight / 2;
    mouseX = (e.clientX - halfX) / halfX;
    mouseY = (e.clientY - halfY) / halfY;

    targetRotationY = mouseX * 0.45;
    targetRotationX = mouseY * 0.3;
  }

  function onWindowResize() {
    if (!canvasContainer || !camera || !renderer) return;
    const width = canvasContainer.clientWidth;
    const height = canvasContainer.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }

  // Animation Loop with Visibility & Reduced-Motion Respect
  function animate() {
    if (!isTabVisible) return;

    animationFrameId = requestAnimationFrame(animate);

    const now = performance.now();
    const t = now * 0.001;

    if (crateGroup && !prefersReducedMotion) {
      // Gentle floating up/down
      crateGroup.position.y = Math.sin(t * 1.5) * 0.16;

      // Smooth idle rotation + mouse parallax lerp
      crateGroup.rotation.y += (targetRotationY + 0.35 + Math.sin(t * 0.5) * 0.12 - crateGroup.rotation.y) * 0.04;
      crateGroup.rotation.x += (targetRotationX + 0.2 - crateGroup.rotation.x) * 0.04;
      crateGroup.rotation.z = Math.sin(t * 1.1) * 0.035;
    }

    if (starPoints && !prefersReducedMotion) {
      starPoints.rotation.y = t * 0.015;
    }

    if (renderer && scene && camera) {
      renderer.render(scene, camera);
    }
  }

  // Pause when tab hidden
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      isTabVisible = false;
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    } else {
      isTabVisible = true;
      animate();
    }
  });

  // ── 2. Stat Numbers Count-Up ──────────────────────────────────
  function initCountUp() {
    const statElements = document.querySelectorAll('.h-stat-number[data-target]');
    if (!statElements.length) return;

    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = parseFloat(el.getAttribute('data-target')) || 0;
          const prefix = el.getAttribute('data-prefix') || '';
          const suffix = el.getAttribute('data-suffix') || '';
          const isDecimal = String(target).includes('.');

          if (prefersReducedMotion) {
            el.textContent = prefix + (isDecimal ? target.toFixed(1) : Math.floor(target).toLocaleString('en-IN')) + suffix;
            obs.unobserve(el);
            return;
          }

          let current = 0;
          const duration = 1400;
          const steps = 45;
          const increment = target / steps;
          const intervalTime = duration / steps;

          const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
              current = target;
              clearInterval(timer);
            }
            el.textContent = prefix + (isDecimal ? current.toFixed(1) : Math.floor(current).toLocaleString('en-IN')) + suffix;
          }, intervalTime);

          obs.unobserve(el);
        }
      });
    }, { threshold: 0.2 });

    statElements.forEach(el => observer.observe(el));
  }

  // ── 3. VanillaTilt for Landing Cards ──────────────────────────
  function initTilt() {
    if (prefersReducedMotion || isMobile) return;
    const tiltCards = document.querySelectorAll('[data-tilt]');
    if (typeof VanillaTilt !== 'undefined' && tiltCards.length) {
      VanillaTilt.init(tiltCards, {
        max: 10,
        speed: 380,
        glare: true,
        'max-glare': 0.18,
        scale: 1.015,
      });
    }
  }

  // ── Initialize ────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    initThreeJS();
    initCountUp();
    initTilt();
  });

})();
