let socket = null;

function connect() {
    socket = new WebSocket('ws://' + window.location.host + '/websocket');

    socket.onopen = () => {
        console.log("Connected to plain WebSocket");
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.type === "stats") {
                updateStats(data);
            } else {
                console.log("Mensagem desconhecida:", data);
            }
        } catch (e) {
            console.error("Erro ao processar mensagem:", e);
        }
    };

    socket.onerror = (event) => {
        console.error("WebSocket error", event);
    };

    socket.onclose = () => {
        console.log("Disconnected from WebSocket");
    };
}

function updateStats(data) {
    const statsDiv = document.getElementById("stats");

    statsDiv.innerHTML = `
        <h3>Top 10 pesquisas</h3>
        <ul>${data.top_queries.map(q => `<li>${q}</li>`).join('')}</ul>

        <h3>Barrels ativos</h3>
        <ul>${data.barrels.map(b => `<li>${b.ip} - ${b.size} entradas</li>`).join('')}</ul>

        <h3>Tempo médio de resposta (décimas de segundo)</h3>
        <ul>${Object.entries(data.avg_response_times).map(([ip, t]) => `<li>${ip}: ${t}</li>`).join('')}</ul>
    `;
}

window.addEventListener('load', () => {
    connect(); // Estabelece ligação ao WebSocket para stats
});