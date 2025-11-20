// combined.js
function createMiniChart(ctx, color) {
    return new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: '', data: [] }] },
        options: {
            animation: { duration: 500, easing: 'easeInOutQuart' },
            plugins: { legend: { display: false } },
            scales: { x: { display: false }, y: { display: false } }
        }
    });
}

let miniLSChart, miniFLChart, miniCombinedChart;

document.addEventListener("DOMContentLoaded", () => {
    miniLSChart = createMiniChart(document.getElementById("miniLS").getContext("2d"));
    miniFLChart = createMiniChart(document.getElementById("miniFL").getContext("2d"));
    miniCombinedChart = createMiniChart(document.getElementById("miniCombined").getContext("2d"));

    updateCombined();
    setInterval(updateCombined, 1500);
});

async function updateCombined() {
    const resp = await fetch("/api/combined");
    const dC = await resp.json();

    if (dC.error) return;

    setRiskBox(document.getElementById("landslideRisk"), dC.landslide);
    setRiskBox(document.getElementById("floodRisk"), dC.flood);
    setRiskBox(document.getElementById("combinedRisk"), dC.combined);

    pushAndCap(miniLSChart.data.labels, dC.timestamp);
    pushAndCap(miniLSChart.data.datasets[0].data, dC.landslide);
    miniLSChart.update();

    pushAndCap(miniFLChart.data.labels, dC.timestamp);
    pushAndCap(miniFLChart.data.datasets[0].data, dC.flood);
    miniFLChart.update();

    pushAndCap(miniCombinedChart.data.labels, dC.timestamp);
    pushAndCap(miniCombinedChart.data.datasets[0].data, dC.combined);
    miniCombinedChart.update();
}
