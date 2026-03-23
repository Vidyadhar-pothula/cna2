document.addEventListener('DOMContentLoaded', () => {

    // ============================================================
    // 1. CINEMATIC ATMOSPHERE
    // ============================================================

    // Inject grid overlay
    const gridOverlay = document.createElement('div');
    gridOverlay.className = 'grid-overlay';
    document.body.prepend(gridOverlay);

    // Intro → Main App transition
    const introLayer = document.querySelector('.intro-layer');
    const mainApp    = document.querySelector('.main-app');

    if (introLayer && mainApp) {
        mainApp.style.opacity    = '0';
        mainApp.style.visibility = 'hidden';

        let introGone = false;

        const dismissIntro = () => {
            if (introGone) return;
            introGone = true;
            introLayer.style.opacity    = '0';
            introLayer.style.visibility = 'hidden';
            setTimeout(() => {
                introLayer.style.display     = 'none';
                mainApp.style.visibility     = 'visible';
                mainApp.style.opacity        = '1';
                mainApp.style.transition     = 'opacity 1s ease';
            }, 1200);
        };

        window.addEventListener('scroll',  () => { if (window.scrollY > 10) dismissIntro(); }, { passive: true });
        introLayer.addEventListener('click', dismissIntro);
        window.addEventListener('keydown',  dismissIntro);
    }

    // Scroll-based section reveal
    const revealSections = document.querySelectorAll(
        '.objective-section, .upload-section, .processing-section'
    );
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
    }, { threshold: 0.08 });
    revealSections.forEach(s => revealObserver.observe(s));

    // Subtle mouse parallax on intro logo
    const orionContainer = document.querySelector('.orion-container');
    if (orionContainer) {
        window.addEventListener('mousemove', (e) => {
            const x = (e.clientX / window.innerWidth  - 0.5) * 8;
            const y = (e.clientY / window.innerHeight - 0.5) * 4;
            orionContainer.style.transform  = `translate(${x}px, ${y}px)`;
            orionContainer.style.transition = 'transform 0.6s ease';
        });
    }

    // ============================================================
    // 2. JOURNEY TIMELINE — step activation helper
    // ============================================================

    const nodes = document.querySelectorAll('.node');

    function setActiveStep(stepNumber) {
        nodes.forEach(node => {
            const s = parseInt(node.dataset.step);
            node.classList.toggle('active',    s === stepNumber);
            node.classList.toggle('completed', s < stepNumber);
        });
    }

    // ============================================================
    // 3. START ANALYSIS — PDF upload & API call
    // ============================================================

    const startBtn      = document.getElementById('startBtn');
    const fileInput     = document.getElementById('input-pdf');

    // Result section elements
    const equipmentSection  = document.getElementById('equipment-section');
    const variablesSection  = document.getElementById('variables-section');
    const unifiedSection    = document.getElementById('unified-section');
    const pseudocodeSection = document.getElementById('pseudocode-section');
    const workflowActions   = document.getElementById('workflow-actions');

    const equipmentTbody    = document.getElementById('equipment-tbody');
    const variablesTbody    = document.getElementById('variables-tbody');
    const unifiedTbody      = document.getElementById('unified-tbody');
    const pseudocodeDisplay = document.getElementById('pseudocode-display');

    // Hide all result sections initially
    function resetResults() {
        equipmentSection.style.display  = 'block'; // always show skeleton
        variablesSection.style.display  = 'none';
        unifiedSection.style.display    = 'none';
        pseudocodeSection.style.display = 'none';
        workflowActions.style.display   = 'none';
        equipmentTbody.innerHTML  = '';
        variablesTbody.innerHTML  = '';
        unifiedTbody.innerHTML    = '';
        pseudocodeDisplay.textContent = '';
        setActiveStep(1);
    }

    if (startBtn) {
        startBtn.addEventListener('click', async () => {
            if (!fileInput || fileInput.files.length === 0) {
                alert('Please upload a PDF file first.');
                return;
            }

            // Scroll down to the processing section
            document.querySelector('.processing-section').scrollIntoView({ behavior: 'smooth' });

            startBtn.textContent = 'Processing...';
            startBtn.disabled    = true;
            resetResults();

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            try {
                const response = await fetch('http://localhost:8000/api/process_document', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('API Error: ' + response.statusText);

                const data = await response.json();

                // ---- Step 1: Equipment Table ----
                setActiveStep(1);
                renderEquipment(data.equipment || []);

                // ---- Step 2: Variables (Logic Extraction) ----
                await delay(600);
                setActiveStep(2);
                variablesSection.style.display = 'block';
                renderVariables(data.variables || []);

                // ---- Step 3: Unified Control Table ----
                await delay(600);
                setActiveStep(3);
                unifiedSection.style.display = 'block';
                renderUnified(data.unified_control_table || []);

                // ---- Step 4: Pseudocode ----
                await delay(600);
                setActiveStep(4);
                pseudocodeSection.style.display = 'block';
                const pseudocode = data.pseudocode || JSON.stringify(data.unified_control_table || [], null, 2);
                typeWriter(pseudocode, pseudocodeDisplay);

                // Show action buttons
                await delay(800);
                workflowActions.style.display = 'flex';

            } catch (error) {
                console.error(error);
                alert('Error processing document: ' + error.message);
            } finally {
                startBtn.textContent = 'Start Analysis';
                startBtn.disabled    = false;
            }
        });
    }

    // ============================================================
    // 4. RENDER HELPERS
    // ============================================================

    function renderEquipment(equipment) {
        equipmentTbody.innerHTML = '';
        if (equipment.length === 0) {
            equipmentTbody.innerHTML = '<tr><td colspan="3" style="opacity:0.4;text-align:center;">No equipment data found.</td></tr>';
            return;
        }
        equipment.forEach((item, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="color:var(--green);font-family:'Fira Code',monospace;font-size:0.82rem;">${item.id || ('EQP-' + String(i+1).padStart(2,'0'))}</td>
                    <td>${item.name || item.condition || ''}</td>
                    <td style="opacity:0.7;">${item.description || item.value || ''}</td>
                `;
                equipmentTbody.appendChild(tr);
            }, i * 120);
        });
    }

    function renderVariables(variables) {
        variablesTbody.innerHTML = '';
        if (variables.length === 0) {
            variablesTbody.innerHTML = '<tr><td colspan="3" style="opacity:0.4;text-align:center;">No variables found.</td></tr>';
            return;
        }
        variables.forEach((item, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="color:var(--green);font-family:'Fira Code',monospace;font-size:0.82rem;">${item.id || ('VAR-' + String(i+1).padStart(2,'0'))}</td>
                    <td>${item.name || ''}</td>
                    <td style="opacity:0.7;">${item.value || item.range || ''}</td>
                `;
                variablesTbody.appendChild(tr);
            }, i * 120);
        });
    }

    function renderUnified(rows) {
        unifiedTbody.innerHTML = '';
        if (rows.length === 0) {
            unifiedTbody.innerHTML = '<tr><td colspan="5" style="opacity:0.4;text-align:center;">No unified control data generated.</td></tr>';
            return;
        }
        rows.forEach((row, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.equipment  || ''}</td>
                    <td>${row.variable   || ''}</td>
                    <td>${row.parameter  || ''}</td>
                    <td>${row.condition  || ''}</td>
                    <td>${row.action     || ''}</td>
                `;
                unifiedTbody.appendChild(tr);
            }, i * 150);
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

    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ============================================================
    // 5. WORKFLOW BUTTONS
    // ============================================================

    const btnSimulation = document.getElementById('btn-view-simulation');
    const btnExport     = document.getElementById('btn-export');

    if (btnSimulation) {
        btnSimulation.addEventListener('click', () => {
            window.location.href = '/simulation.html';
        });
    }

    if (btnExport) {
        btnExport.addEventListener('click', () => {
            alert('Export feature coming soon.');
        });
    }

});