const POSITIONS = ["A1","A2","A3","B1","B2","B3","C1","C2","C3"];

const board     = document.getElementById("board");
const statusEl  = document.getElementById("status");
const historyEl = document.getElementById("history");
const btnStart  = document.getElementById("btn-start");
const btnReset  = document.getElementById("btn-reset");
const debugLog  = document.getElementById("debug-log");
const btnClear  = document.getElementById("btn-clear-log");

let gameActive    = false;
let waiting       = false;
let currentPlayer = "O";

// ── Debug logger ────────────────────────────────────────────────

function logRequest(method, path, body, status, responseBody, elapsed) {
    const entry = document.createElement("div");
    entry.className = "debug-entry";

    const statusClass = status >= 200 && status < 300 ? "ok" : "err";
    const timestamp = new Date().toLocaleTimeString("en-US", { hour12: false });
    const bodyStr = body ? JSON.stringify(body) : "";
    const respStr = JSON.stringify(responseBody, null, 2);

    let html = '<span class="debug-time">' + timestamp + "</span> ";
    html += '<span class="debug-method ' + method + '">' + method + "</span> ";
    html += '<span class="debug-url">/api/' + path + "</span> ";
    if (bodyStr) html += '<span class="debug-body">\u2192 ' + bodyStr + "</span> ";
    html += '<span class="debug-status ' + statusClass + '">' + status + "</span> ";
    html += '<span class="debug-time">' + elapsed + "ms</span>";
    html += '<div class="debug-body">\u2190 ' + respStr + "</div>";

    entry.innerHTML = html;
    debugLog.prepend(entry);
}

btnClear.addEventListener("click", () => { debugLog.innerHTML = ""; });

// ── Build board cells ───────────────────────────────────────────

POSITIONS.forEach(pos => {
    const cell = document.createElement("div");
    cell.className = "cell disabled";
    cell.dataset.pos = pos;
    cell.addEventListener("click", () => onCellClick(pos));
    board.appendChild(cell);
});

// ── Mode <-> difficulty enable/disable ──────────────────────────

const modeSelect = document.getElementById("mode");
const difficultySelect = document.getElementById("difficulty");
const symbolSelect = document.getElementById("symbol");

function syncModeControls() {
    const twoPlayer = parseInt(modeSelect.value, 10) === 2;
    difficultySelect.disabled = twoPlayer;
    symbolSelect.disabled     = twoPlayer;
}
modeSelect.addEventListener("change", syncModeControls);
syncModeControls();

// ── API helpers ─────────────────────────────────────────────────

async function api(method, path, body) {
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const t0 = performance.now();
    const r = await fetch("/api/" + path, opts);
    const elapsed = Math.round(performance.now() - t0);
    const data = await r.json().catch(() => ({ detail: r.statusText }));
    logRequest(method, path, body || null, r.status, data, elapsed);
    if (!r.ok) {
        throw new Error(data.detail || JSON.stringify(data));
    }
    return data;
}

// ── Render game state ───────────────────────────────────────────

function render(state) {
    const cells = board.querySelectorAll(".cell");
    cells.forEach((cell, i) => {
        const row = Math.floor(i / 3);
        const col = i % 3;
        const val = state.board[row][col];
        cell.innerHTML = val ? '<span class="' + val + '">' + val + "</span>" : "";
        cell.className = "cell";
        if (val) cell.classList.add("occupied");
        if (state.game_status !== "InProgress") cell.classList.add("disabled");
    });

    gameActive = state.game_status === "InProgress";
    currentPlayer = state.current_player;
    btnReset.disabled = state.game_status === "Idle";

    if (state.game_status === "Idle") {
        statusEl.textContent = "Click Start Game to begin";
    } else if (state.game_status === "InProgress") {
        if (state.game_mode === 1) {
            const me = state.human_symbol;
            statusEl.textContent = state.current_player === me
                ? "Your move (" + me + ")"
                : "Opponent thinking...";
        } else {
            statusEl.textContent = state.current_player + "'s turn";
        }
    } else if (state.game_status === "Draw") {
        statusEl.textContent = "It's a draw!";
    } else {
        // "XWins" or "OWins"
        const winner = state.game_status.replace("Wins", "");
        statusEl.textContent = winner + " wins!";
    }

    historyEl.innerHTML = state.move_history
        .map(m => "<div>" + m + "</div>").join("");
    historyEl.scrollTop = historyEl.scrollHeight;
}

// ── Optimistic UI ───────────────────────────────────────────────

function placeOptimistic(pos, symbol) {
    const cell = board.querySelector('[data-pos="' + pos + '"]');
    if (cell) {
        cell.innerHTML = '<span class="' + symbol + ' pending">' + symbol + "</span>";
        cell.classList.add("occupied");
    }
}

// ── Event handlers ──────────────────────────────────────────────

btnStart.addEventListener("click", async () => {
    const mode       = parseInt(document.getElementById("mode").value, 10);
    const difficulty = document.getElementById("difficulty").value;
    const symbol     = document.getElementById("symbol").value;
    waiting = true;
    statusEl.textContent = "Starting game...";
    try {
        const body = mode === 1
            ? { mode, human_symbol: symbol, ai_difficulty: difficulty }
            : { mode };
        const data = await api("POST", "start", body);
        render(data.state);
        await maybePlayAi(data.state);
    } catch (e) {
        statusEl.textContent = e.message;
    }
    waiting = false;
});

btnReset.addEventListener("click", async () => {
    waiting = true;
    statusEl.textContent = "Resetting — returning pieces...";
    try {
        const data = await api("POST", "reset");
        render(data.state);
    } catch (e) {
        statusEl.textContent = e.message;
    }
    waiting = false;
});

async function onCellClick(pos) {
    if (!gameActive || waiting) return;
    const cell = board.querySelector('[data-pos="' + pos + '"]');
    if (cell.classList.contains("occupied")) return;

    waiting = true;
    placeOptimistic(pos, currentPlayer);
    statusEl.textContent = "CNC placing " + currentPlayer + " at " + pos + "...";
    try {
        const data = await api("POST", "move", { position: pos });
        render(data.state);
        await maybePlayAi(data.state);
    } catch (e) {
        statusEl.textContent = e.message;
        // Revert optimistic update on error
        try {
            const state = await api("GET", "state");
            render(state);
        } catch (_) {}
    }
    waiting = false;
}

async function maybePlayAi(state) {
    if (!state || !state.ai_pending_cell) return;
    const cell = state.ai_pending_cell;
    const sym  = state.ai_symbol;
    placeOptimistic(cell, sym);
    statusEl.textContent = "CNC placing " + sym + " at " + cell + "...";
    try {
        const data = await api("POST", "ai-move");
        render(data.state);
        // Just in case the API returns another pending move (shouldn't happen)
        if (data.state.ai_pending_cell) await maybePlayAi(data.state);
    } catch (e) {
        statusEl.textContent = "Move failed: " + e.message;
        try {
            const s = await api("GET", "state");
            render(s);
        } catch (_) {}
    }
}

// ── Initial load ────────────────────────────────────────────────

api("GET", "state").then(render).catch(() => {});

api("GET", "info").then(info => {
    const banner = document.getElementById("info-banner");
    if (!info) return;
    const place = info.place_delay_s ?? 0;
    const grip  = info.grip_delay_s ?? 0;
    const virt  = info.virtual ? " \u00b7 VIRTUAL MODE (no hardware)" : "";
    banner.textContent =
        `Each move waits ~${place}s after release and ~${grip}s after pickup ` +
        `for the vacuum to settle.${virt}`;
    banner.hidden = false;
}).catch(() => {});
