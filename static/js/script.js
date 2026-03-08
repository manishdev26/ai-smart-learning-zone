// SmartLearn - Main JavaScript

// ── Auto-dismiss flash messages ──
document.addEventListener('DOMContentLoaded', function () {
  const flashes = document.querySelectorAll('.flash-alert');
  flashes.forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.5s ease';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 500);
    }, 4000);
  });

  // ── Animate progress bars on load ──
  const bars = document.querySelectorAll('.progress-bar-custom');
  bars.forEach(function (bar) {
    const target = bar.style.width;
    bar.style.width = '0%';
    setTimeout(function () { bar.style.width = target; }, 200);
  });

  // ── Fade-in elements ──
  const fadeEls = document.querySelectorAll('.fade-in');
  fadeEls.forEach(function (el, i) {
    el.style.opacity = '0';
    el.style.transform = 'translateY(16px)';
    setTimeout(function () {
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, i * 80);
  });

  // ── Quiz: highlight selected option ──
  const radios = document.querySelectorAll('.option-label input[type=radio]');
  radios.forEach(function (radio) {
    radio.addEventListener('change', function () {
      const name = radio.getAttribute('name');
      document.querySelectorAll(`input[name="${name}"]`).forEach(function (r) {
        r.closest('.option-label').style.background = '';
        r.closest('.option-label').style.borderColor = 'transparent';
      });
      radio.closest('.option-label').style.background = 'rgba(108,99,255,0.15)';
      radio.closest('.option-label').style.borderColor = 'var(--primary)';
    });
  });

  // ── Sidebar mobile toggle (hamburger) ──
  const sidebar = document.getElementById('sidebar');
  const overlay = document.createElement('div');
  overlay.id = 'sidebarOverlay';
  overlay.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:99;';
  document.body.appendChild(overlay);

  overlay.addEventListener('click', function () {
    if (sidebar) sidebar.classList.remove('open');
    overlay.style.display = 'none';
  });

  // Patch sidebar toggle buttons
  const toggleBtns = document.querySelectorAll('[onclick*="sidebar"]');
  toggleBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (sidebar && sidebar.classList.contains('open')) {
        overlay.style.display = 'none';
      } else {
        overlay.style.display = 'block';
      }
    });
  });

  // ── Stat counter animation ──
  document.querySelectorAll('.stat-num').forEach(function (el) {
    const text = el.textContent.trim();
    const num = parseInt(text);
    if (!isNaN(num) && num > 0 && num < 10000) {
      let current = 0;
      const step = Math.ceil(num / 20);
      const interval = setInterval(function () {
        current += step;
        if (current >= num) {
          current = num;
          clearInterval(interval);
        }
        el.textContent = current + (text.includes('%') ? '%' : '');
      }, 50);
    }
  });

  // ── Course card ripple effect ──
  document.querySelectorAll('.course-card, .card-custom').forEach(function (card) {
    card.addEventListener('mouseenter', function () {
      card.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease';
    });
  });
});
