document
  .getElementById("search-form")
  .addEventListener("submit", function (event) {
    event.preventDefault(); // evita recarregamento
    const query = document.getElementById("search-input").value.trim();
    const type = document.getElementById("search-type").value;

    const encoded = encodeURIComponent(query);
    console.log("Tipo selecionado:", type);
    if (type === "word") {
      window.location.href = `/search?words=${encoded}`;
    } else if (type === "backlinks") {
      window.location.href = `/search-backlinks?url=${encoded}`;
    } else if (type === "addurls") {
      fetch("/add-url", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `url=${encoded}`,
      })
        .then((res) => res.json())
        .then((data) => {
          alert(data.message || data.error);
        })
        .catch((err) => {
          console.error("Erro ao adicionar URL:", err);
        });
    }
  });

// Abrir e fechar modal
document.getElementById("open-stats-btn").addEventListener("click", () => {
  document.getElementById("stats-modal").style.display = "block";
});

document.getElementById("close-stats-btn").addEventListener("click", () => {
  document.getElementById("stats-modal").style.display = "none";
});

// Fechar ao clicar fora do conteúdo do modal
window.addEventListener("click", function (event) {
  const modal = document.getElementById("stats-modal");
  if (event.target === modal) {
    modal.style.display = "none";
  }
});
