document.addEventListener('DOMContentLoaded', () => {

    // ============================================================
    // 1. GRID OVERLAY
    // ============================================================
    const gridOverlay = document.createElement('div');
    gridOverlay.className = 'grid-overlay';
    document.body.prepend(gridOverlay);

    // ============================================================
    // 2. INTRO ANIMATION SEQUENCE
    //    Phase 1 (0s):     Symbol appears tiny, scales up to full size (CSS animation, 1.2s)
    //    Phase 2 (1.8s):   Symbol slides left (translateX) to make room
    //    Phase 3 (2.2s):   RION text fades + slides in from right (mid-slide)
    //    Phase 4 (4s+):    Scroll indicator appears, dismiss becomes active
    // ============================================================

    const introLayer     = document.querySelector('.intro-layer');
    const mainApp        = document.querySelector('.main-app');
    const powerSymbol    = document.querySelector('.power-symbol');
    const orionText      = document.querySelector('.orion-text');
    const orionContainer = document.querySelector('.orion-container');

    // Hide main app until scroll
    if (mainApp) {
        mainApp.style.opacity    = '0';
        mainApp.style.visibility = 'hidden';
    }

    // The container uses flexbox. Symbol starts centered because
    // RION text is invisible (opacity:0, width still 0-ish visually).
    // We offset the symbol right initially so it appears screen-center,
    // then remove the offset as text appears, making it slide left naturally.

    if (powerSymbol && orionText && orionContainer) {

        // Push symbol to center of screen initially
        // (half the width of the RION text, approx)
        powerSymbol.style.transform = 'scale(1) translateX(0)';

        // Wait for scale animation to mostly finish (1.2s CSS anim),
        // then add a rightward offset so it looks centered,
        // then on the next frame remove it — triggering the CSS transition slide
        setTimeout(() => {
            // Measure how wide the text will be once visible
            // Use a rough offset — half the orion text width
            const offset = orionText.offsetWidth > 0
                ? Math.round(orionText.offsetWidth / 2)
                : 160; // fallback ~160px

            // Jump symbol to offset (no transition) so it's screen-center
            powerSymbol.style.transition = 'none';
            powerSymbol.style.transform  = `translateX(${offset}px)`;

            // Next frame: restore transition and slide back to 0 (leftward)
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    powerSymbol.style.transition = 'transform 0.85s cubic-bezier(0.4, 0, 0.2, 1), filter 0.3s ease';
                    powerSymbol.style.transform  = 'translateX(0)';
                });
            });

        }, 1400); // after scale animation

        // Phase 3: reveal RION text mid-slide (300ms into the slide)
        setTimeout(() => {
            orionText.classList.add('visible');
        }, 1700);
    }

    // Step 2 — dismiss intro on scroll, click, or keydown
    let introGone = false;

    const dismissIntro = () => {
        if (introGone) return;
        introGone = true;

        if (introLayer) {
            introLayer.style.opacity    = '0';
            introLayer.style.visibility = 'hidden';
        }

        setTimeout(() => {
            if (introLayer) introLayer.style.display = 'none';
            if (mainApp) {
                mainApp.style.visibility = 'visible';
                mainApp.style.opacity    = '1';
                mainApp.style.transition = 'opacity 0.9s ease';
            }
        }, 1000);
    };

    // Only allow dismiss after the logo animation plays (~3.2s)
    setTimeout(() => {
        window.addEventListener('scroll',  () => { if (window.scrollY > 5) dismissIntro(); }, { passive: true });
        introLayer && introLayer.addEventListener('click', dismissIntro);
        window.addEventListener('keydown', dismissIntro);
    }, 3200);

    // ============================================================
    // 3. SCROLL-BASED SECTION REVEAL
    //    Sections are hidden by default, appear as user scrolls
    // ============================================================

    const revealSections = document.querySelectorAll(
        '.objective-section, .upload-section, .processing-section'
    );

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(e => {
            if (e.isIntersecting) e.target.classList.add('visible');
        });
    }, { threshold: 0.08 });

    revealSections.forEach(s => revealObserver.observe(s));

    // ============================================================
    // 4. RESULTS HIDDEN UNTIL UPLOAD
    //    Processing section and all result tables are hidden
    //    until the user actually uploads and gets a response
    // ============================================================

    const processingSection = document.querySelector('.processing-section');
    const equipmentSection  = document.getElementById('equipment-section');
    const variablesSection  = document.getElementById('variables-section');
    const unifiedSection    = document.getElementById('unified-section');
    const pseudocodeSection = document.getElementById('pseudocode-section');
    const workflowActions   = document.getElementById('workflow-actions');

    // Hide the entire processing section initially
    if (processingSection) {
        processingSection.style.display = 'none';
    }

    // ============================================================
    // 5. JOURNEY TIMELINE HELPER
    // ============================================================

    const nodes = document.querySelectorAll('.node');

    function setActiveStep(stepNumber) {
        nodes.forEach(node => {
            const s = parseInt(node.dataset.step);
            node.classList.remove('active', 'completed');
            if (s === stepNumber) node.classList.add('active');
            if (s < stepNumber)   node.classList.add('completed');
        });
    }

    // ============================================================
    // 6. START ANALYSIS — PDF upload & API call
    // ============================================================

    const startBtn  = document.getElementById('startBtn');
    const fileInput = document.getElementById('input-pdf');

    const equipmentTbody    = document.getElementById('equipment-tbody');
    const variablesTbody    = document.getElementById('variables-tbody');
    const unifiedTbody      = document.getElementById('unified-tbody');
    const pseudocodeDisplay = document.getElementById('pseudocode-display');

    if (startBtn) {
        startBtn.addEventListener('click', async () => {
            if (!fileInput || fileInput.files.length === 0) {
                alert('Please upload a PDF file first.');
                return;
            }

            // Show the processing section for the first time
            if (processingSection) {
                processingSection.style.display = 'block';
                // Smooth scroll to it
                setTimeout(() => {
                    processingSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 100);
            }

            // Reset all result panels
            if (equipmentSection)  equipmentSection.style.display  = 'none';
            if (variablesSection)  variablesSection.style.display  = 'none';
            if (unifiedSection)    unifiedSection.style.display    = 'none';
            if (pseudocodeSection) pseudocodeSection.style.display = 'none';
            if (workflowActions)   workflowActions.style.display   = 'none';
            if (equipmentTbody)    equipmentTbody.innerHTML  = '';
            if (variablesTbody)    variablesTbody.innerHTML  = '';
            if (unifiedTbody)      unifiedTbody.innerHTML    = '';
            if (pseudocodeDisplay) pseudocodeDisplay.textContent = '';

            setActiveStep(1);

            startBtn.textContent = 'Processing…';
            startBtn.disabled    = true;

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
                if (equipmentSection) {
                    equipmentSection.style.display = 'block';
                    renderEquipment(data.equipment || []);
                }

                // ---- Step 2: Variables (Logic Extraction) ----
                await delay(700);
                setActiveStep(2);
                if (variablesSection) {
                    variablesSection.style.display = 'block';
                    renderVariables(data.variables || []);
                }

                // ---- Step 3: Unified Control Table ----
                await delay(700);
                setActiveStep(3);
                if (unifiedSection) {
                    unifiedSection.style.display = 'block';
                    renderUnified(data.unified_control_table || []);
                }

                // ---- Step 4: Pseudocode ----
                await delay(700);
                setActiveStep(4);
                if (pseudocodeSection && pseudocodeDisplay) {
                    pseudocodeSection.style.display = 'block';
                    const code = data.pseudocode || JSON.stringify(data.unified_control_table || [], null, 2);
                    typeWriter(code, pseudocodeDisplay);
                }

                // Show action buttons
                await delay(900);
                if (workflowActions) workflowActions.style.display = 'flex';

            } catch (error) {
                console.error(error);
                alert('Error processing document: ' + error.message);
                // Hide processing section again on error
                if (processingSection) processingSection.style.display = 'none';
            } finally {
                startBtn.textContent = 'Start Analysis';
                startBtn.disabled    = false;
            }
        });
    }

    // ============================================================
    // 7. RENDER HELPERS
    // ============================================================

    function renderEquipment(equipment) {
        if (!equipmentTbody) return;
        equipmentTbody.innerHTML = '';
        if (equipment.length === 0) {
            equipmentTbody.innerHTML = '<tr><td colspan="3" style="opacity:0.35;text-align:center;padding:20px;">No equipment data found.</td></tr>';
            return;
        }
        equipment.forEach((item, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="color:var(--green);font-family:'Fira Code',monospace;font-size:0.8rem;">${item.id || ('EQP-' + String(i+1).padStart(2,'0'))}</td>
                    <td>${item.name || item.condition || ''}</td>
                    <td style="color:var(--white-70);">${item.description || item.value || ''}</td>
                `;
                equipmentTbody.appendChild(tr);
            }, i * 100);
        });
    }

    function renderVariables(variables) {
        if (!variablesTbody) return;
        variablesTbody.innerHTML = '';
        if (variables.length === 0) {
            variablesTbody.innerHTML = '<tr><td colspan="3" style="opacity:0.35;text-align:center;padding:20px;">No variables found.</td></tr>';
            return;
        }
        variables.forEach((item, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="color:var(--green);font-family:'Fira Code',monospace;font-size:0.8rem;">${item.id || ('VAR-' + String(i+1).padStart(2,'0'))}</td>
                    <td>${item.name || ''}</td>
                    <td style="color:var(--white-70);">${item.value || item.range || ''}</td>
                `;
                variablesTbody.appendChild(tr);
            }, i * 100);
        });
    }

    function renderUnified(rows) {
        if (!unifiedTbody) return;
        unifiedTbody.innerHTML = '';
        if (rows.length === 0) {
            unifiedTbody.innerHTML = '<tr><td colspan="5" style="opacity:0.35;text-align:center;padding:20px;">No unified control data generated.</td></tr>';
            return;
        }
        rows.forEach((row, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.equipment || ''}</td>
                    <td>${row.variable  || ''}</td>
                    <td>${row.parameter || ''}</td>
                    <td>${row.condition || ''}</td>
                    <td>${row.action    || ''}</td>
                `;
                unifiedTbody.appendChild(tr);
            }, i * 120);
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
    // 8. WORKFLOW BUTTONS
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