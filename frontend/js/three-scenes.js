/* ═══════════════════════════════════════════════════════════════
   CODEVERSE — 3D Three.js Environments (three-scenes.js)
   Holographic Core with Orbiting Energy Rings & 3D Interactive
   Learning Journey Constellation Map
   ═══════════════════════════════════════════════════════════════ */

const ThreeScenes = (() => {
  const activeScenes = new Map();

  function createRenderer(container) {
    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);
    return renderer;
  }

  function handleResize(sceneData) {
    const { camera, renderer, container } = sceneData;
    if (!container || !renderer || !camera) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }

  // ── 1. Landing Page: 3D Holographic Codeverse Core ──────────
  function createLandingScene(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return null;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return null;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(55, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.z = 28;

    const renderer = createRenderer(container);

    // ── Particle Galaxy Matrix ────────────────────────────────
    const particleCount = 700;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const palette = [
      new THREE.Color(0x00f2fe), // neon cyan
      new THREE.Color(0xa855f7), // neon purple
      new THREE.Color(0x6366f1), // electric indigo
      new THREE.Color(0x00f5d4)  // emerald
    ];

    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      positions[i3]     = (Math.random() - 0.5) * 65;
      positions[i3 + 1] = (Math.random() - 0.5) * 45;
      positions[i3 + 2] = (Math.random() - 0.5) * 35;

      const col = palette[Math.floor(Math.random() * palette.length)];
      colors[i3]     = col.r;
      colors[i3 + 1] = col.g;
      colors[i3 + 2] = col.b;
    }

    const particleGeo = new THREE.BufferGeometry();
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMat = new THREE.PointsMaterial({
      size: 0.18,
      vertexColors: true,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // ── Central Holographic Quantum Core ──────────────────────
    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Inner Icosahedron
    const coreGeo = new THREE.IcosahedronGeometry(3.6, 1);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      wireframe: true,
      transparent: true,
      opacity: 0.45
    });
    const innerCore = new THREE.Mesh(coreGeo, coreMat);
    coreGroup.add(innerCore);

    // Orbiting Torus Ring 1
    const ring1Geo = new THREE.TorusGeometry(5.2, 0.05, 16, 64);
    const ring1Mat = new THREE.MeshBasicMaterial({
      color: 0xa855f7,
      transparent: true,
      opacity: 0.6
    });
    const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
    ring1.rotation.x = Math.PI / 3;
    coreGroup.add(ring1);

    // Orbiting Torus Ring 2
    const ring2Geo = new THREE.TorusGeometry(6.4, 0.04, 16, 64);
    const ring2Mat = new THREE.MeshBasicMaterial({
      color: 0x00f5d4,
      transparent: true,
      opacity: 0.5
    });
    const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
    ring2.rotation.y = Math.PI / 4;
    ring2.rotation.x = -Math.PI / 6;
    coreGroup.add(ring2);

    // Orbiting Quantum Nodes
    const nodeCount = 8;
    const nodeSpheres = [];
    for (let i = 0; i < nodeCount; i++) {
      const nodeGeo = new THREE.SphereGeometry(0.2, 8, 8);
      const nodeMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe });
      const node = new THREE.Mesh(nodeGeo, nodeMat);
      coreGroup.add(node);
      nodeSpheres.push({ mesh: node, speed: 0.8 + i * 0.2, radius: 5.2 + (i % 2) * 1.2, phase: (i * Math.PI * 2) / nodeCount });
    }

    // Mouse Tracking
    const mouse = { x: 0, y: 0 };
    const onMouseMove = (e) => {
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener('mousemove', onMouseMove, { passive: true });

    let animId;
    const clock = new THREE.Clock();

    function animate() {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      particles.rotation.y = elapsed * 0.025;
      particles.rotation.x = elapsed * 0.015;

      coreGroup.rotation.y = elapsed * 0.2;
      coreGroup.rotation.x = elapsed * 0.12;

      ring1.rotation.z = elapsed * 0.3;
      ring2.rotation.z = -elapsed * 0.25;

      // Animate nodes around rings
      nodeSpheres.forEach(n => {
        const angle = elapsed * n.speed + n.phase;
        n.mesh.position.x = Math.cos(angle) * n.radius;
        n.mesh.position.y = Math.sin(angle) * n.radius * 0.6;
        n.mesh.position.z = Math.sin(angle) * n.radius * 0.8;
      });

      // Smooth camera parallax
      camera.position.x += (mouse.x * 3.5 - camera.position.x) * 0.025;
      camera.position.y += (mouse.y * 2.5 - camera.position.y) * 0.025;
      camera.lookAt(scene.position);

      renderer.render(scene, camera);
    }
    animate();

    const sceneData = { camera, renderer, container, scene };
    const onResize = () => handleResize(sceneData);
    window.addEventListener('resize', onResize);

    const sceneRef = {
      cleanup: () => {
        cancelAnimationFrame(animId);
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('resize', onResize);
        renderer.dispose();
        particleGeo.dispose();
        particleMat.dispose();
        coreGeo.dispose();
        coreMat.dispose();
        ring1Geo.dispose();
        ring1Mat.dispose();
        ring2Geo.dispose();
        ring2Mat.dispose();
        if (renderer.domElement.parentNode) {
          renderer.domElement.parentNode.removeChild(renderer.domElement);
        }
      }
    };

    activeScenes.set(containerId, sceneRef);
    return sceneRef;
  }

  // ── 2. Dashboard: Interactive Coding Core ───────────────────
  function createDashboardScene(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return null;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return null;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.z = 6;

    const renderer = createRenderer(container);

    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Inner wireframe sphere
    const sphereGeo = new THREE.IcosahedronGeometry(1.6, 2);
    const sphereMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      wireframe: true,
      transparent: true,
      opacity: 0.5
    });
    const sphere = new THREE.Mesh(sphereGeo, sphereMat);
    coreGroup.add(sphere);

    // Outer quantum ring
    const ringGeo = new THREE.TorusGeometry(2.4, 0.03, 16, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xa855f7,
      transparent: true,
      opacity: 0.7
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 3;
    coreGroup.add(ring);

    // Small particle dust around core
    const dustCount = 120;
    const dustPos = new Float32Array(dustCount * 3);
    for (let i = 0; i < dustCount; i++) {
      const i3 = i * 3;
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      const r = 2.2 + Math.random() * 0.8;
      dustPos[i3]     = r * Math.sin(phi) * Math.cos(theta);
      dustPos[i3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      dustPos[i3 + 2] = r * Math.cos(phi);
    }
    const dustGeo = new THREE.BufferGeometry();
    dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
    const dustMat = new THREE.PointsMaterial({
      size: 0.08,
      color: 0x00f5d4,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending
    });
    const dust = new THREE.Points(dustGeo, dustMat);
    coreGroup.add(dust);

    let mouseX = 0, mouseY = 0;
    container.addEventListener('mousemove', (e) => {
      const rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    }, { passive: true });

    let animId;
    const clock = new THREE.Clock();

    function animate() {
      animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      coreGroup.rotation.y = t * 0.25;
      coreGroup.rotation.x = t * 0.15;
      ring.rotation.z = t * 0.4;
      dust.rotation.y = -t * 0.2;

      // Mouse response
      coreGroup.rotation.z += (mouseX * 0.2 - coreGroup.rotation.z) * 0.05;

      renderer.render(scene, camera);
    }
    animate();

    const sceneData = { camera, renderer, container, scene };
    const onResize = () => handleResize(sceneData);
    window.addEventListener('resize', onResize);

    const sceneRef = {
      cleanup: () => {
        cancelAnimationFrame(animId);
        window.removeEventListener('resize', onResize);
        renderer.dispose();
        sphereGeo.dispose();
        sphereMat.dispose();
        ringGeo.dispose();
        ringMat.dispose();
        dustGeo.dispose();
        dustMat.dispose();
        if (renderer.domElement.parentNode) {
          renderer.domElement.parentNode.removeChild(renderer.domElement);
        }
      }
    };

    activeScenes.set(containerId, sceneRef);
    return sceneRef;
  }

  // ── 3. Progress Page: 3D Learning Journey Constellation Map ──
  function createJourneyMapScene(containerId, nodesData, onNodeClick) {
    const container = document.getElementById(containerId);
    if (!container) return null;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return null;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(6, 0, 24);

    const renderer = createRenderer(container);
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const nodeMeshes = [];
    const lineCoords = [];

    // Colors for status
    const statusColors = {
      completed: 0x00f5d4, // emerald
      current:   0x00f2fe, // cyan
      unlocked:  0xffb703, // amber
      locked:    0x475569  // dim slate
    };

    // Create Nodes in 3D Space
    nodesData.forEach((node, i) => {
      const color = statusColors[node.status] || 0x6366f1;
      const isCurrent = node.status === 'current';

      // Outer ring for current/completed
      if (isCurrent || node.status === 'completed') {
        const haloGeo = new THREE.RingGeometry(0.8, 0.95, 32);
        const haloMat = new THREE.MeshBasicMaterial({
          color,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.6
        });
        const halo = new THREE.Mesh(haloGeo, haloMat);
        halo.position.set(node.x, node.y, node.z);
        scene.add(halo);
      }

      // Core Node Sphere
      const sphereGeo = new THREE.SphereGeometry(isCurrent ? 0.7 : 0.5, 16, 16);
      const sphereMat = new THREE.MeshBasicMaterial({
        color,
        wireframe: node.status === 'locked'
      });
      const mesh = new THREE.Mesh(sphereGeo, sphereMat);
      mesh.position.set(node.x, node.y, node.z);
      mesh.userData = { nodeData: node };
      scene.add(mesh);
      nodeMeshes.push(mesh);

      // Collect line coordinates for connections
      if (i > 0) {
        const prev = nodesData[i - 1];
        lineCoords.push(prev.x, prev.y, prev.z, node.x, node.y, node.z);
      }
    });

    // Connecting Beams between nodes
    if (lineCoords.length > 0) {
      const lineGeo = new THREE.BufferGeometry();
      lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(lineCoords, 3));
      const lineMat = new THREE.LineBasicMaterial({
        color: 0x00f2fe,
        transparent: true,
        opacity: 0.35
      });
      const lines = new THREE.LineSegments(lineGeo, lineMat);
      scene.add(lines);
    }

    // Ambient background stars in journey map
    const starsCount = 300;
    const starPos = new Float32Array(starsCount * 3);
    for (let i = 0; i < starsCount * 3; i++) {
      starPos[i] = (Math.random() - 0.5) * 50;
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({ size: 0.1, color: 0x818cf8, transparent: true, opacity: 0.5 });
    const stars = new THREE.Points(starGeo, starMat);
    scene.add(stars);

    // Hover & Click Handling
    let hoveredMesh = null;
    const tooltip = document.getElementById('journey-map-tooltip');

    function onPointerMove(e) {
      const rect = container.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(nodeMeshes);

      if (intersects.length > 0) {
        hoveredMesh = intersects[0].object;
        container.style.cursor = 'pointer';
        const node = hoveredMesh.userData.nodeData;

        if (tooltip) {
          tooltip.style.display = 'block';
          tooltip.style.left = `${e.clientX - rect.left + 15}px`;
          tooltip.style.top = `${e.clientY - rect.top - 20}px`;
          tooltip.innerHTML = `
            <div style="font-family: var(--font-cyber); font-size: 11px; color: var(--neon-cyan);">${node.name}</div>
            <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">
              Missions: ${node.problems} · Status: <span style="text-transform: uppercase; font-weight: 700; color: #fff;">${node.status}</span>
            </div>
          `;
        }
      } else {
        hoveredMesh = null;
        container.style.cursor = 'default';
        if (tooltip) tooltip.style.display = 'none';
      }
    }

    function onPointerClick() {
      if (hoveredMesh && onNodeClick) {
        onNodeClick(hoveredMesh.userData.nodeData);
      }
    }

    container.addEventListener('mousemove', onPointerMove, { passive: true });
    container.addEventListener('click', onPointerClick);

    let animId;
    const clock = new THREE.Clock();

    function animate() {
      animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      // Gentle floating motion
      nodeMeshes.forEach((mesh, i) => {
        mesh.position.y = mesh.userData.nodeData.y + Math.sin(t * 1.5 + i) * 0.15;
      });

      // Subtle scene camera drift
      camera.position.x += (mouse.x * 2 - camera.position.x + 6) * 0.03;
      camera.position.y += (mouse.y * 1.5 - camera.position.y) * 0.03;
      camera.lookAt(6, 0, 0);

      renderer.render(scene, camera);
    }
    animate();

    const sceneData = { camera, renderer, container, scene };
    const onResize = () => handleResize(sceneData);
    window.addEventListener('resize', onResize);

    const sceneRef = {
      cleanup: () => {
        cancelAnimationFrame(animId);
        container.removeEventListener('mousemove', onPointerMove);
        container.removeEventListener('click', onPointerClick);
        window.removeEventListener('resize', onResize);
        renderer.dispose();
        if (renderer.domElement.parentNode) {
          renderer.domElement.parentNode.removeChild(renderer.domElement);
        }
      }
    };

    activeScenes.set(containerId, sceneRef);
    return sceneRef;
  }

  function destroyAll() {
    activeScenes.forEach((ref) => ref.cleanup());
    activeScenes.clear();
  }

  return {
    createLandingScene,
    createDashboardScene,
    createJourneyMapScene,
    destroyAll
  };
})();
