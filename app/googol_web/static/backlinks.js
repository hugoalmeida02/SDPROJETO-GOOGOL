async function loadBacklinks() {
  const params = new URLSearchParams(window.location.search);
  const url = params.get("url");
  if (!url) {
    document.getElementById("results-container").innerHTML =
      "Nenhuma URL fornecida.";
    return;
  }

  try {
    const res = await fetch(`/backlinks?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    displayResults(data);
  } catch (err) {
    console.error(err);
    document.getElementById("results-container").innerHTML =
      "Erro ao obter backlinks.";
  }
}

function displayResults(data) {
  const container = document.getElementById("results-container");
  container.innerHTML = "";

  if (data.length === 0) {
    container.innerHTML = "<p>Nenhum backlink encontrado.</p>";
    return;
  }

  data.forEach((item) => {
    const div = document.createElement("div");
    div.className = "result-item";
    div.innerHTML = `
      <h3><a href="${item.url}" target="_blank">${item.title}</a></h3>
      <p>${item.snippet || item.url}</p>
    `;
    container.appendChild(div);
  });
}

window.onload = loadBacklinks;
