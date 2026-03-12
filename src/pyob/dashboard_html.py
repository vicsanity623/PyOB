OBSERVER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyOB // ARCHITECT HUD</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;600&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #0a0a0c; --card: #141417; --accent: #00ffa3; --text: #e0e0e6; --dim: #88888e; --err: #ff4d4d; }
        * { box-sizing: border-box; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; padding: 15px; line-height: 1.5; }
        .hud-container { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        /* Typography & Glow */
        h1 { grid-column: span 2; font-family: 'JetBrains Mono'; font-size: 1.2rem; letter-spacing: 2px; color: var(--accent); text-transform: uppercase; margin: 10px 0; display: flex; justify-content: space-between; }
        .glow { text-shadow: 0 0 15px var(--accent); }
        /* Component Cards */
        .card { background: var(--card); border: 1px solid #2a2a30; border-radius: 8px; padding: 20px; overflow: hidden; position: relative; }
        .card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: linear-gradient(90deg, transparent, var(--accent), transparent); opacity: 0.3; }
        .label { font-size: 0.7rem; font-weight: 600; color: var(--dim); text-transform: uppercase; margin-bottom: 12px; letter-spacing: 1px; display: flex; align-items: center; gap: 8px; }
        .label::before { content: ''; width: 6px; height: 6px; background: var(--accent); border-radius: 50%; box-shadow: 0 0 8px var(--accent); }
        /* Data Displays */
        .data-box { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; height: 250px; overflow-y: auto; background: #00000044; border-radius: 4px; padding: 12px; color: #ced4e0; scrollbar-width: thin; }
        .stat-grid { grid-column: span 2; display: flex; gap: 40px; background: var(--card); padding: 15px 25px; border-radius: 8px; border: 1px solid #2a2a30; }
        .stat-item { display: flex; flex-direction: column; }
        .stat-val { font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono'; color: #fff; }
        .stat-lbl { font-size: 0.6rem; color: var(--dim); }
        /* Mobile Specifics */
        @media (max-width: 768px) {
            .hud-container { grid-template-columns: 1fr; }
            h1, .stat-grid { grid-column: 1; }
            .stat-grid { flex-wrap: wrap; gap: 20px; }
        }
        .status-pill { padding: 4px 12px; border-radius: 20px; font-size: 0.7rem; font-weight: 800; background: #222; }
        .evolving { color: var(--accent); border: 1px solid var(--accent); box-shadow: 0 0 10px #00ffa344; }
        input, textarea { background: #000; border: 1px solid #2a2a30; color: var(--accent); padding: 10px; border-radius: 4px; width: 100%; font-family: 'JetBrains Mono'; margin-bottom: 10px; }
        button { width: 100%; padding: 12px; background: var(--accent); color: #000; border: none; border-radius: 4px; font-weight: 700; cursor: pointer; transition: 0.2s; }
        button:hover { filter: brightness(1.2); }
        /* Specific styles for queue items */
        .queue-item {
            margin-bottom: 8px;
            padding: 8px;
            background: #00000066;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: 'JetBrains Mono';
            font-size: 0.8em;
            color: #ced4e0;
        }
        .queue-item button {
            width: auto;
            padding: 5px 10px;
            font-size: 0.7em;
            margin-left: 5px;
            border-radius: 3px;
        }
        .queue-item .move-btn { background: #4a4a50; color: var(--text); }
        .queue-item .remove-btn { background: #cc0000; color: #fff; }
    </style>
</head>
<body>
    <h1>
        <span>PyOB // Evolution Engine</span>
        <span id="status-pill" class="status-pill">READY</span>
    </h1>
    <div class="hud-container">
        <div class="stat-grid">
            <div class="stat-item"><span class="stat-lbl">Iteration</span><span id="iteration" class="stat-val">--</span></div>
            <div class="stat-item"><span class="stat-lbl">Symbolic Ledger</span><span id="ledger" class="stat-val">--</span></div>
            <div class="stat-item"><span class="stat-lbl">Pending Cascades</span><span id="queue-count" class="stat-val">--</span></div>
        </div>
        <div class="card">
            <div class="label">Logic Memory (MEMORY.md)</div>
            <textarea id="memory" class="data-box" style="height: 250px;">Initializing brain...</textarea>
            <button onclick="saveMemory()" style="margin-top: 10px;">SAVE MEMORY</button>
        </div>
        <div class="card">
            <div class="label">System Logs (HISTORY.md)</div>
            <div id="history" class="data-box">No history yet.</div>
        </div>
        <div class="card" style="grid-column: span 2;">
            <div class="label">Architectural Analysis</div>
            <div id="analysis" class="data-box" style="height: 350px;">Scanning structure...</div>
        </div>
        <div class="card" style="grid-column: span 2;">
            <div class="label">Pending Patch Reviews</div>
            <div id="pending-patches" class="data-box" style="height: 250px;">No pending patches.</div>
        </div>
        <div class="card">
            <div class="label">Manual Override</div>
            <input type="text" id="manualTargetFile" placeholder="src/pyob/target.py">
            <button onclick="setManualTarget()">FORCE TARGET</button>
        </div>
        <div class="card">
            <div class="label">Manual Cascade Injection</div>
            <input type="text" id="cascadeItem" placeholder="e.g., src/pyob/new_feature.py or 'Refactor dashboard'">
            <button onclick="addCascadeItem()" style="margin-top: 10px;">ADD TO QUEUE</button>
        </div>
        <div class="card">
            <div class="label">Queue Status</div>
            <div id="queue" class="data-box" style="height: 200px;">IDLE</div> <!-- Increased height for interactive queue -->
        </div>
    </div>

    <script>
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
                document.getElementById('memory').value = data.memory || "Brain empty."; // Changed to .value for textarea
                document.getElementById('history').innerText = data.history || "No logs.";
                document.getElementById('analysis').innerText = data.analysis || "Parsing...";

                // --- START NEW QUEUE RENDERING LOGIC ---
                const queueDiv = document.getElementById('queue');
                queueDiv.innerHTML = ''; // Clear previous content
                if (data.cascade_queue && data.cascade_queue.length > 0) {
                    data.cascade_queue.forEach((item, index) => {
                        const itemElement = document.createElement('div');
                        itemElement.className = 'queue-item';
                        itemElement.innerHTML = `
                            <span style="flex-grow: 1;">${item}</span>
                            <div style="display: flex; gap: 5px;">
                                <button class="move-btn" onclick="moveQueueItem('${item}', 'up')">Ã¢â€ â€˜</button>
                                <button class="move-btn" onclick="moveQueueItem('${item}', 'down')">Ã¢â€ â€œ</button>
                                <button class="remove-btn" onclick="removeQueueItem('${item}')">X</button>
                            </div>
                        `;
                        queueDiv.appendChild(itemElement);
                    });
                } else {
                    queueDiv.innerText = "EMPTY";
                }
                // --- END NEW QUEUE RENDERING LOGIC ---

                await updatePendingPatches(); // Refresh pending patches
            } catch (e) { document.getElementById('status-pill').innerText = "OFFLINE"; console.error("Error updating stats:", e); }
        }

        async function setManualTarget() {
            const targetFile = document.getElementById('manualTargetFile').value;
            if (!targetFile) return;
            await fetch('/api/set_target_file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_file: targetFile })
            });
            document.getElementById('manualTargetFile').value = '';
        }

        async function updatePendingPatches() {
            try {
                const response = await fetch('/api/pending_patches');
                const data = await response.json();
                const patchesDiv = document.getElementById('pending-patches');
                patchesDiv.innerHTML = ''; // Clear previous content

                if (data.patches && data.patches.length > 0) {
                    data.patches.forEach(patch => {
                        const patchElement = document.createElement('div');
                        patchElement.style.marginBottom = '10px';
                        patchElement.innerHTML = `
                            <span style="color: var(--accent); font-weight: 700;">Patch ID: ${patch.id}</span><br>
                            <span style="font-size: 0.8em; color: var(--dim);">File: ${patch.target_file}</span><br>
                            <span style="font-size: 0.8em; color: var(--dim);">Description: ${patch.description || 'N/A'}</span><br>
                            <button onclick="reviewPatch('${patch.id}', 'approve')" style="width: 48%; margin-right: 4%; background: #00cc66; color: #000;">APPROVE</button>
                            <button onclick="reviewPatch('${patch.id}', 'reject')" style="width: 48%; background: #cc0000; color: #fff;">REJECT</button>
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
                await fetch('/api/review_patch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ patch_id: patchId, action: action })
                });
                // Refresh stats and patches after review
                await updateStats();
            } catch (e) {
                console.error(`Failed to ${action} patch ${patchId}:`, e);
                alert(`Failed to ${action} patch ${patchId}. Check console for details.`);
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
                const result = await response.json();
                if (response.ok) {
                    alert('Logic Memory saved successfully!');
                    await updateStats(); // Refresh to ensure consistency
                } else {
                    alert(`Failed to save Logic Memory: ${result.error}`);
                }
            } catch (e) {
                console.error("Failed to save Logic Memory:", e);
                alert("Error saving Logic Memory. Check console for details.");
            }
        }

        async function addCascadeItem() {
            const item = document.getElementById('cascadeItem').value;
            if (!item) {
                alert('Please enter an item to add to the cascade queue.');
                return;
            }
            try {
                const response = await fetch('/api/cascade_queue/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ item: item })
                });
                const result = await response.json();
                if (response.ok) {
                    alert(`'${item}' added to cascade queue.`);
                    document.getElementById('cascadeItem').value = ''; // Clear input
                    await updateStats(); // Refresh queue display
                } else {
                    alert(`Failed to add item to queue: ${result.error}`);
                }
            } catch (e) {
                console.error("Failed to add item to cascade queue:", e);
                alert("Error adding item to cascade queue. Check console for details.");
            }
        }

        // --- START NEW QUEUE INTERACTION FUNCTIONS ---
        async function moveQueueItem(itemId, direction) {
            try {
                await fetch('/api/cascade_queue/move', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ item_id: itemId, direction: direction })
                });
                await updateStats(); // Refresh queue after move
            } catch (e) {
                console.error(`Failed to move item ${itemId} ${direction}:`, e);
                alert(`Failed to move item. Check console for details.`);
            }
        }

        async function removeQueueItem(itemId) {
            if (!confirm(`Are you sure you want to remove "${itemId}" from the queue?`)) {
                return;
            }
            try {
                await fetch('/api/cascade_queue/remove', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ item_id: itemId })
                });
                await updateStats(); // Refresh queue after removal
            } catch (e) {
                console.error(`Failed to remove item ${itemId}:`, e);
                alert(`Failed to remove item. Check console for details.`);
            }
        }
        // --- END NEW QUEUE INTERACTION FUNCTIONS ---

        setInterval(updateStats, 3000);
        updateStats();
    </script>
</body>
</html>
"""
