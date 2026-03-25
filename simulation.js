// Simulation Logic for 6-Phase Journey
document.addEventListener('DOMContentLoaded', () => {
    let currentPhase = 1;
    const totalPhases = 6;

    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const phaseIndicator = document.getElementById('phaseIndicator');
    const phases = [
        "INPUT CONFIGURATION",
        "SEMANTIC ENTITY EXTRACTION",
        "CONSTRAINT TALLY BOARD",
        "LOGIC TRANSLATION",
        "AGENTIC VALIDATION",
        "UNIFIED CONTROL TABLE"
    ];

    function updatePhaseDisplay() {
        document.querySelectorAll('.phase-content').forEach(p => p.classList.remove('active'));
        const activePhase = document.getElementById(`phase-${currentPhase}`);
        if (activePhase) activePhase.classList.add('active');

        phaseIndicator.textContent = `PHASE ${currentPhase}: ${phases[currentPhase-1]}`;
        prevBtn.disabled = (currentPhase === 1);
        nextBtn.disabled = (currentPhase === totalPhases);
    }

    if (prevBtn) prevBtn.addEventListener('click', () => {
        if (currentPhase > 1) {
            currentPhase--;
            updatePhaseDisplay();
        }
    });

    if (nextBtn) nextBtn.addEventListener('click', () => {
        if (currentPhase < totalPhases) {
            currentPhase++;
            updatePhaseDisplay();
        }
    });

    // Mock/Simulation logic for demonstration
    const simStartBtn = document.getElementById('simStartBtn');
    if (simStartBtn) {
        simStartBtn.addEventListener('click', () => {
            simStartBtn.textContent = "INITIALIZING...";
            simStartBtn.disabled = true;
            setTimeout(() => {
                currentPhase = 2;
                updatePhaseDisplay();
                runPhase2();
            }, 1000);
        });
    }

    function runPhase2() {
        const output = document.getElementById('ner-output');
        output.innerHTML = "<p>Analyzing narrative structure...</p>";
        setTimeout(() => {
            output.innerHTML = `
                <span class="ner-token equipment">P-101<span class="ner-label">EQUIPMENT</span></span> 
                has high pressure 
                <span class="ner-token condition">VALUE > 100<span class="ner-label">CONDITION</span></span>...
            `;
        }, 800);
    }

    updatePhaseDisplay();
});
