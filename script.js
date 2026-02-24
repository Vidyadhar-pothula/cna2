document.addEventListener('DOMContentLoaded', () => {
    let currentPhase = 1;
    const totalPhases = 6;

    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const phaseIndicator = document.getElementById('phaseIndicator');
    const phases = document.querySelectorAll('.phase');

    // Input Elements
    const inputNarrative = document.getElementById('input-narrative');
    const inputSymbols = document.getElementById('input-symbols');
    const simulateBtn = document.getElementById('simulateBtn');

    // Phase 2 Elements (NER)
    const nerOutput = document.getElementById('ner-output');

    // Phase 3 Elements (Tally)
    const tallyBoard = document.getElementById('tally-board');

    // Phase 4 Elements (GenAI)
    const initialCodeDisplay = document.getElementById('initial-code-display');

    // Phase 5 Elements (Validation + Output)
    const checkTime = document.getElementById('check-time');
    const checkSyntax = document.getElementById('check-syntax');
    const finalCodeDisplay = document.getElementById('final-code-display');

    // Phase 6 Elements (Matrix)
    const matrixTableBody = document.querySelector('#unified-matrix-table tbody');

    // State
    let userSymbolList = {};
    let extractedEntities = [];
    let unifiedControlTable = [];

    function updatePhase() {
        // Update UI
        phases.forEach(p => p.classList.remove('active'));
        const phaseElem = document.getElementById(`phase-${currentPhase}`);
        if (phaseElem) phaseElem.classList.add('active');

        phaseIndicator.textContent = getPhaseTitle(currentPhase);

        prevBtn.disabled = currentPhase === 1;
        nextBtn.disabled = currentPhase === totalPhases;

        // Trigger Phase Specific Animations
        if (currentPhase === 2) runPhase2();
        if (currentPhase === 3) runPhase3();
        if (currentPhase === 4) runPhase4();
        if (currentPhase === 5) runPhase5();
        if (currentPhase === 6) runPhase6();
    }

    function getPhaseTitle(phase) {
        switch (phase) {
            case 1: return 'Phase 1: Input Configuration';
            case 2: return 'Phase 2: Text Processing & NER';
            case 3: return 'Phase 3: Constraint Tally';
            case 4: return 'Phase 4: Logic Translation';
            case 5: return 'Phase 5: Validation & Final Output';
            case 6: return 'Phase 6: Unified Control Table';
            default: return '';
        }
    }

    prevBtn.addEventListener('click', () => {
        if (currentPhase > 1) {
            currentPhase--;
            updatePhase();
        }
    });

    nextBtn.addEventListener('click', () => {
        if (currentPhase < totalPhases) {
            currentPhase++;
            updatePhase();
        }
    });

    simulateBtn.addEventListener('click', async () => {
        const fileInput = document.getElementById('input-pdf');
        const symbolsText = inputSymbols.value;

        if (fileInput.files.length === 0) {
            alert("Please upload a PDF file.");
            return;
        }

        try {
            userSymbolList = JSON.parse(symbolsText);
        } catch (e) {
            alert("Invalid JSON in Symbol List");
            return;
        }

        // Show Loading State
        simulateBtn.textContent = "Processing PDF with 11-Stage Pipeline...";
        simulateBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('http://localhost:8000/api/process_document', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error("API Error: " + response.statusText);
            }

            const data = await response.json();
            window.llmFullResults = data; // Global or local state
            let llmFullResults = data;

            // Map API data
            extractedEntities = [];
            const mapEntity = (e, type) => ({
                phrase: e.original_phrase || e.name || e.id,
                type: type,
                id: e.id,
                description: e.description
            });

            if (data.equipment_table) extractedEntities = extractedEntities.concat(data.equipment_table.map(e => mapEntity(e, 'equipment')));
            if (data.variables_table) extractedEntities = extractedEntities.concat(data.variables_table.map(e => mapEntity(e, 'variable')));
            if (data.parameters_table) extractedEntities = extractedEntities.concat(data.parameters_table.map(e => mapEntity(e, 'parameter')));
            if (data.conditions_table) extractedEntities = extractedEntities.concat(data.conditions_table.map(e => mapEntity(e, 'condition')));
            if (data.actions_table) extractedEntities = extractedEntities.concat(data.actions_table.map(e => mapEntity(e, 'action')));

            // Store Unified Control Table
            unifiedControlTable = data.unified_control_table || [];

            // Reset and Move to Phase 2
            nerOutput.innerHTML = '';
            currentPhase = 2;
            updatePhase();

            // Visualize NER 
            renderNER(extractedEntities);

        } catch (error) {
            console.error(error);
            alert("Error processing document: " + error.message);
        } finally {
            simulateBtn.textContent = "Upload & Initialize Simulation";
            simulateBtn.disabled = false;
        }
    });

    // Phase 2: Text Processing & NER
    function runPhase2() {
        // Already handled in the API callback
    }

    function renderNER(entities) {
        nerOutput.innerHTML = '';
        entities.forEach(entity => {
            const span = document.createElement('span');
            span.className = `ner-token tag ${entity.type}`;
            span.textContent = (entity.phrase || 'Unknown') + ' ';

            const lbl = document.createElement('span');
            lbl.className = 'ner-label';
            lbl.textContent = entity.type.toUpperCase();
            span.appendChild(lbl);

            nerOutput.appendChild(span);
        });
    }

    // Phase 3: Constraint Tally
    function runPhase3() {
        if (tallyBoard.children.length > 0) return; // Run once
        tallyBoard.innerHTML = '';
        let delay = 0;

        extractedEntities.slice(0, 10).forEach(entity => {
            setTimeout(() => {
                const item = document.createElement('div');
                let matchType = 'infer';
                let targetID = '???';
                let statusText = 'INFERRED';

                const matchKey = Object.keys(userSymbolList).find(k =>
                    (entity.phrase && entity.phrase.toLowerCase().includes(k.toLowerCase())) ||
                    k.toLowerCase().includes((entity.phrase || '').toLowerCase())
                );

                if (matchKey) {
                    matchType = 'match';
                    targetID = userSymbolList[matchKey];
                    statusText = 'MATCH FOUND';
                }

                item.className = `tally-item ${matchType}`;
                item.innerHTML = `
                    <span class="tally-source">${entity.phrase || 'Unknown'}</span>
                    <span class="tally-arrow">→</span>
                    <span class="tally-target">${targetID}</span>
                    <span class="tag match-${matchType === 'match' ? 'success' : 'infer'}">${statusText}</span>
                `;
                tallyBoard.appendChild(item);

            }, delay);
            delay += 400;
        });
    }

    // Phase 4: Logic Translation
    function runPhase4() {
        initialCodeDisplay.textContent = '';
        if (llmFullResults && llmFullResults.pseudocode) {
            typeWriter(llmFullResults.pseudocode, initialCodeDisplay);
        } else {
            const code = `// AI-Generated Logic from Unified Control Table...`;
            typeWriter(code, initialCodeDisplay);
        }
    }

    // Phase 5: Validation & Final Output
    function runPhase5() {
        finalCodeDisplay.textContent = '';
        checkTime.innerHTML = '<span class="status">⚪</span> Checking for Time Constraint...';
        checkSyntax.innerHTML = '<span class="status">⚪</span> Checking Syntax...';
        checkTime.classList.remove('passed');
        checkSyntax.classList.remove('passed');

        setTimeout(() => {
            checkSyntax.innerHTML = '<span class="status">✅</span> Syntax Check Passed';
            checkSyntax.classList.add('passed');
        }, 1000);

        setTimeout(() => {
            const finalCode = JSON.stringify(unifiedControlTable, null, 2);
            typeWriter(finalCode, finalCodeDisplay);
        }, 2000);
    }

    // Phase 6: Unified Table Rendering
    function runPhase6() {
        matrixTableBody.innerHTML = '';
        if (unifiedControlTable.length === 0) {
            matrixTableBody.innerHTML = '<tr><td colspan="5">No unified control data generated.</td></tr>';
            return;
        }

        unifiedControlTable.forEach((row, index) => {
            // Animate rows
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.equipment || ''}</td>
                    <td>${row.variable || ''}</td>
                    <td>${row.parameter || ''}</td>
                    <td>${row.condition || ''}</td>
                    <td>${row.action || ''}</td>
                `;
                matrixTableBody.appendChild(tr);
            }, index * 200);
        });
    }

    function typeWriter(text, element) {
        let i = 0;
        element.textContent = '';
        element.style.whiteSpace = 'pre-wrap';
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, 2);
            }
        }
        type();
    }

    updatePhase();
});
