document
  .getElementById("index-top-stories-btn")
  .addEventListener("click", async () => {
    const msg = document.getElementById("tool-msg");
    const container = document.getElementById("indexed-urls-container");
    const list = document.getElementById("indexed-url-list");
    msg.textContent = "A carregar os top stories do Hacker News...";

    try {
      const query = new URLSearchParams(window.location.search);
      const searchWords = query.get("words") || "";
      const res = await fetch(
        `/index_hackernews_urls?words=${encodeURIComponent(searchWords)}`,
        {
          method: "POST",
        }
      );

      const data = await res.json();
      msg.textContent = `Foram indexadas ${data.count} URLs das top stories.`;

      // Mostrar os resultados
      list.innerHTML = "";
      data.urls.forEach((url) => {
        const li = document.createElement("li");
        li.innerHTML = `<a href="${url}" target="_blank">${url}</a>`;
        list.appendChild(li);
      });

      container.style.display = "block";
    } catch (err) {
      console.error(err);
      msg.textContent = "Erro ao indexar as top stories.";
    }
  });

document
  .getElementById("generate-analysis-btn")
  .addEventListener("click", async function () {
    const searchTerms = "{{ words }}"; // Passa os termos do Jinja2 para o JavaScript

    try {
      // Adicionar a análise no início da página sem modificar o resto do conteúdo
      const analysisContainer = document.getElementById("analysis-container");
      const analysisContent = document.getElementById("analysis-content");

      // Mostrar a análise na página
      analysisContainer.style.display = "block";

      const response = await fetch("/generate_analysis", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ search_terms: searchTerms }),
      });

      // Verifica se a resposta foi bem-sucedida
      if (!response.ok) {
        analysisContent.textContent = "Erro ao gerar a análise";
        throw new Error("Erro ao gerar a análise");
      }

      const data = await response.json();
      const analysisText = data.analysis;

      analysisContent.textContent = analysisText;
    } catch (error) {
      console.error("Erro ao gerar a análise:", error);
    }
  });
