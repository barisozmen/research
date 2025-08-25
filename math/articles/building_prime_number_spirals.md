**Building Prime Number Spirals at 60 FPS: A Practical Guide to Interactive Math**

I built an interactive prime-spiral explorer that renders hundreds of thousands of integers and lets you pan, zoom, and hover to inspect primes. This note walks through the engineering: data structures, coordinate transforms, rendering, and the small decisions that make it snappy.

The implementation is a single self-contained HTML file using Canvas and jQuery. No build step, no framework. Open it in a browser and it works.

**What it is**
- **Three layouts for 1…N**:
  - Ulam spiral (grid spiral; primes form diagonal ridges)
  - Sacks spiral (polar layout; $r=\sqrt{n}$, $\theta=2\pi\sqrt{n}$)
  - Archimedes spiral ($r=a\theta$; choose $\theta\propto\sqrt{n}$ for spacing)
- **Sieve** up to N (default 50k; usable into the hundreds of thousands)
- **Pan, zoom to cursor, hover tooltips** for primes
- **Spatial hashing** for O(1)-ish hover lookup
- **Live stats** for range, count, density, zoom
- **Optional** spiral-line overlay (Ulam)

**Architecture**
- A single class, `PrimeSpiralVisualizer`:
  - Holds UI/render state (`offsetX`, `offsetY`, `zoom`, `spiralType`, caches)
  - Sieve for primality
  - Spiral coordinate generators
  - Projection and culling to visible set
  - Spatial grid for hit-testing
  - Canvas draw routine
  - Event wiring for pan/zoom/sliders/modal
- No animation loop; re-renders on state changes (pan/zoom/hover/slider)

**Primes: Sieve of Eratosthenes**
- Time: $O(n\log\log n)$
- Space: $O(n)$
- In practice, a few ms to 500k in modern browsers

```javascript
sieveOfEratosthenes(limit) {
  const sieve = new Array(limit + 1).fill(true);
  sieve[0] = sieve[1] = false;

  for (let i = 2; i * i <= limit; i++) {
    if (sieve[i]) {
      for (let j = i * i; j <= limit; j += i) {
        sieve[j] = false;
      }
    }
  }

  const primeSet = new Set();
  for (let i = 2; i <= limit; i++) {
    if (sieve[i]) primeSet.add(i);
  }
  return primeSet;
}
```

- **Tradeoffs**:
  - `Set` keeps checks readable (`primes.has(n)`)
  - For multi-million ranges, prefer a `Uint8Array`/bitset plus a fast `isPrime(n)`

**Coordinates: three spirals**
- **Ulam**: grid walk with corner turns; each integer maps to a unique lattice point
```javascript
generateUlamSpiral(maxNum) {
  const points = [];
  let x = 0, y = 0;
  let dx = 0, dy = -1;
  let num = 1;

  for (let i = 0; i < maxNum; i++) {
    points.push({ x, y, n: num });

    if (x === y || (x < 0 && x === -y) || (x > 0 && x === 1 - y)) {
      [dx, dy] = [-dy, dx];
    }

    x += dx;
    y += dy;
    num++;
  }
  return points;
}
```

- **Sacks**: $r=\sqrt{n}$, $\theta=2\pi\sqrt{n}$ in polar, then to Cartesian
```javascript
generateSacksSpiral(maxNum) {
  const points = [];
  for (let n = 1; n <= maxNum; n++) {
    const r = Math.sqrt(n);
    const theta = 2 * Math.PI * r;
    const x = r * Math.cos(theta);
    const y = r * Math.sin(theta);
    points.push({ x, y, n });
  }
  return points;
}
```

- **Archimedes**: $r=a\theta$ with $\theta\propto\sqrt{n}$ for visual balance
```javascript
generateArchimedesSpiral(maxNum) {
  const points = [];
  const a = 2;
  for (let n = 1; n <= maxNum; n++) {
    const theta = Math.sqrt(n) * 0.5;
    const r = a * theta;
    const x = r * Math.cos(theta);
    const y = r * Math.sin(theta);
    points.push({ x, y, n });
  }
  return points;
}
```

- **What they reveal**:
  - Ulam: diagonal prime-rich lines (quadratic polynomials)
  - Sacks: smooth quadratic curves of high prime yield
  - Archimedes: graceful bands, visually balanced spacing

**Projection, culling, and spatial hashing**
- Transform world → screen, keep only on-screen points, index into a coarse grid
```javascript
buildSpatialGrid() {
  this.spatialGrid.clear();
  const gridSize = 20; // pixels
  const { width, height } = this.resizeCanvas();

  this.visiblePoints = [];
  const centerX = width / 2 + this.offsetX;
  const centerY = height / 2 + this.offsetY;
  const scale = this.spiralType === 'ulam' ? 8 : 4;

  for (const point of this.spiralPoints) {
    const screenX = centerX + point.x * scale * this.zoom;
    const screenY = centerY + point.y * scale * this.zoom;

    if (screenX >= -50 && screenX <= width + 50 && screenY >= -50 && screenY <= height + 50) {
      const gridX = Math.floor(screenX / gridSize);
      const gridY = Math.floor(screenY / gridSize);
      const gridKey = `${gridX},${gridY}`;

      const pointData = { ...point, screenX, screenY };
      this.visiblePoints.push(pointData);

      if (!this.spatialGrid.has(gridKey)) {
        this.spatialGrid.set(gridKey, []);
      }
      this.spatialGrid.get(gridKey).push(pointData);
    }
  }
}
```

- **Hover**: probe the 3×3 neighborhood around the mouse cell for O(1)-ish hit-testing
```javascript
findPointAt(mouseX, mouseY) {
  const gridSize = 20;
  const gridX = Math.floor(mouseX / gridSize);
  const gridY = Math.floor(mouseY / gridSize);

  for (let dx = -1; dx <= 1; dx++) {
    for (let dy = -1; dy <= 1; dy++) {
      const gridKey = `${gridX + dx},${gridY + dy}`;
      const points = this.spatialGrid.get(gridKey);

      if (points) {
        for (const point of points) {
          const distance = Math.hypot(mouseX - point.screenX, mouseY - point.screenY);
          const dotSize = parseFloat(this.$dotSizeSlider.val());
          const hitRadius = Math.max(8, dotSize * this.zoom + 4);
          if (distance <= hitRadius) return point;
        }
      }
    }
  }
  return null;
}
```

**Rendering pipeline**
- Retina-aware canvas scaling via `devicePixelRatio`
- Subtle radial background for depth
- Faint non-primes, bright colorized primes
- Hover glow and size emphasis, optional Ulam spiral line
```javascript
const dotSize = parseFloat(this.$dotSizeSlider.val());

// Faint non-primes
this.ctx.fillStyle = 'rgba(150, 164, 199, 0.08)';
for (const point of this.visiblePoints) {
  if (!this.primes.has(point.n)) {
    this.ctx.beginPath();
    this.ctx.arc(point.screenX, point.screenY, dotSize * 0.4 * this.zoom, 0, Math.PI * 2);
    this.ctx.fill();
  }
}

// Colorized primes
for (const point of this.visiblePoints) {
  if (this.primes.has(point.n)) {
    const logN = Math.log(point.n);
    const hue = (logN * 47 + point.n * 0.1) % 360;
    const intensity = Math.min(1, logN / 10);
    const lightness = 60 + intensity * 25;
    const saturation = 70 + intensity * 20;

    const isHovered = this.hoveredPoint && this.hoveredPoint.n === point.n;
    const alpha = isHovered ? 1 : 0.9;
    const sizeMultiplier = isHovered ? 1.5 : 1;

    this.ctx.fillStyle = `hsla(${hue}, ${saturation}%, ${lightness}%, ${alpha})`;

    if (isHovered) {
      this.ctx.shadowColor = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
      this.ctx.shadowBlur = 15;
    }

    this.ctx.beginPath();
    this.ctx.arc(point.screenX, point.screenY, dotSize * this.zoom * sizeMultiplier, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.shadowBlur = 0;
  }
}
```

**Interactivity: pan and zoom-to-cursor**
- Panning updates offsets and rebuilds the grid
- Zoom anchored at the cursor to prevent drift
```javascript
this.$canvas.on('wheel', (e) => {
  e.preventDefault();

  const rect = this.canvas.getBoundingClientRect();
  const mouseX = e.originalEvent.clientX - rect.left;
  const mouseY = e.originalEvent.clientY - rect.top;

  const zoomFactor = e.originalEvent.deltaY > 0 ? 0.9 : 1.1;
  const newZoom = this.zoom * zoomFactor;

  if (newZoom >= 0.1 && newZoom <= 50) {
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    this.offsetX += (mouseX - centerX) * (1 - zoomFactor);
    this.offsetY += (mouseY - centerY) * (1 - zoomFactor);

    this.zoom = newZoom;
    this.buildSpatialGrid();
    this.updateStats();
    this.draw();
  }
});
```

**Performance notes**
- Sieve to 500k: a few ms in Chrome on recent hardware
- Rendering cost ≈ number of visible points; culling reduces by 10–100×
- Hover cost ≈ number of points in a few small grid cells
- Rebuilding the grid each pan/zoom is simpler and fast enough
- No `requestAnimationFrame`; redraw only on interaction

**Scaling further**
- Use typed arrays/bitsets for primality; avoid `Set`
- Progressive rendering in slices across frames
- Sieve in a Web Worker to keep UI responsive
- WebGL/WebGPU: instanced sprites and fragment-shader coloring for millions of points at 60 FPS

**Polish**
- Minimal UI: two sliders (range, dot size), four buttons (spiral type selection, regenerate, reset view, line toggle), one info modal
- Tooltip only for primes (less noise)
- Center dot on Ulam as a visual anchor
- Lightweight performance HUD encourages exploration

**Try it**
- Open `math/prime_spiral_demo.html`
- Change the range, switch spirals, hover along diagonal ridges, zoom deeply

**Teaching hooks**
- Why the sieve is fast ($O(n\log\log n)$)
- Why Ulam diagonals align with quadratics
- How spatial hashing converts linear scans into constant-time probes

**Closing thoughts**
- Precompute the right structure (sieve)
- Choose coordinates that reveal structure (three spirals)
- Cull aggressively and index spatially
- Keep interaction math simple and anchored (zoom-to-cursor)
