function clickMenu() {
      if (itens.style.display == 'block') {
        itens.style.display = 'none'
      } else {
        itens.style.display = 'block'
      }
    }

    function mudouTamanho() {
      if (window.innerWidth >= 768) {
        itens.style.display = 'block'
      } else {
        itens.style.display = 'none'
      }
    }
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
    let socket = null;

    function connect() {
      socket = new WebSocket("ws://" + window.location.host + "/websocket");

      socket.onopen = () => {
        console.log("Connected to plain WebSocket");
        // Recupera as estatísticas do localStorage, se existirem
        const savedStats = localStorage.getItem("stats");
        if (savedStats) {
          updateStats(JSON.parse(savedStats));
        }
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
        <ul>${data.top_queries.map((q) => `<li>${q}</li>`).join("")}</ul>

        <h3>Barrels ativos</h3>
        <ul>${data.barrels
          .map(
            (b) => `<li>
                ${b.ip} - 
                Palavras indexadas: ${b.size_words} | 
                URLs indexados: ${b.size_urls}
            </li>`
          )
          .join("")}</ul>

        <h3>Tempo médio de resposta (décimas de segundo)</h3>
        <ul>${Object.entries(data.avg_response_times)
          .map(([ip, t]) => `<li>${ip}: ${t.toFixed(4)}</li>`)
          .join("")}</ul>
    `;

      // Salvar as estatísticas no localStorage
      localStorage.setItem("stats", JSON.stringify(data));
    }

    window.addEventListener("load", () => {
      connect(); // Estabelece ligação ao WebSocket para stats
    });