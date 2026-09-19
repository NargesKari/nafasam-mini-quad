// AUTO-GENERATED — do not edit directly.
// Source of truth: web/public/index.html
// Regenerate with: python3 scripts/generate_web_header.py

#pragma once

const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<title>Nafasam</title>
<style>
  :root {
    --bg: #0b0f17; --panel: #131a26; --line: #243146; --text: #e6edf7; --dim: #7d8ca5;
    --accent: #3ddcc4; --danger: #ff5c72; --warn: #ffb547;
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; user-select: none; -webkit-user-select: none; }
  html, body {
    margin: 0; height: 100%; height: 100dvh; overflow: hidden; touch-action: none;
    background: radial-gradient(120% 100% at 50% 0%, #17223a 0%, var(--bg) 60%);
    color: var(--text); font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  #app {
    height: 100%; display: flex; flex-direction: column;
    padding: max(10px, env(safe-area-inset-top)) max(14px, env(safe-area-inset-right))
             max(12px, env(safe-area-inset-bottom)) max(14px, env(safe-area-inset-left));
  }

  /* ---- top bar ---- */
  header { display: flex; align-items: center; gap: 12px; }
  .brand { font-weight: 800; letter-spacing: .28em; font-size: 15px; }
  .brand b { color: var(--accent); }
  .chips { display: flex; gap: 8px; margin-left: auto; }
  .chip {
    display: flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 999px;
    background: var(--panel); border: 1px solid var(--line); font-size: 11px; letter-spacing: .08em; color: var(--dim);
  }
  .chip i { width: 8px; height: 8px; border-radius: 50%; background: var(--danger); transition: background .2s, box-shadow .2s; }
  .chip.on { color: var(--text); }
  .chip.on i { background: var(--accent); box-shadow: 0 0 8px var(--accent); }
  #chipArm.on i { background: var(--warn); box-shadow: 0 0 8px var(--warn); }
  #chipBat.on i { background: var(--accent); box-shadow: 0 0 8px var(--accent); }
  #helpBtn {
    width: 34px; height: 34px; border-radius: 50%; border: 1px solid var(--line); background: var(--panel);
    color: var(--accent); font-size: 17px; font-weight: 700; cursor: pointer;
  }

  /* ---- readouts ---- */
  .readouts { display: flex; justify-content: center; gap: 22px; margin-top: 8px; font-variant-numeric: tabular-nums; }
  .ro { text-align: center; }
  .ro small { display: block; font-size: 10px; letter-spacing: .14em; color: var(--dim); }
  .ro span { font-size: 16px; font-weight: 600; }

  /* ---- controls ---- */
  .controls { flex: 1; display: flex; align-items: center; justify-content: space-between; min-height: 0; }
  .pad-wrap { display: flex; flex-direction: column; align-items: center; gap: 8px; }
  .pad-wrap label { font-size: 10px; letter-spacing: .16em; color: var(--dim); }
  .pad {
    --size: min(46vh, 34vw, 260px); --knob: calc(var(--size) * .34);
    position: relative; width: var(--size); height: var(--size); border-radius: 50%;
    background: radial-gradient(circle at 50% 50%, #1a2436 0%, #0f1622 70%);
    border: 1px solid var(--line); box-shadow: inset 0 0 30px rgba(0,0,0,.6), 0 0 0 6px rgba(61,220,196,.04);
    touch-action: none;
  }
  .pad::before, .pad::after { content: ""; position: absolute; background: var(--line); opacity: .7; }
  .pad::before { left: 50%; top: 12%; bottom: 12%; width: 1px; }
  .pad::after { top: 50%; left: 12%; right: 12%; height: 1px; }
  .knob {
    position: absolute; left: 50%; top: 50%; width: var(--knob); height: var(--knob); margin: calc(var(--knob) / -2) 0 0 calc(var(--knob) / -2);
    border-radius: 50%; background: radial-gradient(circle at 35% 30%, #6ff3dd, #1fa793);
    box-shadow: 0 4px 14px rgba(0,0,0,.6), 0 0 18px rgba(61,220,196,.35); will-change: transform;
  }
  .pad.active .knob { box-shadow: 0 4px 14px rgba(0,0,0,.6), 0 0 26px rgba(61,220,196,.7); }

  .center { display: flex; flex-direction: column; align-items: center; gap: 12px; }
  #armBtn {
    width: 96px; height: 96px; border-radius: 50%; border: 2px solid var(--accent); background: transparent;
    color: var(--accent); font-weight: 800; letter-spacing: .12em; font-size: 14px; cursor: pointer;
    transition: all .15s;
  }
  #armBtn.armed { background: var(--danger); border-color: var(--danger); color: #fff; box-shadow: 0 0 26px rgba(255,92,114,.55); }
  #armBtn:active { transform: scale(.95); }
  #toast { min-height: 16px; font-size: 12px; color: var(--warn); text-align: center; max-width: 180px; }

  /* ---- help panel ---- */
  #help {
    position: fixed; inset: 0; background: rgba(5,8,14,.86); backdrop-filter: blur(6px);
    display: none; align-items: center; justify-content: center; padding: 20px; z-index: 50;
  }
  #help.open { display: flex; }
  .card {
    max-width: 560px; max-height: 100%; overflow-y: auto; background: var(--panel); border: 1px solid var(--line);
    border-radius: 16px; padding: 18px 22px; font-size: 14px; line-height: 1.55; touch-action: pan-y;
  }
  .card h2 { margin: 0 0 8px; font-size: 16px; letter-spacing: .12em; color: var(--accent); }
  .card ul { margin: 0; padding-left: 18px; }
  .card li { margin-bottom: 6px; }
  .card b { color: var(--accent); }
  .card button { margin-top: 10px; padding: 8px 18px; border-radius: 8px; border: 1px solid var(--accent); background: none; color: var(--accent); font-weight: 700; }

  /* ---- rotate hint ---- */
  #rotate { display: none; position: fixed; inset: 0; z-index: 100; background: var(--bg); align-items: center; justify-content: center; text-align: center; padding: 24px; color: var(--dim); }
  @media (orientation: portrait) { #rotate { display: flex; } }
</style>
</head>
<body>
<div id="rotate"><div><div style="font-size:44px">&#8635;</div>Rotate your phone to landscape</div></div>

<div id="app">
  <header>
    <div class="brand">NAF<b>A</b>SAM</div>
    <div class="chips">
      <div class="chip" id="chipLink"><i></i>LINK</div>
      <div class="chip" id="chipImu"><i></i>IMU</div>
      <div class="chip" id="chipArm"><i></i>ARMED</div>
      <div class="chip" id="chipBat"><i></i><span id="txtBat">--V</span></div>
    </div>
    <button id="helpBtn" aria-label="Help">?</button>
  </header>

  <div class="readouts">
    <div class="ro"><small>THROTTLE</small><span id="roT">0</span></div>
    <div class="ro"><small>YAW</small><span id="roY">0</span></div>
    <div class="ro"><small>PITCH</small><span id="roP">0</span></div>
    <div class="ro"><small>ROLL</small><span id="roR">0</span></div>
  </div>

  <div class="controls">
    <div class="pad-wrap"><div class="pad" id="padL"><div class="knob"></div></div><label>THROTTLE / YAW</label></div>
    <div class="center">
      <button id="armBtn">ARM</button>
      <div id="toast"></div>
    </div>
    <div class="pad-wrap"><div class="pad" id="padR"><div class="knob"></div></div><label>PITCH / ROLL</label></div>
  </div>
</div>

<div id="help">
  <div class="card">
    <h2>HOW TO FLY</h2>
    <ul>
      <li>Place the drone <b>flat and still</b>, then power it. It calibrates the gyro on boot; wait for the <b>IMU</b> light.</li>
      <li>Connect this phone to the <b>Nafasam</b> WiFi and open <b>192.168.4.1</b>. The <b>LINK</b> light shows the connection.</li>
      <li>Keep <b>throttle at zero</b>, then press <b>ARM</b>. Arming is refused if throttle is up.</li>
      <li><b>Left stick</b>: up/down = throttle, left/right = yaw (turn). Throttle drops to zero when you let go.</li>
      <li><b>Right stick</b>: up/down = pitch (forward/back), left/right = roll (sideways). It self-levels when centred.</li>
      <li>Press <b>DISARM</b> to stop all motors at any time.</li>
      <li>If the link drops for half a second, or the app goes to the background, the drone disarms itself.</li>
    </ul>
    <button id="helpClose">CLOSE</button>
  </div>
</div>

<script>
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var state = { throttle: 0, yaw: 0, pitch: 0, roll: 0 };
  var armWanted = false;

  // ---------- joysticks ----------
  // restY: screen-y where the knob springs back to (+1 = bottom edge, 0 = centre).
  function Stick(el, restY, onChange) {
    var knob = el.querySelector('.knob');
    var pid = null, x = 0, y = restY;
    function draw() {
      var r = (el.clientWidth - knob.clientWidth) / 2;
      knob.style.transform = 'translate(' + (x * r) + 'px,' + (y * r) + 'px)';
    }
    function move(e) {
      var b = el.getBoundingClientRect();
      var r = (b.width - knob.clientWidth) / 2;
      var dx = (e.clientX - (b.left + b.width / 2)) / r;
      var dy = (e.clientY - (b.top + b.height / 2)) / r;
      var m = Math.hypot(dx, dy);
      if (m > 1) { dx /= m; dy /= m; }
      x = dx; y = dy; draw(); onChange(x, y);
    }
    function release() {
      pid = null; x = 0; y = restY; el.classList.remove('active'); draw(); onChange(x, y);
    }
    el.addEventListener('pointerdown', function (e) {
      if (pid !== null) return;
      pid = e.pointerId; el.setPointerCapture(pid); el.classList.add('active'); move(e);
    });
    el.addEventListener('pointermove', function (e) { if (e.pointerId === pid) move(e); });
    el.addEventListener('pointerup', function (e) { if (e.pointerId === pid) release(); });
    el.addEventListener('pointercancel', function (e) { if (e.pointerId === pid) release(); });
    window.addEventListener('resize', draw);
    this.reset = release;
    draw();
  }

  function dz(v) { return Math.abs(v) < 0.05 ? 0 : v; }
  function pct(v) { return Math.round(Math.max(-1, Math.min(1, v)) * 100); }

  var left = new Stick($('padL'), 1, function (x, y) {
    state.throttle = Math.max(0, Math.round((1 - y) / 2 * 100));   // bottom = 0, top = 100
    state.yaw = pct(dz(x));
    show();
  });
  var right = new Stick($('padR'), 0, function (x, y) {
    state.pitch = pct(dz(-y));   // up = forward
    state.roll = pct(dz(x));
    show();
  });

  function show() {
    $('roT').textContent = state.throttle;
    $('roY').textContent = state.yaw;
    $('roP').textContent = state.pitch;
    $('roR').textContent = state.roll;
  }

  // ---------- ARM ----------
  function setArm(v) {
    armWanted = v;
    $('armBtn').classList.toggle('armed', v);
    $('armBtn').textContent = v ? 'DISARM' : 'ARM';
    refused = 0;
  }
  $('armBtn').addEventListener('click', function () { setArm(!armWanted); });

  var toastTimer;
  function toast(msg) {
    $('toast').textContent = msg;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { $('toast').textContent = ''; }, 3500);
  }

  // ---------- help ----------
  $('helpBtn').addEventListener('click', function () { $('help').classList.toggle('open'); });
  $('helpClose').addEventListener('click', function () { $('help').classList.remove('open'); });

  // ---------- link ----------
  var inflight = false, fails = 0, refused = 0;
  function chip(id, on) { $(id).classList.toggle('on', !!on); }

  function tick() {
    if (inflight) return;
    inflight = true;
    var ctl = new AbortController();
    var to = setTimeout(function () { ctl.abort(); }, 400);
    var q = 'throttle=' + state.throttle + '&yaw=' + state.yaw + '&pitch=' + state.pitch +
            '&roll=' + state.roll + '&armed=' + (armWanted ? 1 : 0);
    fetch('/control?' + q, { cache: 'no-store', signal: ctl.signal })
      .then(function (r) { return r.json(); })
      .then(function (s) {
        fails = 0;
        chip('chipLink', true); chip('chipImu', s.imu); chip('chipArm', s.armed);
        if (s.vbat !== undefined && s.vbat > 0) {
          $('txtBat').textContent = s.vbat.toFixed(1) + 'V';
          chip('chipBat', s.vbat >= 3.3);
        }
        if (armWanted && !s.armed) {
          if (++refused >= 4) {
            setArm(false);
            toast(s.imu ? 'Arm refused: lower throttle first' : 'IMU not ready');
          }
        } else {
          refused = 0;
        }
        if (!armWanted) refused = 0;
      })
      .catch(function () {
        if (++fails >= 3) {
          chip('chipLink', false); chip('chipImu', false); chip('chipArm', false); chip('chipBat', false);
          if (armWanted) setArm(false);
        }
      })
      .then(function () { clearTimeout(to); inflight = false; });
  }
  setInterval(tick, 100);

  // Safety: leaving the page disarms and zeroes the sticks.
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { setArm(false); left.reset(); right.reset(); tick(); }
  });

  document.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  show();
})();
</script>
</body>
</html>

)rawliteral";
