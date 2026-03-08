document.addEventListener('DOMContentLoaded', () => {
    const voteForm = document.getElementById('vote-form');
    const votingCard = document.getElementById('voting-card');
    const resultsCard = document.getElementById('results-card');
    const resultsContainer = document.getElementById('results-container');
    const showResultsBtn = document.getElementById('show-results-btn');
    const backToVoteBtn = document.getElementById('back-to-vote-btn');
    const liveIndicator = document.getElementById('live-indicator');

    const showVotedText = () => {
        const text = localStorage.getItem('votedOptionText');
        if (!text) return;

        let info1 = voteForm.querySelector('.info-message');
        if (!info1) {
            info1 = document.createElement('div');
            info1.className = 'info-message';
            info1.style.cssText = 'background: rgba(99, 102, 241, 0.1); color: var(--accent); padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: 600; border: 1px solid rgba(99, 102, 241, 0.2);';
            voteForm.prepend(info1);
        }
        info1.innerHTML = `Váš uložený hlas: <strong>${text}</strong>`;

        let info2 = resultsCard.querySelector('.info-message-results');
        if (!info2) {
            info2 = document.createElement('div');
            info2.className = 'info-message-results';
            info2.style.cssText = 'background: rgba(99, 102, 241, 0.1); color: var(--accent); padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: 600; border: 1px solid rgba(99, 102, 241, 0.2);';
            const headerDiv = resultsCard.querySelector('div');
            headerDiv.insertAdjacentElement('afterend', info2);
        }
        info2.innerHTML = `Vámi zvolená možnost: <strong>${text}</strong>`;
    };
    showVotedText();

    let resultsChart = null;
    let pollingInterval = null;

    const initChart = (votes) => {
        const ctx = document.getElementById('resultsChart').getContext('2d');
        const labels = Object.keys(votes);
        const data = Object.values(votes);

        if (resultsChart) {
            resultsChart.data.labels = labels;
            resultsChart.data.datasets[0].data = data;
            resultsChart.update();
            return;
        }

        resultsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Počet hlasů',
                    data: data,
                    backgroundColor: 'rgba(99, 102, 241, 0.5)',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#f8fafc' }
                    }
                }
            }
        });
    };

    const runConfetti = () => {
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#6366f1', '#10b981', '#f43f5e']
        });
    };

    const updateResultsUI = (votes) => {
        const totalVotes = Object.values(votes).reduce((a, b) => a + b, 0);
        resultsContainer.innerHTML = '';

        initChart(votes);

        for (const [id, count] of Object.entries(votes)) {
            const percentage = totalVotes > 0 ? (count / totalVotes * 100).toFixed(1) : 0;
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            resultItem.innerHTML = `
                <div class="result-info">
                    <span>${id}</span>
                    <span><strong>${count} hlasů</strong> (${percentage}%)</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percentage}%"></div>
                </div>
            `;
            resultsContainer.appendChild(resultItem);
        }
    };

    const fetchResults = async (isBackground = false) => {
        try {
            const res = await fetch('/api/results');
            const votes = await res.json();
            updateResultsUI(votes);

            if (!isBackground) {
                votingCard.style.display = 'none';
                resultsCard.style.display = 'block';
                startPolling();
            }
        } catch (err) {
            console.error('Chyba při načítání:', err);
        }
    };

    const startPolling = () => {
        if (pollingInterval) clearInterval(pollingInterval);
        pollingInterval = setInterval(() => fetchResults(true), 5000);
    };

    const stopPolling = () => {
        if (pollingInterval) clearInterval(pollingInterval);
    };

    voteForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const selected = voteForm.querySelector('input[name="vote"]:checked');
        if (!selected) return;

        try {
            const res = await fetch('/api/vote', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ option: selected.value })
            });

            if (res.status === 403) {
                alert('Již jste hlasoval(a). Více hlasů není povoleno.');
                if (!localStorage.getItem('votedOptionText')) {
                    localStorage.setItem('votedOptionText', selected.nextElementSibling.textContent);
                    showVotedText();
                }
                fetchResults(true);
                return;
            }

            const votes = await res.json();
            const selectedText = selected.nextElementSibling.textContent;
            localStorage.setItem('votedOptionText', selectedText);
            showVotedText();
            runConfetti();
            updateResultsUI(votes);
            votingCard.style.display = 'none';
            resultsCard.style.display = 'block';
            startPolling();
        } catch (err) {
            alert('Chyba při odesílání.');
        }
    });

    showResultsBtn.addEventListener('click', () => fetchResults(false));

    backToVoteBtn.addEventListener('click', () => {
        stopPolling();
        resultsCard.style.display = 'none';
        votingCard.style.display = 'block';
    });

    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            const token = prompt('Zadejte administrátorský token pro smazání všech hlasů:');
            if (!token) return;

            try {
                const res = await fetch('/api/reset', {
                    method: 'POST',
                    headers: { 'Authorization': token }
                });

                if (res.ok) {
                    alert('Hlasy úspěšně resetovány.');
                    fetchResults(false);
                } else {
                    alert('Neplatný token!');
                }
            } catch (err) {
                alert('Chyba komunikace se serverem.');
            }
        });
    }
});
