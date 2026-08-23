// ===================== Particle background =====================
(function initParticles() {
  const canvas = document.getElementById("particle-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let w, h, particles;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", resize);
  resize();

  const COUNT = Math.min(70, Math.floor((window.innerWidth * window.innerHeight) / 18000));
  particles = Array.from({ length: COUNT }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.25,
    vy: (Math.random() - 0.5) * 0.25,
    r: Math.random() * 1.6 + 0.4,
  }));

  function tick() {
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "rgba(0, 255, 209, 0.55)";
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    // connecting lines for nearby particles
    ctx.strokeStyle = "rgba(0, 255, 209, 0.08)";
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const a = particles[i], b = particles[j];
        const dist = Math.hypot(a.x - b.x, a.y - b.y);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(tick);
  }
  tick();
})();

// ===================== Hero typing effect =====================
(function typingEffect() {
  const el = document.getElementById("typing-target");
  if (!el) return;
  const phrases = ["ChatGPT.", "Perplexity.", "Gemini.", "AI Overviews."];
  let phraseIndex = 0, charIndex = 0, deleting = false;

  function loop() {
    const current = phrases[phraseIndex];
    if (!deleting) {
      charIndex++;
      el.textContent = current.slice(0, charIndex);
      if (charIndex === current.length) {
        deleting = true;
        setTimeout(loop, 1400);
        return;
      }
    } else {
      charIndex--;
      el.textContent = current.slice(0, charIndex);
      if (charIndex === 0) {
        deleting = false;
        phraseIndex = (phraseIndex + 1) % phrases.length;
      }
    }
    setTimeout(loop, deleting ? 40 : 80);
  }
  loop();
})();

// ===================== Cursor glow =====================
(function cursorGlow() {
  const glow = document.getElementById("cursor-glow");
  if (!glow) return;
  window.addEventListener("mousemove", (e) => {
    glow.style.left = e.clientX + "px";
    glow.style.top = e.clientY + "px";
  });
})();

// ===================== Mobile nav toggle =====================
window.Grezz = window.Grezz || {};
(function mobileNav() {
  const menu = document.getElementById("mobile-menu");
  const btn = document.getElementById("mobile-menu-btn");
  if (!menu || !btn) return;
  window.Grezz.toggleMobileMenu = function () {
    menu.classList.toggle("open");
  };
})();

// ===================== Scroll reveal (IntersectionObserver) =====================
(function scrollReveal() {
  const targets = document.querySelectorAll(".reveal-scroll");
  if (!targets.length || !("IntersectionObserver" in window)) {
    targets.forEach((t) => t.classList.add("in-view"));
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );
  targets.forEach((t) => observer.observe(t));
})();

// ===================== Multi-step loading status cycler =====================
(function loadingStatusCycler() {
  const steps = [
    "Fetching the page...",
    "Reading structured data...",
    "Analyzing content clarity...",
    "Calculating GEO Score...",
    "Drafting AI recommendations...",
  ];
  let intervalId = null;

  document.body.addEventListener("htmx:beforeRequest", (evt) => {
    if (!evt.target.matches("#analyze-form")) return;
    const statusEl = document.getElementById("loading-status");
    if (!statusEl) return;
    let i = 0;
    statusEl.textContent = steps[0];
    intervalId = setInterval(() => {
      i = (i + 1) % steps.length;
      statusEl.textContent = steps[i];
    }, 1400);
  });

  document.body.addEventListener("htmx:afterRequest", (evt) => {
    if (!evt.target.matches("#analyze-form")) return;
    if (intervalId) clearInterval(intervalId);
    const statusEl = document.getElementById("loading-status");
    if (statusEl) statusEl.textContent = "";
  });
})();

// ===================== Copy AI summary to clipboard =====================
window.Grezz.copySummary = function (btn) {
  const text = document.getElementById("ai-summary-text")?.innerText || "";
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = "Copied! ✓";
    setTimeout(() => (btn.textContent = original), 1800);
  });
};

// ===================== Sticky dismissible ad bar =====================
(function stickyAdBar() {
  const KEY = "grezz_sticky_ad_dismissed";
  const bar = document.getElementById("sticky-ad-bar");
  if (!bar) return;

  window.Grezz.dismissStickyAd = function () {
    bar.classList.add("hidden");
    sessionStorage.setItem(KEY, "1");
  };

  if (sessionStorage.getItem(KEY)) return;

  // Only appear after the person scrolls a bit, so it never blocks the
  // hero/first impression — non-intrusive by design.
  let shown = false;
  window.addEventListener("scroll", () => {
    if (shown || sessionStorage.getItem(KEY)) return;
    if (window.scrollY > 480) {
      shown = true;
      bar.classList.remove("hidden");
    }
  });
})();


window.Grezz = window.Grezz || {};
(function cookieConsent() {
  const KEY = "grezz_cookie_consent";
  const banner = document.getElementById("cookie-consent");
  if (!banner) return;

  if (!localStorage.getItem(KEY)) {
    setTimeout(() => banner.classList.remove("hidden"), 1200);
  }

  window.Grezz.acceptCookieConsent = function () {
    localStorage.setItem(KEY, "accepted");
    banner.classList.add("hidden");
  };
  window.Grezz.dismissCookieConsent = function () {
    localStorage.setItem(KEY, "dismissed");
    banner.classList.add("hidden");
  };
})();

// ===================== Confetti burst for high GEO scores =====================
function maybeCelebrate(score) {
  if (score < 85) return;
  const colors = ["#00ffd1", "#a855f7", "#ff2e88", "#4fd1ff"];
  const container = document.createElement("div");
  container.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:60;overflow:hidden;";
  document.body.appendChild(container);

  for (let i = 0; i < 60; i++) {
    const piece = document.createElement("span");
    const size = Math.random() * 8 + 4;
    piece.style.cssText = `
      position:absolute; top:-20px; left:${Math.random() * 100}%;
      width:${size}px; height:${size}px;
      background:${colors[Math.floor(Math.random() * colors.length)]};
      border-radius:${Math.random() > 0.5 ? "50%" : "2px"};
      opacity:0.9;
      transform:rotate(${Math.random() * 360}deg);
    `;
    container.appendChild(piece);
    const duration = 2200 + Math.random() * 1400;
    piece.animate(
      [
        { transform: `translateY(0) rotate(0deg)`, opacity: 1 },
        { transform: `translateY(${window.innerHeight + 40}px) rotate(${360 + Math.random() * 360}deg)`, opacity: 0.2 },
      ],
      { duration, easing: "cubic-bezier(0.4,0,0.2,1)", fill: "forwards" }
    );
  }
  setTimeout(() => container.remove(), 3800);
}

// ===================== Score gauge + bar animation =====================
function animateScoreGauge() {
  const ring = document.querySelector(".gauge-ring .progress");
  const numberEl = document.querySelector(".gauge-number");
  if (!ring || !numberEl) return;

  const score = parseInt(ring.dataset.score || "0", 10);
  const circumference = 502; // 2 * PI * r(80)
  const offset = circumference - (score / 100) * circumference;

  let color = "#ff4d6d";
  if (score >= 85) color = "#00ffd1";
  else if (score >= 60) color = "#4fd1ff";
  else if (score >= 35) color = "#ffb020";
  ring.style.color = color;
  ring.setAttribute("stroke", color);

  requestAnimationFrame(() => {
    ring.style.strokeDashoffset = offset;
  });

  // count-up number
  let current = 0;
  const step = Math.max(1, Math.round(score / 40));
  const interval = setInterval(() => {
    current = Math.min(current + step, score);
    numberEl.textContent = current;
    if (current >= score) {
      clearInterval(interval);
      maybeCelebrate(score);
    }
  }, 20);

  // category bars
  document.querySelectorAll(".cat-bar-fill").forEach((bar) => {
    const val = bar.dataset.value || "0";
    requestAnimationFrame(() => {
      bar.style.width = val + "%";
    });
  });
}

// Run on normal load and after HTMX swaps in the results partial
document.addEventListener("DOMContentLoaded", animateScoreGauge);
document.body.addEventListener("htmx:afterSwap", (evt) => {
  if (evt.detail.target && evt.detail.target.id === "results-container") {
    animateScoreGauge();
    evt.detail.target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});
