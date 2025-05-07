// // Submeter novo URL para indexação
// const formUrl = document.getElementById("form-url");
// formUrl.addEventListener("submit", async (e) => {
//     e.preventDefault();
//     const url = document.getElementById("url-input").value;

//     const response = await fetch("/add-url", {
//         method: "POST",
//         headers: {
//             "Content-Type": "application/json"
//         },
//         body: JSON.stringify({ url: url })
//     });

//     if (response.ok) {
//         alert("URL adicionado com sucesso!");
//         document.getElementById("url-input").value = "";
//     } else {
//         alert("Erro ao adicionar URL.");
//     }
// });

// // Submeter pesquisa de termos
// const formSearch = document.getElementById("form-search");
// formSearch.addEventListener("submit", async (e) => {
//     e.preventDefault();
//     const words = document.getElementById("search-input").value;

//     const response = await fetch(`/search?words=${encodeURIComponent(words)}`);
//     if (response.ok) {
//         const html = await response.text();
//         document.body.innerHTML = html;
//     } else {
//         alert("Erro ao realizar pesquisa.");
//     }
// });

// Submeter consulta de backlinks
const formBacklinks = document.getElementById("form-backlink");
formBacklinks.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = document.getElementById("backlink-input").value;

    const response = await fetch(`/search_backlinks?url=${encodeURIComponent(url)}`);
    if (response.ok) {
        const html = await response.text();
        document.body.innerHTML = html;
    } else {
        alert("Erro ao realizar consulta.");
    }
});



