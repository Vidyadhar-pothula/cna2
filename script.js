document.addEventListener('DOMContentLoaded', () => {
    let currentPhase = 1;
    const totalPhases = 5;

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

    // State
    let userSymbolList = {};
    let extractedEntities = [];

    function updatePhase() {
        // Update UI
        phases.forEach(p => p.classList.remove('active'));
        document.getElementById(`phase-${currentPhase}`).classList.add('active');

        phaseIndicator.textContent = getPhaseTitle(currentPhase);

        prevBtn.disabled = currentPhase === 1;
        nextBtn.disabled = currentPhase === totalPhases;

        // Trigger Phase Specific Animations
        if (currentPhase === 2) runPhase2();
        if (currentPhase === 3) runPhase3();
        if (currentPhase === 4) runPhase4();
        if (currentPhase === 5) runPhase5();
    }

    function getPhaseTitle(phase) {
        switch (phase) {
            case 1: return 'Phase 1: Input Configuration';
            case 2: return 'Phase 2: Text Processing & NER';
            case 3: return 'Phase 3: Constraint Tally';
            case 4: return 'Phase 4: Logic Translation';
            case 5: return 'Phase 5: Validation & Final Output';
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
        simulateBtn.textContent = "Processing PDF with LayoutLMv3...";
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

            // Map API data to internal format
            // API returns: [{token: "SUSV", label: "B-EQUIPMENT", ...}]
            // We map to: {phrase: "SUSV", type: "equipment"}
            extractedEntities = data.map(item => ({
                phrase: item.token,
                type: item.label.replace('B-', '').replace('I-', '').toLowerCase()
            }));

            // Reset and Move to Phase 2
            nerOutput.innerHTML = '';
            currentPhase = 2;
            updatePhase();

            // Visualize NER (using the extracted entities)
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
        // Simple visualization: Just listing the tokens as they appear in the extraction
        // In a real app, we would overlay this on the PDF image

        entities.forEach(entity => {
            const span = document.createElement('span');
            span.className = `ner-token tag ${entity.type}`;
            span.textContent = entity.phrase + ' ';

            const lbl = document.createElement('span');
            lbl.className = 'ner-label';
            lbl.textContent = entity.type.toUpperCase();
            span.appendChild(lbl);

            nerOutput.appendChild(span);
        });
    }

    // Phase 3: Constraint Tally
    function runPhase3() {
        tallyBoard.innerHTML = '';
        let delay = 0;

        // Process each extracted entity
        extractedEntities.forEach(entity => {
            setTimeout(() => {
                const item = document.createElement('div');
                let matchType = 'infer';
                let targetID = '???';
                let statusText = 'INFERRED';

                // Check against User Symbol List
                const matchKey = Object.keys(userSymbolList).find(k =>
                    entity.phrase.toLowerCase().includes(k.toLowerCase()) ||
                    k.toLowerCase().includes(entity.phrase.toLowerCase())
                );

                if (matchKey) {
                    matchType = 'match';
                    targetID = userSymbolList[matchKey];
                    statusText = 'MATCH FOUND';
                } else {
                    // Inference Logic (Hardcoded for demo)
                    if (entity.phrase.includes("Outgoing")) targetID = "FT-201.OUT";
                    else if (entity.phrase.includes("weight")) targetID = "V-110.dWT";
                    else if (entity.phrase.includes("time")) targetID = "P-TIME_ALARM";
                }

                item.className = `tally-item ${matchType}`;
                item.innerHTML = `
                    <span class="tally-source">${entity.phrase}</span>
                    <span class="tally-arrow">→</span>
                    <span class="tally-target">${targetID}</span>
                    <span class="tag match-${matchType === 'match' ? 'success' : 'infer'}">${statusText}</span>
                `;
                tallyBoard.appendChild(item);

            }, delay);
            delay += 800;
        });
    }

    // Phase 4: Logic Translation
    function runPhase4() {
        initialCodeDisplay.textContent = '';
        const code = `// Initial Translation using Constrained Symbols
IF (V-110.State == FEED) 
   AND (ABS(FT-201.IN - FT-201.OUT - V-110.dWT) > P-TOL)
THEN
   V-110.Alarm_Deviation = TRUE`;

        typeWriter(code, initialCodeDisplay);
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
            checkTime.innerHTML = '<span class="status">✅</span> Missing Parameter "configurable time" -> Added DELAY_TIME';
            checkTime.classList.add('passed');
        }, 2500);

        setTimeout(() => {
            const finalCode = `// Logic TALLIED against User Symbol List
DEVIATION = ABS(FT-201.IN - FT-201.OUT - V-110.dWT)

IF (V-110.State == FEED) 
   AND (DEVIATION > P-TOL)
THEN
   DELAY_TIME = P-TIME_ALARM  // Inferred/Standardized Time Parameter
   IF (DEVIATION > P-TOL) FOR DELAY_TIME
   THEN
      V-110.Alarm_Deviation = TRUE
   END_IF
END_IF`;
            typeWriter(finalCode, finalCodeDisplay);
        }, 3500);
    }

    function typeWriter(text, element) {
        let i = 0;
        element.textContent = '';
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, 10);
            }
        }
        type();
    }

    // Initial Start
    updatePhase();
});
