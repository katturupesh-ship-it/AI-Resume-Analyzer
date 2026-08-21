const button = document.querySelector("#analyzeButton");
const result = document.querySelector("#result");
const fileInput = document.querySelector("#resumeFile");
const fileName = document.querySelector("#fileName");
const jobDescInput = document.querySelector("#jobDescription");

let latestAnalysisData = null;

// Update file selection label
fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 0) {
        fileName.textContent = "📄 " + fileInput.files[0].name;
        fileName.style.color = "#2563eb";
        fileName.style.fontWeight = "600";
    } else {
        fileName.textContent = "No file selected";
        fileName.style.color = "#64748b";
    }
});

// Load recent scan history
async function loadHistory() {
    try {
        const response = await fetch("/history");
        const data = await response.json();
        const historyContainer = document.querySelector("#historyList");
        if (!historyContainer) return;

        if (data.success && data.history && data.history.length > 0) {
            historyContainer.innerHTML = data.history.map(item => `
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s ease;" onmouseover="this.style.transform='translateX(4px)'" onmouseout="this.style.transform='translateX(0)'">
                    <div>
                        <strong style="color: #1e293b; font-size: 0.9rem;">📄 ${item.filename}</strong>
                        <div style="font-size: 0.75rem; color: #64748b;">${item.created_at} • ${item.word_count} words</div>
                    </div>
                    <span style="font-weight: 700; font-size: 1rem; color: ${item.ats_score >= 75 ? '#10b981' : (item.ats_score >= 50 ? '#f59e0b' : '#ef4444')};">
                        ${item.ats_score}/100
                    </span>
                </div>
            `).join("");
        } else {
            historyContainer.innerHTML = `<p style="font-size: 0.85rem; color: #64748b;">No recent scans stored yet.</p>`;
        }
    } catch (e) {
        console.error("Could not fetch history:", e);
    }
}

// Download JSON
function downloadJSON() {
    if (!latestAnalysisData) return;
    const blob = new Blob([JSON.stringify(latestAnalysisData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `resume_analysis_report.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// Animate Score Counter & Circular Gauge
function animateScoreGauge(targetScore, color) {
    const gauge = document.querySelector("#gaugeProgressBar");
    const scoreNum = document.querySelector("#scoreNumberText");
    if (!gauge || !scoreNum) return;

    // Circumference: 2 * PI * r (r=65) = ~408.4
    const totalLength = 408.4;
    const offset = totalLength - (targetScore / 100) * totalLength;

    setTimeout(() => {
        gauge.style.strokeDashoffset = offset;
        gauge.style.stroke = color;
    }, 100);

    let current = 0;
    const increment = targetScore / 40;
    const timer = setInterval(() => {
        current += increment;
        if (current >= targetScore) {
            scoreNum.textContent = targetScore;
            clearInterval(timer);
        } else {
            scoreNum.textContent = Math.floor(current);
        }
    }, 25);
}

// Analyze button handler
button.addEventListener("click", async function () {
    if (fileInput.files.length === 0) {
        result.innerHTML = `
            <div class="animated-entry" style="text-align: center; padding: 20px; color: #ef4444;">
                <h3>No File Selected</h3>
                <p>Please select a PDF or Image resume to analyze.</p>
            </div>
        `;
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("resume", file);
    formData.append("job_description", jobDescInput ? jobDescInput.value : "");

    button.disabled = true;
    button.textContent = "Analyzing Pipeline...";

    // Scanner animation during loading
    result.innerHTML = `
        <div class="loading-box animated-entry">
            <div class="scanner-beam"></div>
            <div class="pulse-circle">⚡</div>
            <h3 style="color: #0f172a; margin-bottom: 6px; font-weight: 700;">Evaluating Resume Intelligence</h3>
            <p style="color: #64748b; font-size: 0.9rem; max-width: 480px; margin: 0 auto;">Transcribing document layers, running weighted ATS algorithms, and querying Google Gemini 3.6...</p>
        </div>
    `;

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            body: formData
        });
        const data = await response.json();

        if (data.success) {
            latestAnalysisData = data;
            const ats = data.ats || { total_score: 0, breakdown: {}, word_count: 0 };
            const b = ats.breakdown;
            const score = ats.total_score;
            const scoreColor = score >= 75 ? "#10b981" : (score >= 50 ? "#f59e0b" : "#ef4444");

            // 1. Technical Skills Badges
            const skillsHTML = (data.skills && data.skills.length > 0)
                ? data.skills.map(s => `<span class="skill-badge">${s}</span>`).join("")
                : `<span style="color: #64748b; font-size: 0.9rem;">No recognized technical skills found.</span>`;

            // 2. Sections Status Badges
            const sectionsHTML = data.sections
                ? Object.entries(data.sections).map(([s, found]) => `
                    <span style="display: inline-flex; align-items: center; gap: 4px; background: ${found ? '#ecfdf5' : '#fef2f2'}; color: ${found ? '#065f46' : '#991b1b'}; border: 1px solid ${found ? '#a7f3d0' : '#fecaca'}; padding: 5px 12px; margin: 3px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        ${found ? '✓' : '✗'} ${s}
                    </span>`).join("")
                : "";

            // 3. AI Insights Block
            let aiHTML = "";
            if (data.ai_insights && data.ai_insights.summary) {
                const ai = data.ai_insights;
                const recsHTML = (ai.recommendations && ai.recommendations.length > 0)
                    ? ai.recommendations.map(r => `<li style="margin-bottom: 8px; font-size: 0.92rem; color: #1e293b;">• ${r}</li>`).join("")
                    : "";

                aiHTML = `
                    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1px solid #bae6fd; border-radius: 12px; padding: 24px; margin-bottom: 24px; text-align: left; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.06);">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                            <span style="font-size: 1.3rem;">🤖</span>
                            <h4 style="margin: 0; color: #0369a1; font-size: 1.05rem; font-weight: 700;">Gemini AI Executive Feedback</h4>
                        </div>
                        <p style="font-size: 0.92rem; color: #334155; line-height: 1.65; margin-bottom: ${recsHTML ? '16px' : '0'};">
                            ${ai.summary}
                        </p>
                        ${recsHTML ? `
                            <div style="font-size: 0.82rem; font-weight: 700; color: #0284c7; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em;">Strategic Recommendations:</div>
                            <ul style="list-style: none; padding: 0; margin: 0;">
                                ${recsHTML}
                            </ul>
                        ` : ''}
                    </div>
                `;
            }

            // 4. Job Description Match Block
            let jdHTML = "";
            if (data.jd_match && data.jd_match.has_jd) {
                const match = data.jd_match;
                const matchColor = match.match_percentage >= 70 ? "#10b981" : (match.match_percentage >= 40 ? "#f59e0b" : "#ef4444");

                const matchedBadges = match.matched_skills.map(s => `
                    <span style="background: #dcfce7; color: #15803d; padding: 4px 12px; margin: 2px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">✓ ${s}</span>
                `).join("") || `<span style="color: #64748b; font-size: 0.85rem;">None</span>`;

                const missingBadges = match.missing_skills.map(s => `
                    <span style="background: #fee2e2; color: #b91c1c; padding: 4px 12px; margin: 2px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">✗ ${s}</span>
                `).join("") || `<span style="color: #64748b; font-size: 0.85rem;">None</span>`;

                jdHTML = `
                    <div style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 12px; padding: 22px; margin-bottom: 24px; box-shadow: var(--shadow-sm); text-align: left;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <h4 style="margin: 0; color: #1e293b; font-weight: 700;">Job Description Alignment</h4>
                            <span style="font-size: 1.35rem; font-weight: 800; color: ${matchColor};">${match.match_percentage}% Match</span>
                        </div>
                        <p style="font-size: 0.88rem; color: #64748b; margin-bottom: 16px;">${match.message}</p>
                        
                        <div style="margin-bottom: 12px;">
                            <div style="font-size: 0.8rem; font-weight: 700; color: #475569; margin-bottom: 6px; text-transform: uppercase;">Matched Keywords:</div>
                            <div>${matchedBadges}</div>
                        </div>

                        <div>
                            <div style="font-size: 0.8rem; font-weight: 700; color: #475569; margin-bottom: 6px; text-transform: uppercase;">Missing Target Keywords:</div>
                            <div>${missingBadges}</div>
                        </div>
                    </div>
                `;
            }

            // 5. Suggestions
            const suggestionsHTML = (data.suggestions && data.suggestions.length > 0)
                ? data.suggestions.map(s => `
                    <li style="display: flex; gap: 10px; margin-bottom: 10px; font-size: 0.92rem; color: #334155;">
                        <span style="color: #3b82f6; font-weight: 700;">•</span>
                        <span>${s}</span>
                    </li>
                `).join("")
                : `<p style="font-size: 0.9rem; color: #10b981;">No structural improvements needed!</p>`;

            // 6. Strengths & Gaps
            const strengthsHTML = (data.strengths || []).map(s => `<li style="margin-bottom: 6px; font-size: 0.85rem; color: #065f46;">✓ ${s}</li>`).join("");
            const weaknessesHTML = (data.weaknesses || []).map(w => `<li style="margin-bottom: 6px; font-size: 0.85rem; color: #991b1b;">⚠ ${w}</li>`).join("");

            // Render Result Card
            result.innerHTML = `
                <div class="animated-entry">
                    <!-- Export & Print Actions -->
                    <div class="no-print" style="display: flex; justify-content: flex-end; gap: 10px; margin-bottom: 20px;">
                        <button onclick="downloadJSON()" style="background: #ffffff; border: 1px solid #cbd5e1; padding: 8px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; color: #334155; transition: var(--transition);" onmouseover="this.style.background='#f1f5f9'" onmouseout="this.style.background='#ffffff'">
                            📥 Download JSON
                        </button>
                        <button onclick="window.print()" style="background: var(--primary); color: #ffffff; border: none; padding: 8px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: var(--transition);" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                            🖨️ Print / Save PDF
                        </button>
                    </div>

                    <!-- Circular Progress Overall ATS Score -->
                    <div style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 14px; padding: 28px; text-align: center; margin-bottom: 24px; box-shadow: var(--shadow-sm);">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Overall ATS Score</div>

                        <!-- Animated SVG Gauge -->
                        <div class="score-gauge-container">
                            <svg class="score-gauge-svg" viewBox="0 0 150 150">
                                <circle class="gauge-bg" cx="75" cy="75" r="65"></circle>
                                <circle id="gaugeProgressBar" class="gauge-progress" cx="75" cy="75" r="65"></circle>
                            </svg>
                            <div class="score-text-overlay">
                                <div id="scoreNumberText" class="score-number" style="color: ${scoreColor};">0</div>
                                <div style="font-size: 0.8rem; font-weight: 600; color: #94a3b8;">/ 100</div>
                            </div>
                        </div>

                        <!-- Breakdown Grid -->
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; margin-top: 24px;">
                            <div style="background: #f8fafc; padding: 12px 10px; border-radius: 10px; border: 1px solid #e2e8f0; transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                <div style="font-size: 0.75rem; color: #64748b;">Skills</div>
                                <strong style="color: #1e293b; font-size: 0.95rem;">${b.skills} / 25</strong>
                            </div>
                            <div style="background: #f8fafc; padding: 12px 10px; border-radius: 10px; border: 1px solid #e2e8f0; transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                <div style="font-size: 0.75rem; color: #64748b;">Experience</div>
                                <strong style="color: #1e293b; font-size: 0.95rem;">${b.experience} / 20</strong>
                            </div>
                            <div style="background: #f8fafc; padding: 12px 10px; border-radius: 10px; border: 1px solid #e2e8f0; transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                <div style="font-size: 0.75rem; color: #64748b;">Education</div>
                                <strong style="color: #1e293b; font-size: 0.95rem;">${b.education} / 15</strong>
                            </div>
                            <div style="background: #f8fafc; padding: 12px 10px; border-radius: 10px; border: 1px solid #e2e8f0; transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                <div style="font-size: 0.75rem; color: #64748b;">Projects</div>
                                <strong style="color: #1e293b; font-size: 0.95rem;">${b.projects} / 15</strong>
                            </div>
                            <div style="background: #f8fafc; padding: 12px 10px; border-radius: 10px; border: 1px solid #e2e8f0; transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                <div style="font-size: 0.75rem; color: #64748b;">Extra Sections</div>
                                <strong style="color: #1e293b; font-size: 0.95rem;">${b.supplementary} / 15</strong>
                            </div>
                            <div style="background: #f8fafc; padding: 12px 10px; border-radius: 10px; border: 1px solid #e2e8f0; transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                <div style="font-size: 0.75rem; color: #64748b;">Format</div>
                                <strong style="color: #1e293b; font-size: 0.95rem;">${b.formatting} / 10</strong>
                            </div>
                        </div>
                    </div>

                    <!-- AI Insights -->
                    ${aiHTML}

                    <!-- JD Match -->
                    ${jdHTML}

                    <!-- Actionable Recommendations -->
                    <div style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 12px; padding: 22px; margin-bottom: 24px; box-shadow: var(--shadow-sm); text-align: left;">
                        <h4 style="margin: 0 0 14px; color: #1e293b; font-weight: 700;">💡 Actionable Recommendations</h4>
                        <ul style="list-style: none; padding: 0; margin: 0;">
                            ${suggestionsHTML}
                        </ul>
                    </div>

                    <!-- Strengths & Gaps -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 24px; text-align: left;">
                        <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 12px; padding: 20px;">
                            <h4 style="margin: 0 0 10px; color: #065f46; font-weight: 700;">Resume Strengths</h4>
                            <ul style="margin: 0; padding-left: 18px;">
                                ${strengthsHTML || "<li style='font-size: 0.85rem;'>None detected.</li>"}
                            </ul>
                        </div>
                        <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 20px;">
                            <h4 style="margin: 0 0 10px; color: #991b1b; font-weight: 700;">Structural Gaps</h4>
                            <ul style="margin: 0; padding-left: 18px;">
                                ${weaknessesHTML || "<li style='font-size: 0.85rem;'>None detected!</li>"}
                            </ul>
                        </div>
                    </div>

                    <!-- Detected Technical Skills & Section Status -->
                    <div style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 12px; padding: 22px; margin-bottom: 24px; box-shadow: var(--shadow-sm); text-align: left;">
                        <h4 style="margin: 0 0 10px; color: #1e293b; font-weight: 700;">Detected Technical Skills (${data.skills.length})</h4>
                        <div style="margin-bottom: 20px;">${skillsHTML}</div>

                        <h4 style="margin: 0 0 10px; color: #1e293b; font-weight: 700;">Section Detection Status</h4>
                        <div>${sectionsHTML}</div>
                    </div>

                    <!-- Clean Extracted Text Preview -->
                    <details class="no-print" style="background: #f8fafc; border: 1px solid var(--border-color); border-radius: 10px; padding: 14px; text-align: left;">
                        <summary style="font-size: 0.85rem; font-weight: 600; color: #64748b; cursor: pointer;">
                            View Extracted Clean Text (${ats.word_count} words)
                        </summary>
                        <pre style="white-space: pre-wrap; background: #ffffff; padding: 14px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 0.8rem; max-height: 250px; overflow-y: auto; margin-top: 10px; color: #334155;">${data.text}</pre>
                    </details>
                </div>
            `;

            // Trigger the animated score counter and circular gauge
            animateScoreGauge(score, scoreColor);

            // Refresh recent scan history
            loadHistory();
        } else {
            result.innerHTML = `
                <div class="animated-entry" style="text-align: center; padding: 20px; color: #ef4444;">
                    <h3>Analysis Failed</h3>
                    <p>${data.message}</p>
                </div>
            `;
        }
    } catch (error) {
        result.innerHTML = `
            <div class="animated-entry" style="text-align: center; padding: 20px; color: #ef4444;">
                <h3>Server Error</h3>
                <p>Could not connect to the Flask server.</p>
            </div>
        `;
        console.error("Error:", error);
    }

    button.disabled = false;
    button.textContent = "Analyze Resume";
});

// Load scan history when page loads
loadHistory();