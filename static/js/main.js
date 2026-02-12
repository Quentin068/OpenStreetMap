const socket = io();
const canvas = document.getElementById('mapCanvas');
const ctx = canvas.getContext('2d');

let roads = [], min_x, max_x, min_y, max_y, w, h;
let isSimulating = false;
let aiEnabled = false;

// --- Moteur de Rendu (Zoom/Pan) ---
let scale = 1, originX = 0, originY = 0;
let isDragging = false, startDragX, startDragY;

function resize() {
    w = canvas.width = document.getElementById('map-container').clientWidth;
    h = canvas.height = document.getElementById('map-container').clientHeight;
    if (!isSimulating && roads.length > 0) drawMap([], [], []);
}

window.onresize = resize;

canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoom = Math.exp(e.deltaY < 0 ? 0.1 : -0.1);

    // Zoom vers la souris
    const mx = e.offsetX;
    const my = e.offsetY;

    originX -= (mx - originX) * (zoom - 1);
    originY -= (my - originY) * (zoom - 1);
    scale *= zoom;
    if (!isSimulating) drawMap([], [], []);
});

canvas.addEventListener('mousedown', (e) => {
    if (e.button === 0) {
        isDragging = true;
        startDragX = e.clientX;
        startDragY = e.clientY;
    } else if (e.button === 2) {
        handleRightClick(e);
    }
});

canvas.addEventListener('mousemove', (e) => {
    if (isDragging) {
        originX += e.clientX - startDragX;
        originY += e.clientY - startDragY;
        startDragX = e.clientX;
        startDragY = e.clientY;
        if (!isSimulating) drawMap([], [], []);
    }
});

canvas.addEventListener('mouseup', () => isDragging = false);
canvas.addEventListener('contextmenu', (e) => e.preventDefault());

function handleRightClick(e) {
    if (!isSimulating) return;
    // Coordonnées souris -> Monde
    const rect = canvas.getBoundingClientRect();
    const worldX = (e.clientX - rect.left - originX) / scale;
    const worldY = (e.clientY - rect.top - originY) / scale;

    socket.emit('add_roadwork', {
        x: (worldX / w) * (max_x - min_x) + min_x,
        y: ((h - worldY) / h) * (max_y - min_y) + min_y
    });
    const el = document.getElementById('alert');
    el.style.opacity = 1;
    setTimeout(() => el.style.opacity = 0, 1000);
}

// --- Chart.js ---
Chart.defaults.color = '#aaa';
Chart.defaults.borderColor = 'rgba(255,255,255,0.1)';
const chart = new Chart(document.getElementById('chart'), {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Cycle (s)',
            data: [],
            borderColor: '#ffff00',
            tension: 0.1,
            pointRadius: 0,
            borderWidth: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {x: {display: false}, y: {suggestedMin: 20, suggestedMax: 100, grid: {color: '#333'}}},
        plugins: {legend: {display: false}}
    }
});

function project(x, y) {
    return {px: (x - min_x) / (max_x - min_x) * w, py: h - ((y - min_y) / (max_y - min_y) * h)};
}

socket.on('init_data', (data) => {
    min_x = data.bounds[0];
    max_x = data.bounds[1];
    min_y = data.bounds[2];
    max_y = data.bounds[3];
    roads = data.roads;
    resize();
    // Centrage initial
    scale = 0.95;
    originX = w * 0.025;
    originY = h * 0.025;
    drawMap([], [], []);
});

socket.on('update', (data) => {
    if (isSimulating) {
        drawMap(data.cars, data.lights, data.roadworks);
        updateUI(data.stats);
    }
});

function updateUI(stats) {
    document.getElementById('st-mode').innerText = "En ligne";
    document.getElementById('st-mode').style.color = "#00ff00";
    document.getElementById('st-trips').innerText = stats.trips;

    const congEl = document.getElementById('st-cong');
    congEl.innerText = stats.congestion.toFixed(1) + "%";
    congEl.className = stats.congestion > 25 ? "val warn" : "val ok";

    document.getElementById('st-cycle').innerText = stats.avg_cycle.toFixed(1) + "s";

    if (chart.data.labels.length > 40) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.data.labels.push("");
    chart.data.datasets[0].data.push(stats.avg_cycle);
    chart.update();
}

function drawMap(cars, lights, works) {
    ctx.save();
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, w, h);
    ctx.translate(originX, originY);
    ctx.scale(scale, scale);

    // Routes (Fines lignes blanches)
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 0.8 / scale;
    ctx.beginPath();
    roads.forEach(r => {
        let p1 = project(r[0][0], r[0][1]), p2 = project(r[1][0], r[1][1]);
        ctx.moveTo(p1.px, p1.py);
        ctx.lineTo(p2.px, p2.py);
    });
    ctx.stroke();

    // Travaux (Carré jaune)
    const blink = Math.floor(Date.now() / 400) % 2 === 0;
    ctx.fillStyle = blink ? '#ffff00' : '#aaaa00';
    works.forEach(rw => {
        let p = project(rw[0], rw[1]);
        const s = 10 / scale;
        ctx.fillRect(p.px - s / 2, p.py - s / 2, s, s);
    });

    // Feux (Points colorés)
    lights.forEach(l => {
        let p = project(l.x, l.y);
        const s = 3 / scale;
        ctx.fillStyle = l.color;
        ctx.beginPath();
        ctx.arc(p.px, p.py, s, 0, Math.PI * 2);
        ctx.fill();
    });

    // Voitures (Points blancs brillants)
    ctx.fillStyle = '#ffffff';
    cars.forEach(c => {
        let p = project(c[0], c[1]);
        let r = Math.max(1, 2.5 / scale);
        ctx.beginPath();
        ctx.arc(p.px, p.py, r, 0, Math.PI * 2);
        ctx.fill();
    });

    ctx.restore();
}

function startSim() {
    let nb = document.getElementById('car-slider').value;
    isSimulating = true;
    socket.emit('start_sim', {nb: nb});
}

function stopSim() {
    isSimulating = false;
    document.getElementById('st-mode').innerText = "Arrêt";
    socket.emit('stop_sim');
}

function toggleAI() {
    aiEnabled = !aiEnabled;
    const btn = document.getElementById('btn-ai');
    if (aiEnabled) {
        btn.classList.add('active-ai');
        btn.innerText = "IA ACTIVE";
        socket.emit('toggle_ai', {active: true});
    } else {
        btn.classList.remove('active-ai');
        btn.innerText = "⚡ Smart Grid (IA)";
        socket.emit('toggle_ai', {active: false});
    }
}