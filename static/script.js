document.addEventListener('DOMContentLoaded', () => {

    // ============================================================
    // 1. ATMOSPHERE
    // ============================================================
    const gridOverlay = document.createElement('div');
    gridOverlay.className = 'grid-overlay';
    document.body.prepend(gridOverlay);

    // ============================================================
    // 2. INTRO — pure CSS animation, JS only handles dismiss
    // ============================================================
    const introLayer = document.querySelector('.intro-layer');
    const mainApp    = document.querySelector('.main-app');

    if (mainApp) {
        mainApp.style.opacity    = '0';
        mainApp.style.visibility = 'hidden';
    }

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

    // Allow dismiss after animations complete (~3.5s)
    setTimeout(() => {
        window.addEventListener('scroll', () => { if (window.scrollY > 5) dismissIntro(); }, { passive: true });
        introLayer && introLayer.addEventListener('click', dismissIntro);
        window.addEventListener('keydown', dismissIntro);
    }, 3500);

    // ============================================================
    // 3. SCROLL REVEAL
    // ============================================================
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
    }, { threshold: 0.08 });

    document.querySelectorAll('.objective-section, .upload-section, .processing-section')
        .forEach(s => revealObserver.observe(s));

    // ============================================================
    // 4. STEP SYSTEM
    //    Steps: 1=Processing, 2=Extraction (5 tables), 3=Unified, 4=Pseudocode
    // ============================================================
    const TOTAL_STEPS = 4;
    let currentStep   = 1;
    let maxUnlocked   = 1; // steps unlock as data arrives

    const nodes        = document.querySelectorAll('.node');
    const stepPanels   = document.querySelectorAll('.step-panel');
    const prevBtn      = document.getElementById('prevStep');
    const nextBtn      = document.getElementById('nextStep');
    const stepLabel    = document.getElementById('stepLabel');
    const timelineFill = document.getElementById('timeline-fill');

    // Make goToStep globally accessible (used in onclick attributes in HTML)
    window.goToStep = function(step) {
        if (step < 1 || step > TOTAL_STEPS) return;
        if (step > maxUnlocked) return; // can't jump ahead of unlocked steps
        currentStep = step;
        renderStep();
    };

    window.changeStep = function(dir) {
        const target = currentStep + dir;
        if (target < 1 || target > maxUnlocked) return;
        currentStep = target;
        renderStep();
    };

    function renderStep() {
        // Panels
        stepPanels.forEach(p => p.classList.remove('active'));
        const panel = document.getElementById('step-' + currentStep);
        if (panel) panel.classList.add('active');

        // Timeline nodes
        nodes.forEach(n => {
            const s = parseInt(n.dataset.step);
            n.classList.remove('active', 'completed');
            if (s === currentStep) n.classList.add('active');
            if (s < currentStep)  n.classList.add('completed');
        });

        // Timeline fill — fill between first and current node
        const pct = ((currentStep - 1) / (TOTAL_STEPS - 1)) * 100;
        if (timelineFill) timelineFill.style.width = pct + '%';

        // Step label
        if (stepLabel) stepLabel.textContent = `Step ${currentStep} of ${maxUnlocked}`;

        // Arrow buttons
        if (prevBtn) prevBtn.disabled = currentStep === 1;
        if (nextBtn) nextBtn.disabled = currentStep === maxUnlocked;
    }

    function unlockStep(step) {
        if (step > maxUnlocked) {
            maxUnlocked = step;
            // Update nodes — unlock up to this step
            nodes.forEach(n => {
                const s = parseInt(n.dataset.step);
                if (s <= maxUnlocked) {
                    n.style.opacity  = '1';
                    n.style.pointerEvents = 'auto';
                }
            });
        }
        renderStep();
    }

    // Lock future nodes visually at start
    nodes.forEach(n => {
        const s = parseInt(n.dataset.step);
        if (s > 1) {
            n.style.opacity = '0.3';
            n.style.pointerEvents = 'none';
        }
    });

    renderStep();

    // ============================================================
    // 5. START ANALYSIS
    // ============================================================
    const startBtn  = document.getElementById('startBtn');
    const fileInput = document.getElementById('input-pdf');
    const resultsSection = document.getElementById('results-section');

    if (startBtn) {
        startBtn.addEventListener('click', async () => {
            if (!fileInput || fileInput.files.length === 0) {
                alert('Please upload a PDF file first.');
                return;
            }

            // Reset to step 1
            currentStep  = 1;
            maxUnlocked  = 1;
            nodes.forEach(n => {
                const s = parseInt(n.dataset.step);
                if (s > 1) { n.style.opacity = '0.3'; n.style.pointerEvents = 'none'; }
            });

            // Clear all tables
            ['tb-equipment','tb-variables','tb-parameters','tb-conditions','tb-actions','tb-unified']
                .forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = ''; });
            const pd = document.getElementById('pseudocode-display');
            if (pd) pd.textContent = '';

            // Reset status dots
            document.querySelectorAll('.status-item').forEach(el => {
                el.classList.remove('done', 'running');
            });

            // Show results section
            if (resultsSection) {
                resultsSection.style.display = 'block';
                setTimeout(() => resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' }), 120);
            }

            renderStep();

            startBtn.textContent = 'Processing…';
            startBtn.disabled    = true;

            // Animate status items sequentially
            const statusItems = document.querySelectorAll('.status-item');
            for (let i = 0; i < statusItems.length; i++) {
                statusItems[i].classList.add('running');
                await delay(500);
                statusItems[i].classList.remove('running');
                statusItems[i].classList.add('done');
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            try {
                const response = await fetch('http://localhost:8000/api/process_document', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('API Error: ' + response.statusText);

                const data = await response.json();

                // Populate all 5 extraction tables
                fillEquipment(data.equipment   || []);
                fillVariables(data.variables   || []);
                fillParameters(data.parameters || []);
                fillConditions(data.conditions || []);
                fillActions(data.actions       || []);

                // Populate unified table
                fillUnified(data.unified_control_table || buildUnified(data));

                // Populate pseudocode
                const code = data.pseudocode || JSON.stringify(data.unified_control_table || [], null, 2);
                const pdEl = document.getElementById('pseudocode-display');
                if (pdEl) typeWriter(code, pdEl);

                // Feed full context to the AI chatbot
                if (window.orionChatSetDocData) {
                    window.orionChatSetDocData(data, data.raw_text || '');
                }

                // Unlock all steps
                unlockStep(2);
                unlockStep(3);
                unlockStep(4);

                // Auto-advance to step 2
                await delay(400);
                currentStep = 2;
                renderStep();

            } catch (error) {
                console.error(error);
                alert('Error processing document: ' + error.message);
                if (resultsSection) resultsSection.style.display = 'none';
            } finally {
                startBtn.textContent = 'Start Analysis';
                startBtn.disabled    = false;
            }
        });
    }

    // ============================================================
    // 6. TABLE FILLERS
    // ============================================================

    function fillEquipment(arr) {
        const tbody = document.getElementById('tb-equipment');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (!arr.length) { emptyRow(tbody, 4); return; }
        arr.forEach((item, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${i + 1}</td>
                    <td style="font-family:'Fira Code',monospace;font-size:0.8rem;color:var(--green)">${item.id || 'EQP-' + pad(i+1)}</td>
                    <td>${item.name || ''}</td>
                    <td style="color:var(--white-70)">${item.description || ''}</td>`;
                tbody.appendChild(tr);
            }, i * 80);
        });
    }

    function fillVariables(arr) {
        const tbody = document.getElementById('tb-variables');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (!arr.length) { emptyRow(tbody, 4); return; }
        arr.forEach((item, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${i + 1}</td>
                    <td style="font-family:'Fira Code',monospace;font-size:0.8rem;color:#7fc8ff">${item.id || 'VAR-' + pad(i+1)}</td>
                    <td>${item.name || ''}</td>
                    <td style="color:var(--white-70)">${item.value || item.range || ''}</td>`;
                tbody.appendChild(tr);
            }, i * 80);
        });
    }

    function fillParameters(arr) {
        const tbody = document.getElementById('tb-parameters');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (!arr.length) { emptyRow(tbody, 4); return; }
        arr.forEach((item, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${i + 1}</td>
                    <td style="font-family:'Fira Code',monospace;font-size:0.8rem;color:#ffd580">${item.id || 'PAR-' + pad(i+1)}</td>
                    <td>${item.name || ''}</td>
                    <td style="color:var(--white-70)">${item.value || ''}</td>`;
                tbody.appendChild(tr);
            }, i * 80);
        });
    }

    function fillConditions(arr) {
        const tbody = document.getElementById('tb-conditions');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (!arr.length) { emptyRow(tbody, 4); return; }
        arr.forEach((item, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${i + 1}</td>
                    <td style="font-family:'Fira Code',monospace;font-size:0.8rem;color:#d4a0ff">${item.id || 'CON-' + pad(i+1)}</td>
                    <td>${item.condition || item.name || ''}</td>
                    <td style="color:var(--white-70)">${item.threshold || item.value || ''}</td>`;
                tbody.appendChild(tr);
            }, i * 80);
        });
    }

    function fillActions(arr) {
        const tbody = document.getElementById('tb-actions');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (!arr.length) { emptyRow(tbody, 4); return; }
        arr.forEach((item, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${i + 1}</td>
                    <td style="font-family:'Fira Code',monospace;font-size:0.8rem;color:#ff9090">${item.id || 'ACT-' + pad(i+1)}</td>
                    <td>${item.action || item.name || ''}</td>
                    <td style="color:var(--white-70)">${item.trigger || ''}</td>`;
                tbody.appendChild(tr);
            }, i * 80);
        });
    }

    function fillUnified(rows) {
        const tbody = document.getElementById('tb-unified');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (!rows.length) { emptyRow(tbody, 6); return; }
        rows.forEach((row, i) => {
            setTimeout(() => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${i + 1}</td>
                    <td>${row.equipment  || ''}</td>
                    <td>${row.variable   || ''}</td>
                    <td>${row.parameter  || ''}</td>
                    <td>${row.condition  || ''}</td>
                    <td>${row.action     || ''}</td>`;
                tbody.appendChild(tr);
            }, i * 100);
        });
    }

    // Build unified table from separate arrays if API doesn't return it
    function buildUnified(data) {
        const equipment  = data.equipment   || [];
        const variables  = data.variables   || [];
        const parameters = data.parameters  || [];
        const conditions = data.conditions  || [];
        const actions    = data.actions     || [];
        const len = Math.max(equipment.length, variables.length, parameters.length, conditions.length, actions.length);
        const rows = [];
        for (let i = 0; i < len; i++) {
            rows.push({
                equipment:  equipment[i]  ? (equipment[i].name  || equipment[i].id  || '') : '',
                variable:   variables[i]  ? (variables[i].name  || variables[i].id  || '') : '',
                parameter:  parameters[i] ? (parameters[i].name || parameters[i].id || '') : '',
                condition:  conditions[i] ? (conditions[i].condition || conditions[i].name || '') : '',
                action:     actions[i]    ? (actions[i].action  || actions[i].name  || '') : '',
            });
        }
        return rows;
    }

    // ============================================================
    // 7. UTILS
    // ============================================================

    function emptyRow(tbody, cols) {
        tbody.innerHTML = `<tr><td colspan="${cols}" style="text-align:center;opacity:0.3;padding:18px;">No data available.</td></tr>`;
    }

    function pad(n) { return String(n).padStart(2, '0'); }

    function typeWriter(text, element) {
        let i = 0;
        element.textContent = '';
        element.style.whiteSpace = 'pre-wrap';
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i++);
                setTimeout(type, 2);
            }
        }
        type();
    }

    function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

    // ============================================================
    // 8. WORKFLOW BUTTONS
    // ============================================================
    const btnExport  = document.getElementById('btn-export');
    const btnRestart = document.getElementById('btn-restart');

    if (btnExport)  btnExport.addEventListener('click',  () => alert('Export coming soon.'));
    if (btnRestart) btnRestart.addEventListener('click', () => {
        if (resultsSection) resultsSection.style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

});

// ============================================================
// ORION AI CHATBOT
// ============================================================

(function() {

    // ── State ──
    let docText        = '';   // raw extracted text from PDF (set after upload)
    let docData        = {};   // full API response (tables, pseudocode etc.)
    let chatHistory    = [];   // {role, content}[]
    let isTyping       = false;

    // ── Elements ──
    const fab          = document.getElementById('chatFab');
    const sidebar      = document.getElementById('chatSidebar');
    const messages     = document.getElementById('chatMessages');
    const input        = document.getElementById('chatInput');
    const sendBtn      = document.getElementById('chatSend');
    const clearBtn     = document.getElementById('chatClear');
    const statusEl     = document.getElementById('chatStatus');
    const unreadBadge  = document.getElementById('chatUnread');
    const openIcon     = fab  && fab.querySelector('.chat-icon-open');
    const closeIcon    = fab  && fab.querySelector('.chat-icon-close');
    const fabLabel     = fab  && fab.querySelector('.chat-fab-label');

    // ── Toggle sidebar ──
    if (fab) {
        fab.addEventListener('click', () => {
            const isOpen = sidebar.classList.toggle('open');
            if (openIcon)  openIcon.style.display  = isOpen ? 'none'  : 'block';
            if (closeIcon) closeIcon.style.display = isOpen ? 'block' : 'none';
            if (fabLabel)  fabLabel.textContent    = isOpen ? 'Close' : 'Ask AI';
            if (isOpen) {
                unreadBadge.style.display = 'none';
                input && input.focus();
            }
        });
    }

    // ── Clear chat ──
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            chatHistory = [];
            messages.innerHTML = '';
            appendMessage('assistant', 'Chat cleared. Ask me anything about the document!');
        });
    }

    // ── Send on Enter (Shift+Enter = newline) ──
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });
        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });
    }

    if (sendBtn) sendBtn.addEventListener('click', handleSend);

    // ── Quick chips ──
    window.sendChip = function(btn) {
        if (!input) return;
        input.value = btn.textContent;
        handleSend();
    };

    // ── Main send handler ──
    async function handleSend() {
        const text = input.value.trim();
        if (!text || isTyping) return;

        input.value = '';
        input.style.height = 'auto';
        appendMessage('user', text);

        await askOrionAI(text);
    }

    // ── Build system prompt with full document context ──
    function buildSystemPrompt() {
        const hasDoc = Object.keys(docData).length > 0;

        let context = `You are ORION AI, an expert assistant for industrial Control Narrative documents.
You are embedded inside the ORION web application which analyzes Control Narrative PDFs.
You have deep knowledge of process engineering, PLC/SCADA logic, instrumentation, and control systems.
Always be precise, concise, and professional.

`;

        if (!hasDoc) {
            context += `No document has been uploaded yet. Encourage the user to upload a PDF to get document-specific answers. You can still answer general control narrative / engineering questions.`;
            return context;
        }

        context += `The user has uploaded and processed a Control Narrative PDF. Here is the full extracted data:\n\n`;

        if (docData.equipment && docData.equipment.length) {
            context += `EQUIPMENT (${docData.equipment.length} items):\n`;
            docData.equipment.forEach((e, i) => {
                context += `  ${i+1}. ID: ${e.id || 'N/A'} | Name: ${e.name || 'N/A'} | Desc: ${e.description || 'N/A'}\n`;
            });
            context += '\n';
        }

        if (docData.variables && docData.variables.length) {
            context += `VARIABLES (${docData.variables.length} items):\n`;
            docData.variables.forEach((v, i) => {
                context += `  ${i+1}. ID: ${v.id || 'N/A'} | Name: ${v.name || 'N/A'} | Value: ${v.value || v.range || 'N/A'}\n`;
            });
            context += '\n';
        }

        if (docData.parameters && docData.parameters.length) {
            context += `PARAMETERS (${docData.parameters.length} items):\n`;
            docData.parameters.forEach((p, i) => {
                context += `  ${i+1}. ID: ${p.id || 'N/A'} | Name: ${p.name || 'N/A'} | Value: ${p.value || 'N/A'}\n`;
            });
            context += '\n';
        }

        if (docData.conditions && docData.conditions.length) {
            context += `CONDITIONS (${docData.conditions.length} items):\n`;
            docData.conditions.forEach((c, i) => {
                context += `  ${i+1}. ID: ${c.id || 'N/A'} | Condition: ${c.condition || c.name || 'N/A'} | Threshold: ${c.threshold || c.value || 'N/A'}\n`;
            });
            context += '\n';
        }

        if (docData.actions && docData.actions.length) {
            context += `ACTIONS (${docData.actions.length} items):\n`;
            docData.actions.forEach((a, i) => {
                context += `  ${i+1}. ID: ${a.id || 'N/A'} | Action: ${a.action || a.name || 'N/A'} | Trigger: ${a.trigger || 'N/A'}\n`;
            });
            context += '\n';
        }

        if (docData.unified_control_table && docData.unified_control_table.length) {
            context += `UNIFIED CONTROL TABLE (${docData.unified_control_table.length} rows):\n`;
            docData.unified_control_table.forEach((r, i) => {
                context += `  Row ${i+1}: Equipment="${r.equipment||''}" | Variable="${r.variable||''}" | Parameter="${r.parameter||''}" | Condition="${r.condition||''}" | Action="${r.action||''}"\n`;
            });
            context += '\n';
        }

        if (docData.pseudocode) {
            context += `PSEUDOCODE:\n${docData.pseudocode}\n\n`;
        }

        if (docText) {
            // Include first 4000 chars of raw doc text for reference questions
            const snippet = docText.slice(0, 4000);
            context += `RAW DOCUMENT TEXT (excerpt):\n${snippet}\n\n`;
        }

        context += `
SPECIAL INSTRUCTION — HIGHLIGHTING:
If the user asks to "show", "highlight", "find in doc", "where in the document", or similar, 
AND you can identify the relevant passage from the raw document text above,
respond normally but at the very end of your response include a special JSON block like this (and nothing after it):

<<<HIGHLIGHT>>>
{
  "passages": ["exact phrase from document 1", "exact phrase from document 2"],
  "summary": "Brief label for what is being highlighted"
}
<<<END_HIGHLIGHT>>>

Only include this block when the user explicitly asks to see something in the document.
`;

        return context;
    }

    // ── Call Anthropic API ──
    async function askOrionAI(userMessage) {
        isTyping = true;
        sendBtn && (sendBtn.disabled = true);

        // Add to history
        chatHistory.push({ role: 'user', content: userMessage });

        // Show typing indicator
        const typingEl = showTyping();

        try {
            const systemPrompt = buildSystemPrompt();

            const response = await fetch('https://api.anthropic.com/v1/messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: 'claude-sonnet-4-20250514',
                    max_tokens: 1000,
                    system: systemPrompt,
                    messages: chatHistory
                })
            });

            const data = await response.json();
            const rawText = data.content
                .filter(b => b.type === 'text')
                .map(b => b.text)
                .join('');

            // Parse highlight block if present
            let displayText  = rawText;
            let highlightData = null;

            const highlightMatch = rawText.match(/<<<HIGHLIGHT>>>([\s\S]*?)<<<END_HIGHLIGHT>>>/);
            if (highlightMatch) {
                displayText = rawText.replace(/<<<HIGHLIGHT>>>[\s\S]*?<<<END_HIGHLIGHT>>>/, '').trim();
                try {
                    highlightData = JSON.parse(highlightMatch[1].trim());
                } catch(e) { /* ignore parse error */ }
            }

            // Remove typing indicator
            typingEl && typingEl.remove();

            // Render response
            appendMessage('assistant', displayText, highlightData);

            // Add to history
            chatHistory.push({ role: 'assistant', content: rawText });

            // Show highlight toast if applicable
            if (highlightData) {
                showHighlightToast(highlightData);
            }

            // Show unread badge if sidebar is closed
            if (!sidebar.classList.contains('open')) {
                unreadBadge.style.display = 'flex';
            }

        } catch (err) {
            typingEl && typingEl.remove();
            appendMessage('assistant', 'Sorry, I ran into an error. Please check your connection and try again.');
            console.error('ORION AI error:', err);
        } finally {
            isTyping = false;
            sendBtn && (sendBtn.disabled = false);
        }
    }

    // ── Append a message bubble ──
    function appendMessage(role, text, highlightData) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg ${role}`;

        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';

        // Basic markdown: bold, code, newlines
        let html = text
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/`([^`]+)`/g, '<code style="background:rgba(0,209,102,0.1);padding:1px 5px;border-radius:4px;font-family:Fira Code,monospace;font-size:0.82em;">$1</code>')
            .replace(/\n/g, '<br>');

        bubble.innerHTML = html;

        // Inline highlight card
        if (highlightData) {
            const card = document.createElement('div');
            card.className = 'msg-highlight-card';
            card.innerHTML = `<span class="highlight-label">📄 Document Reference</span>${highlightData.summary || ''}`;
            bubble.appendChild(card);
        }

        msgDiv.appendChild(bubble);
        messages.appendChild(msgDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    // ── Show typing indicator ──
    function showTyping() {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-msg assistant';
        msgDiv.innerHTML = `<div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>`;
        messages.appendChild(msgDiv);
        messages.scrollTop = messages.scrollHeight;
        return msgDiv;
    }

    // ── Show document highlight toast ──
    function showHighlightToast(data) {
        const toast = document.getElementById('docHighlightToast');
        const body  = document.getElementById('toastBody');
        if (!toast || !body) return;

        // Highlight passages in toast
        let html = '';
        if (data.passages && data.passages.length) {
            data.passages.forEach(p => {
                // If raw doc text exists, find context around the passage
                if (docText) {
                    const idx = docText.toLowerCase().indexOf(p.toLowerCase());
                    if (idx !== -1) {
                        const start   = Math.max(0, idx - 80);
                        const end     = Math.min(docText.length, idx + p.length + 80);
                        const before  = docText.slice(start, idx);
                        const match   = docText.slice(idx, idx + p.length);
                        const after   = docText.slice(idx + p.length, end);
                        html += `<p style="margin-bottom:10px;">…${escHtml(before)}<mark>${escHtml(match)}</mark>${escHtml(after)}…</p>`;
                    } else {
                        html += `<p style="margin-bottom:10px;"><mark>${escHtml(p)}</mark></p>`;
                    }
                } else {
                    html += `<p style="margin-bottom:10px;"><mark>${escHtml(p)}</mark></p>`;
                }
            });
        }

        body.innerHTML = html || '<p style="opacity:0.5;">No specific passage found in document text.</p>';
        toast.style.display = 'block';

        // Position beside sidebar
        const sidebarOpen = sidebar.classList.contains('open');
        toast.style.right  = sidebarOpen ? '420px' : '32px';
        toast.style.bottom = '110px';
    }

    function escHtml(str) {
        return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    // ── Expose function for main script to update doc context ──
    window.orionChatSetDocData = function(apiData, rawText) {
        docData = apiData || {};
        docText = rawText || '';
        if (statusEl) statusEl.textContent = 'Document loaded — ask me anything';
        // Show a proactive message
        appendMessage('assistant', `Document loaded! I now have full context including **${(docData.equipment||[]).length} equipment items**, **${(docData.variables||[]).length} variables**, **${(docData.conditions||[]).length} conditions**, and more. What would you like to know?`);
        // Show unread badge
        unreadBadge.style.display = 'flex';
    };

})();