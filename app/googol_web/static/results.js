// document
//   .getElementById("index-top-stories-btn")
//   .addEventListener("click", async () => {
//     const msg = document.getElementById("tool-msg");
//     msg.textContent = "A carregar os top stories do Hacker News...";

//     try {
//       const topRes = await fetch(
//         "https://hacker-news.firebaseio.com/v0/topstories.json"
//       );
//       const topIds = await topRes.json();
//       const top30 = topIds.slice(0, 30);

//       let count = 0;
//       for (const id of top30) {
//         const res = await fetch(
//           `https://hacker-news.firebaseio.com/v0/item/${id}.json`
//         );
//         const story = await res.json();
//         if (story && story.url) {
//           await fetch(`/index_url?url=${encodeURIComponent(story.url)}`, {
//             method: "POST",
//           });
//           count++;
//         }
//       }

//       msg.textContent = `Foram indexadas ${count} stories com sucesso.`;
//     } catch (err) {
//       console.error(err);
//       msg.textContent = "Erro ao indexar as top stories.";
//     }
//   });

document.getElementById("generate-analysis-btn").addEventListener("click", async function() {
      const searchTerms = "{{ words }}"; // Passar os termos de pesquisa já existentes para o backend
      try {
        const response = await axios.post("/generate_analysis", { search_terms: searchTerms });
        const analysisText = response.data.analysis;
        
        // Mostrar a análise na página
        document.getElementById("analysis-content").textContent = analysisText;
        document.getElementById("analysis-container").style.display = "block";
      } catch (error) {
        console.error("Erro ao gerar a análise:", error);
      }
    });
