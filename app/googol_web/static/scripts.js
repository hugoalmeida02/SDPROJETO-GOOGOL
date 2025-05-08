// Submeter novo URL para indexação
const formUrl = document.getElementById("form-url");
formUrl.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = document.getElementById("url-input").value;

    const response = await fetch("/add-url", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ url: url })
    });

    if (response.ok) {
        alert("URL adicionado com sucesso!");
        document.getElementById("url-input").value = "";
    } else {
        alert("Erro ao adicionar URL.");
    }
});

// Submeter pesquisa de termos
const formSearch = document.getElementById("form-search");
formSearch.addEventListener("submit", async (e) => {
    e.preventDefault();
    const words = document.getElementById("search-input").value;

    window.location.href = `/search?words=${encodeURIComponent(words)}`;
});

// Submeter consulta de backlinks
const formBacklinks = document.getElementById("form-backlink");
formBacklinks.addEventListener("submit", async (e) => {
e.preventDefault();
const url = document.getElementById("backlink-input").value;

window.location.href = `/search-backlinks?url=${encodeURIComponent(url)}`;
});
