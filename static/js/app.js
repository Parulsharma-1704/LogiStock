/**
 * LogiStock — Core Web Application JavaScript
 * Features: Dark Emerald/Teal Theme helpers, Password toggles, button spinners,
 * Count-up animations, Tooltips, Skeleton shimmer removal, Login 3D Decorative Crate
 */

(function () {
  'use strict';

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isMobile = window.innerWidth < 768;

  // ── 1. Password Visibility Toggle ─────────────────────────────
  document.addEventListener('click', function (e) {
    const toggleBtn = e.target.closest('.password-toggle-btn');
    if (!toggleBtn) return;

    const targetInputId = toggleBtn.getAttribute('data-target') || 'password';
    const passwordInput = document.getElementById(targetInputId) || toggleBtn.parentElement.querySelector('input');
    const icon = toggleBtn.querySelector('i');

    if (passwordInput) {
      if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        if (icon) {
          icon.classList.remove('bi-eye');
          icon.classList.add('bi-eye-slash');
        }
      } else {
        passwordInput.type = 'password';
        if (icon) {
          icon.classList.remove('bi-eye-slash');
          icon.classList.add('bi-eye');
        }
      }
    }
  });

  // ── 2. Button Loading Spinner on Form Submit ──────────────────
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function (e) {
      if (!form.checkValidity()) return;

      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        const originalText = submitBtn.innerHTML;
        submitBtn.setAttribute('data-original-text', originalText);
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Processing...';

        setTimeout(() => {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }, 8000);
      }
    });
  });

  // ── 3. VanillaTilt for Internal App Cards ─────────────────────
  if (typeof VanillaTilt !== 'undefined' && !prefersReducedMotion && !isMobile) {
    VanillaTilt.init(document.querySelectorAll('.stat-card, [data-tilt]'), {
      max: 8,
      speed: 350,
      glare: true,
      'max-glare': 0.12,
      scale: 1.01,
    });
  }

  // ── 4. Bootstrap Tooltip Initialization ───────────────────────
  if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  // ── 5. Count-Up Animation for Dashboard Stat Cards ───────────
  function countUp(el, target, prefix) {
    if (prefersReducedMotion) {
      el.textContent = (prefix || '') + Math.floor(target).toLocaleString('en-IN');
      return;
    }

    const duration = 1200;
    const fps = 60;
    const steps = duration / (1000 / fps);
    let current = 0;
    const increment = target / steps;
    const timer = setInterval(() => {
      current = Math.min(current + increment, target);
      el.textContent = (prefix || '') + Math.floor(current).toLocaleString('en-IN');
      if (current >= target) clearInterval(timer);
    }, 1000 / fps);
  }

  document.querySelectorAll('.stat-val[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count, 10) || 0;
    const prefix = el.dataset.prefix || '';
    countUp(el, target, prefix);
  });

  // ── 6. Low-Stock Progress Bars Animation ──────────────────────
  document.querySelectorAll('.ls-bar-fill[data-pct]').forEach(el => {
    const pct = el.dataset.pct;
    setTimeout(() => {
      el.style.width = pct + '%';
    }, 200);
  });

  // ── 7. Chart Skeleton Shimmer Removal ─────────────────────────
  window.hideChartSkeleton = function (chartId) {
    const skeleton = document.getElementById(chartId + '-skeleton');
    if (skeleton) {
      skeleton.style.display = 'none';
    }
  };

  // ── 8. Login Brand Panel Decorative 3D Emerald Object ─────────
  const loginCanvasContainer = document.getElementById('threejs-login-canvas');
  if (loginCanvasContainer) {
    function isWebGLAvailable() {
      try {
        const c = document.createElement('canvas');
        return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
      } catch (e) {
        return false;
      }
    }

    if (!isWebGLAvailable() || typeof THREE === 'undefined') {
      loginCanvasContainer.innerHTML = `
        <div class="d-flex align-items-center justify-content-center h-100">
          <div class="css-3d-fallback" style="width:100px; height:100px;">
            <div class="cube-face face-front" style="width:100px; height:100px; transform: rotateY(0deg) translateZ(50px);"></div>
            <div class="cube-face face-back" style="width:100px; height:100px; transform: rotateY(180deg) translateZ(50px);"></div>
            <div class="cube-face face-right" style="width:100px; height:100px; transform: rotateY(90deg) translateZ(50px);"></div>
            <div class="cube-face face-left" style="width:100px; height:100px; transform: rotateY(-90deg) translateZ(50px);"></div>
            <div class="cube-face face-top" style="width:100px; height:100px; transform: rotateX(90deg) translateZ(50px);"></div>
            <div class="cube-face face-bottom" style="width:100px; height:100px; transform: rotateX(-90deg) translateZ(50px);"></div>
          </div>
        </div>
      `;
    } else {
      try {
        const width = loginCanvasContainer.clientWidth || 320;
        const height = loginCanvasContainer.clientHeight || 200;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
        camera.position.set(0, 0, 5.5);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
        loginCanvasContainer.appendChild(renderer.domElement);

        // Lights (Multi-tone: Emerald + Cyan + Amber)
        const amb = new THREE.AmbientLight(0x07211b, 2.5);
        scene.add(amb);

        const mintRim = new THREE.PointLight(0x34d399, 4, 15);
        mintRim.position.set(3, 2, 3);
        scene.add(mintRim);

        const cyanRim = new THREE.PointLight(0x06b6d4, 3.5, 15);
        cyanRim.position.set(-3, -2, 2);
        scene.add(cyanRim);

        const amberRim = new THREE.PointLight(0xf59e0b, 2.5, 12);
        amberRim.position.set(1, -3, 1.5);
        scene.add(amberRim);

        // Glossy Emerald Crate
        const group = new THREE.Group();
        const geo = new THREE.BoxGeometry(1.8, 1.8, 1.8);
        const mat = new THREE.MeshPhysicalMaterial({
          color: 0x063126,
          metalness: 0.85,
          roughness: 0.18,
          clearcoat: 1.0,
          emissive: 0x074636,
          emissiveIntensity: 0.35,
        });
        const mesh = new THREE.Mesh(geo, mat);
        group.add(mesh);

        const edges = new THREE.EdgesGeometry(geo);
        const lineMat = new THREE.LineBasicMaterial({ color: 0x34d399, opacity: 0.85, transparent: true });
        group.add(new THREE.LineSegments(edges, lineMat));

        // Subtle Orbit Ring (Cyan)
        const ringGeo = new THREE.TorusGeometry(1.6, 0.02, 16, 64);
        const ringMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4, opacity: 0.65, transparent: true });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = Math.PI / 3;
        group.add(ring);

        scene.add(group);

        let animId = null;
        let isTabActive = true;

        function animateLogin() {
          if (!isTabActive) return;
          animId = requestAnimationFrame(animateLogin);
          if (!prefersReducedMotion) {
            group.rotation.y += 0.012;
            group.rotation.x += 0.006;
          }
          renderer.render(scene, camera);
        }

        animateLogin();

        document.addEventListener('visibilitychange', function () {
          if (document.hidden) {
            isTabActive = false;
            if (animId) cancelAnimationFrame(animId);
          } else {
            isTabActive = true;
            animateLogin();
          }
        });
      } catch (e) {
        console.warn('Login 3D canvas failed:', e);
      }
    }
  }

})();
