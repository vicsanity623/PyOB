async function updateStats() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        document.getElementById('iteration').innerText = data.iteration || "0";
        document.getElementById('ledger').innerText = (data.ledger_stats?.definitions || 0) + " SYM";
        document.getElementById('queue-count').innerText = data.cascade_queue?.length || "0";
        const pill = document.getElementById('status-pill');
        const isEvolving = data.cascade_queue?.length > 0 || data.patches_count > 0;
        pill.innerText = isEvolving ? "EVOLVING" : "STABLE";
        pill.className = isEvolving ? "status-pill evolving" : "status-pill";
        document.getElementById('memory').value = data.memory || "Brain empty.";
        document.getElementById('history').innerText = data.history || "No logs.";
        // Handle structured analysis data for interactive issues
        const analysisContainer = document.getElementById('analysis');
        analysisContainer.innerHTML = ''; // Clear existing content
        const filterText = document.getElementById('analysisFilter').value.toLowerCase();

        if (Array.isArray(data.analysis) && data.analysis.length > 0) {
            const filteredAnalysis = data.analysis.filter(issue =>
                issue.description.toLowerCase().includes(filterText)
            );
            filteredAnalysis.forEach(issue => {
                const issueElement = document.createElement('div');
                issueElement.style.marginBottom = '8px';
                issueElement.style.padding = '8px';
                issueElement.style.background = '#00000066';
                issueElement.style.borderRadius = '4px';
                issueElement.style.display = 'flex';
                issueElement.style.alignItems = 'center';
                issueElement.style.justifyContent = 'space-between';
                issueElement.style.fontFamily = 'JetBrains Mono';
                issueElement.style.fontSize = '0.8em';
                issueElement.style.color = '#ced4e0';

                const statusColor = issue.status === 'acknowledged' ? 'var(--dim)' : 'var(--err)';
                const statusText = issue.status === 'acknowledged' ? 'ACKNOWLEDGED' : 'PENDING';

                issueElement.innerHTML = `
                    <span style="flex-grow: 1;">${issue.description}</span>
                    <span style="font-size: 0.7em; font-weight: 600; color: ${statusColor}; margin-left: 10px;">${statusText}</span>
                    <button onclick="acknowledgeIssue('${issue.id}')"
                            style="width: auto; padding: 5px 10px; font-size: 0.7em; border-radius: 3px; margin-left: 10px;
                                   background: ${issue.status === 'acknowledged' ? '#4a4a50' : 'var(--accent)'};
                                   color: ${issue.status === 'acknowledged' ? 'var(--text)' : '#000'};"
                            ${issue.status === 'acknowledged' ? 'disabled' : ''}>
                        ${issue.status === 'acknowledged' ? 'ACKNOWLEDGED' : 'ACKNOWLEDGE'}
                    </button>
                `;
                analysisContainer.appendChild(issueElement);
            });
        } else {
            analysisContainer.innerText = "No issues found."; // Always display this if no issues or not an array
        }

        // Update chart after fetching data
        updateChart(data);

        const queueDiv = document.getElementById('queue');
        queueDiv.innerHTML = '';
        if (data.cascade_queue && data.cascade_queue.length > 0) {
            data.cascade_queue.forEach((item, index) => {
                const itemElement = document.createElement('div');
                itemElement.className = 'queue-item';

                const textSpan = document.createElement('span');
                textSpan.style.flexGrow = '1';
                textSpan.innerText = item; // Use innerText for safety

                const buttonDiv = document.createElement('div');
                buttonDiv.style.display = 'flex';
                buttonDiv.style.gap = '5px';

                const moveUpBtn = document.createElement('button');
                moveUpBtn.className = 'move-btn';
                moveUpBtn.innerHTML = '&#x25B2;';
                moveUpBtn.addEventListener('click', () => moveQueueItem(item, 'up'));

                const moveDownBtn = document.createElement('button');
                moveDownBtn.className = 'move-btn';
                moveDownBtn.innerHTML = '&#x25BC;';
                moveDownBtn.addEventListener('click', () => moveQueueItem(item, 'down'));

                const removeBtn = document.createElement('button');
                removeBtn.className = 'remove-btn';
                removeBtn.innerHTML = 'X';
                removeBtn.addEventListener('click', () => removeQueueItem(item));

                buttonDiv.appendChild(moveUpBtn);
                buttonDiv.appendChild(moveDownBtn);
                buttonDiv.appendChild(removeBtn);

                itemElement.appendChild(textSpan);
                itemElement.appendChild(buttonDiv);
                queueDiv.appendChild(itemElement);
            });
        } else {
            queueDiv.innerText = "EMPTY";
        }

        await updatePendingPatches();
    } catch (e) { document.getElementById('status-pill').innerText = "OFFLINE"; console.error("Error updating stats:", e); }
}

async function acknowledgeIssue(issueId) {
    try {
        const response = await fetch(`/api/acknowledge-issue/${issueId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'acknowledged' })
        });
        if (response.ok) {
            await updateStats(); // Refresh dashboard to show updated status
        } else {
            console.error(`Failed to acknowledge issue ${issueId}:`, await response.text());
            alert('Error acknowledging issue.');
        }
    } catch (e) {
        console.error(`Failed to acknowledge issue ${issueId}:`, e);
        alert('Network error acknowledging issue.');
    }
}

async function updatePendingPatches() {
    try {
        const response = await fetch('/api/pending_patches');
        const data = await response.json();
        const patchesDiv = document.getElementById('pending-patches');
        patchesDiv.innerHTML = '';

        if (data.patches && data.patches.length > 0) {
            data.patches.forEach(patch => {
                const patchElement = document.createElement('div');
                patchElement.style.marginBottom = '10px';
                patchElement.innerHTML = `
                    <span style="color: var(--accent); font-weight: 700;">Patch ID: ${patch.id}</span><br>
                    <span class="patch-file" style="font-size: 0.8em; color: var(--dim);">File: ${patch.file || 'N/A'}</span><br>
                    <span class="patch-description" style="font-size: 0.8em; color: var(--dim);">Description: ${patch.description || 'No description'}</span><br>
                    <button onclick="viewPatchDiff('${patch.id}')" style="width: 32%; margin-right: 2%; background: #007bff; color: #fff;">VIEW DIFF</button>
                    <button onclick="reviewPatch('${patch.id}', 'approved')" style="width: 32%; margin-right: 2%; background: #00cc00; color: #000;">APPROVE</button>
                    <button onclick="reviewPatch('${patch.id}', 'reject')" style="width: 32%; background: #cc0000; color: #fff;">REJECT</button>
                `;
                patchesDiv.appendChild(patchElement);
            });
        } else {
            patchesDiv.innerText = "No pending patches.";
        }
    } catch (e) {
        console.error("Failed to fetch pending patches:", e);
        document.getElementById('pending-patches').innerText = "Error loading patches.";
    }
}

async function reviewPatch(patchId, action) {
    try {
        if (action === 'approved') {
            await fetch('/api/review_patch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ patch_id: patchId, action: 'approved' })
            });
        } else {
            await fetch('/api/review_patch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ patch_id: patchId, action: action })
            });
        }
        await updateStats();
    } catch (e) {
        console.error(`Failed to ${action} patch ${patchId}:`, e);
    }
}

async function saveMemory() {
    const memoryContent = document.getElementById('memory').value;
    try {
        const response = await fetch('/api/update_memory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: memoryContent })
        });
        if (response.ok) {
            alert('Logic Memory saved successfully!');
            await updateStats();
        }
    } catch (e) {
        console.error("Failed to save Logic Memory:", e);
    }
}

async function addCascadeItem() {
    const item = document.getElementById('cascadeItem').value;
    if (!item) return;
    try {
        const response = await fetch('/api/cascade_queue/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item: item })
        });
        if (response.ok) {
            document.getElementById('cascadeItem').value = '';
            await updateStats();
        }
    } catch (e) {
        console.error("Failed to add item to cascade queue:", e);
    }
}

async function moveQueueItem(itemId, direction) {
    try {
        await fetch('/api/cascade_queue/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId, direction: direction })
        });
        await updateStats();
    } catch (e) {
        console.error(`Failed to move item ${itemId} ${direction}:`, e);
    }
}

async function removeQueueItem(itemId) {
    if (!confirm(`Are you sure you want to remove "${itemId.replace(/"/g, '\\"')}" from the queue?`)) return;
    try {
        await fetch('/api/cascade_queue/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId })
        });
        await updateStats();
    } catch (e) {
        console.error(`Failed to remove item ${itemId}:`, e);
    }
}

async function viewPatchDiff(patchId) {
    try {
        const response = await fetch(`/api/patch_diff/${patchId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        document.getElementById('diffModalPatchId').innerText = `(ID: ${patchId})`;
        document.getElementById('diffContent').innerText = data.diff || "No diff available.";
        openDiffModal();
    } catch (e) {
        console.error(`Failed to fetch diff for patch ${patchId}:`, e);
        alert(`Error viewing diff: ${e.message}`);
    }
}

function openDiffModal() {
    document.getElementById('diffModal').style.display = 'block';
}

function closeDiffModal() {
    document.getElementById('diffModal').style.display = 'none';
    document.getElementById('diffContent').innerText = ''; // Clear content on close
    document.getElementById('diffModalPatchId').innerText = '';
}

function updateChart(data) {
    const ctx = document.getElementById('statsChart').getContext('2d');
    const iterationData = data.iterationHistory ? data.iterationHistory.map((val, index) => { return { x: index, y: val }; }) : [];

    if (window.statsChart) {
        window.statsChart.data.labels = iterationData.map(d => d.x);
        window.statsChart.data.datasets[0].data = iterationData.map(d => d.y);
        window.statsChart.update();
    } else {
        window.statsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: iterationData.map(d => d.x),
                datasets: [{
                    label: 'Iterations Over Time',
                    data: iterationData.map(d => d.y),
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}