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
                    body: JSON.stringify({ search_terms: searchTerms })
                });

                // Verifica se a resposta foi bem-sucedida
                if (!response.ok) {
                    analysisContent.textContent = "Erro ao gerar a análise"
                    throw new Error("Erro ao gerar a análise");
                }

                const data = await response.json();
                const analysisText = data.analysis;
                
                analysisContent.textContent = analysisText;
            } catch (error) {
                console.error("Erro ao gerar a análise:", error);
            }
        });