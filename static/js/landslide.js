let soil1Chart, soil2Chart, tiltChart, vibChart;

function createLine(ctx, label) {
    return new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [{ label, data: [] }] }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    soil1Chart = createLine(document.getElementById("soil1"), "Soil 1");
    soil2Chart = createLine(document.getElementById("soil2"), "Soil 2");
    tiltChart = createLine(document.getElementById("tiltGraph"), "Tilt");
    vibChart = createLine(document.getElementById("vibration"), "Vibration");

    updateLS();
    setInterval(updateLS, 1500);
});

async function updateLS() {
    const resp = await fetch("/api/landslide");
    const d = await resp.json();
    if (d.error) return;

    const t = d.labels.slice(-1)[0];

    pushAndCap(soil1Chart.data.labels, t);
    pushAndCap(soil1Chart.data.datasets[0].data, d.soil1.slice(-1)[0]);
    soil1Chart.update();

    pushAndCap(soil2Chart.data.labels, t);
    pushAndCap(soil2Chart.data.datasets[0].data, d.soil2.slice(-1)[0]);
    soil2Chart.update();

    pushAndCap(tiltChart.data.labels, t);
    pushAndCap(tiltChart.data.datasets[0].data, d.tilt.slice(-1)[0]);
    tiltChart.update();

    pushAndCap(vibChart.data.labels, t);
    pushAndCap(vibChart.data.datasets[0].data, d.vibration.slice(-1)[0]);
    vibChart.update();

    setRiskBox(document.getElementById("landslideDanger"), d.landslide_danger);
    document.getElementById("rainStatus").innerText = d.rain.slice(-1)[0] ? "Raining" : "No Rain";
}
