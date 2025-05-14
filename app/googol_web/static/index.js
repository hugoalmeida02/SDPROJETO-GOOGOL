function clickMenu() {
  if (itens.style.display == "block") {
    itens.style.display = "none";
  } else {
    itens.style.display = "block";
  }
}

function mudouTamanho() {
  if (window.innerWidth >= 768) {
    itens.style.display = "block";
  } else {
    itens.style.display = "none";
  }
}

// Submissão do formulário de pesquisa
document
  .getElementById("search-form")
  .addEventListener("submit", function (event) {
    event.preventDefault();
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

// Menu mobile
document.getElementById("burger").addEventListener("click", clickMenu);

// Abrir e fechar modal stats
document.getElementById("open-stats-btn").addEventListener("click", () => {
  document.getElementById("stats-modal").style.display = "block";
});

document.getElementById("close-stats-btn").addEventListener("click", () => {
  document.getElementById("stats-modal").style.display = "none";
});

// Abrir e fechar modal sobre
document.getElementById("open-sobre-btn").addEventListener("click", () => {
  document.getElementById("sobre-modal").style.display = "block";
});

document.getElementById("close-sobre-btn").addEventListener("click", () => {
  document.getElementById("sobre-modal").style.display = "none";
});

// Abrir e fechar modal ajuda
document.getElementById("open-ajuda-btn").addEventListener("click", () => {
  document.getElementById("ajuda-modal").style.display = "block";
});

document.getElementById("close-ajuda-btn").addEventListener("click", () => {
  document.getElementById("ajuda-modal").style.display = "none";
});

// Abrir e fechar modal contacto
document.getElementById("open-contacto-btn").addEventListener("click", () => {
  document.getElementById("contacto-modal").style.display = "block";
});

document.getElementById("close-contacto-btn").addEventListener("click", () => {
  document.getElementById("contacto-modal").style.display = "none";
});

// Fechar ao clicar fora do conteúdo do modal
window.addEventListener("click", function (event) {
  const modal = document.getElementById("stats-modal");
  if (event.target === modal) {
    modal.style.display = "none";
  }
});
