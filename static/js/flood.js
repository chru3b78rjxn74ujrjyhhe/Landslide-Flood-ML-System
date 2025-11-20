let waterChart, rainChart, soilSatChart;

document.addEventListener("DOMContentLoaded", () => {
    waterChart = new Chart(document.getElementById("waterLevel").getContext("2d"), {
        type: 'line', data: { labels: [], datasets: [{ label: 'Water level (cm)', data: [] }] },
        options: { animation: { duration: 500, easing: 'easeInOutQuart' } }
    });
    rainChart = new Chart(document.getElementById("rainIntensity").getContext("2d"), {
        type: 'line', data: { labels: [], datasets: [{ label: 'Rain intensity', data: [] }] },
        options: { animation: { duration: 500 } }
    });
    soilSatChart = new Chart(document.getElementById("soilSat").getContext("2d"), {
        type: 'line', data: { labels: [], datasets: [{ label: 'Soil saturation', data: [] }] },
        options: { animation: { duration: 500 } }
    });

    fetchAndUpdate();
    setInterval(fetchAndUpdate, 1100);
});

async function fetchAndUpdate() {
    const resp = await fetch("/api/flood");
    const d = await resp.json();

    if (waterChart.data.labels.length === 0) {
        waterChart.data.labels = d.labels.slice();
        waterChart.data.datasets[0].data = d.water_level.slice();
        rainChart.data.labels = d.labels.slice();
        rainChart.data.datasets[0].data = d.rain_intensity.slice();
        soilSatChart.data.labels = d.labels.slice();
        soilSatChart.data.datasets[0].data = d.soil_sat.slice();

        waterChart.update(); rainChart.update(); soilSatChart.update();
    } else {
        const t = d.labels[d.labels.length-1];
        pushAndCap(waterChart.data.labels, t);
        pushAndCap(waterChart.data.datasets[0].data, d.water_level[d.water_level.length-1]);
        waterChart.update();

        pushAndCap(rainChart.data.labels, t);
        pushAndCap(rainChart.data.datasets[0].data, d.rain_intensity[d.rain_intensity.length-1]);
        rainChart.update();

        pushAndCap(soilSatChart.data.labels, t);
        pushAndCap(soilSatChart.data.datasets[0].data, d.soil_sat[d.soil_sat.length-1]);
        soilSatChart.update();
    }

    setRiskBox(document.getElementById("floodDanger"), d.flood_danger);
}
