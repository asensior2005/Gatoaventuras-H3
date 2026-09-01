
function getMyCustomWorlds() {
    try {
        return JSON.parse(localStorage.getItem("cat_my_custom_worlds") || "[]");
    } catch (e) {
        return [];
    }
}

function saveCustomWorldLocal(universe) {
    const list = getMyCustomWorlds();
    list.unshift(universe);
    localStorage.setItem("cat_my_custom_worlds", JSON.stringify(list));
}

function deleteCustomWorldLocal(uid, e) {
    if (e) e.stopPropagation();
    if (!confirm("¿Quieres eliminar este mundo personalizado?")) return;
    const list = getMyCustomWorlds().filter(u => u.id !== uid);
    localStorage.setItem("cat_my_custom_worlds", JSON.stringify(list));
    renderMyCustomWorlds();
    showStatus("🗑️", "Mundo personalizado eliminado.");
}

function renderMyCustomWorlds() {
    const section = getEl("myCustomWorldsSection");
    const grid = getEl("myCustomWorldsGrid");
    if (!section || !grid) return;

    const list = getMyCustomWorlds();
    if (list.length === 0) {
        section.style.display = "none";
        grid.innerHTML = "";
        return;
    }

    section.style.display = "flex";
    grid.innerHTML = "";
    list.forEach(u => {
        const card = document.createElement("div");
        card.className = "pastel-card";
        card.innerHTML = `
            <div class="pastel-card-top-3d">
                <button class="btn-delete-custom-world" onclick="deleteCustomWorldLocal('${u.id}', event)" title="Eliminar mundo">✕</button>
                <img src="${u.image_3d || '/static/icon_scratchers_3d.jpg'}" alt="${u.title}" class="world-image-3d">
                <span class="world-badge-3d-icon">${u.icon || '✨'}</span>
            </div>
            <div class="pastel-card-body">
                <span class="world-subtitle">🌟 Creado por ti</span>
                <h3 class="world-title">${u.title}</h3>
                <p class="world-desc">${u.description}</p>
                <button class="btn-enter-cute">🐾 ¡JUGAR ESTA AVENTURA!</button>
            </div>
        `;
        card.onmouseenter = () => playSFX('hover');
        card.onclick = () => {
            playSFX('click');
            selectUniverse(u);
        };
        grid.appendChild(card);
    });
}
window.state = {
    currentUniverse: null,
    currentMood: "golden_hour",
    history: [],
    isGenerating: false,
    timerInterval: null,
    soundEnabled: true,
    audioInitialized: false,
    tokensLeft: 5,
    isJuror: false,
    jurorCode: localStorage.getItem("cat_juror_code") || null
};

function getEl(id) {
    return document.getElementById(id);
}

// ----------------------------------------------------
// 1. Playful Kawaii Web Audio SFX
// ----------------------------------------------------
let audioCtx = null;
function getAudioContext() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioCtx;
}

window.enableAudioOnUserGesture = function() {
    if (!window.state.audioInitialized) {
        window.state.audioInitialized = true;
        try {
            const ctx = getAudioContext();
            if (ctx.state === 'suspended') ctx.resume();
        } catch(e) {}
    }
};

window.unmuteVideo = function() {
    const video = getEl("mainVideo");
    const banner = getEl("unmuteBanner");
    if (video) {
        video.muted = false;
        video.play().catch(e => console.log(e));
    }
    if (banner) banner.classList.add("hidden");
};

function playSFX(type) {
    if (!window.state.soundEnabled) return;
    try {
        const ctx = getAudioContext();
        if (ctx.state === 'suspended') ctx.resume();
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        if (type === 'hover') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(523.25, now);
            osc.frequency.exponentialRampToValueAtTime(1046.50, now + 0.05);
            gain.gain.setValueAtTime(0.05, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
            osc.start(now);
            osc.stop(now + 0.05);
        } else if (type === 'click') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(659.25, now);
            osc.frequency.exponentialRampToValueAtTime(1318.51, now + 0.09);
            gain.gain.setValueAtTime(0.09, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);
            osc.start(now);
            osc.stop(now + 0.09);
        } else if (type === 'success') {
            [523.25, 659.25, 783.99, 1046.50, 1318.51].forEach((freq, i) => {
                const o = ctx.createOscillator();
                const g = ctx.createGain();
                o.connect(g);
                g.connect(ctx.destination);
                o.type = 'triangle';
                o.frequency.setValueAtTime(freq, now + i * 0.06);
                g.gain.setValueAtTime(0.07, now + i * 0.06);
                g.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
                o.start(now + i * 0.06);
                o.stop(now + 0.5);
            });
        }
    } catch (e) {}
}

window.toggleSoundSFX = function() {
    window.state.soundEnabled = !window.state.soundEnabled;
    const icon = getEl("soundIcon");
    if (icon) icon.innerText = window.state.soundEnabled ? "🔔 Sonidos ON" : "🔕 Silenciado";
    showStatus("🔔", window.state.soundEnabled ? "Sonidos adorables activados" : "Sonidos silenciados");
};

// ----------------------------------------------------
// 2. Tokens & Juror Passcode Handling
// ----------------------------------------------------
async function checkUserTokens() {
    try {
        const res = await fetch("/api/user_tokens");
        const data = await res.json();
        window.state.tokensLeft = data.tokens;
        window.state.isJuror = data.is_juror;
        updateTokensUI();
    } catch(e) {}
}

function updateTokensUI() {
    const pill = getEl("fishTokenPill");
    const label = getEl("fishTokenLabel");
    if (!pill || !label) return;

    if (window.state.isJuror) {
        pill.classList.add("juror-mode");
        label.innerText = "👑 MODO JURADO";
    } else {
        pill.classList.remove("juror-mode");
        label.innerText = `${window.state.tokensLeft}/5 Pescaditos`;
    }
}

window.promptJurorCode = function() {
    playSFX('click');
    if (window.state.isJuror) {
        showStatus("👑", "¡Modo Jurado ya activado! Generaciones ilimitadas.");
        return;
    }
    const code = prompt("Introduce la Clave de Jurado para desbloquear generaciones ilimitadas (ej. H3CONTEST):");
    if (code) {
        verifyJurorCode(code);
    }
};

async function verifyJurorCode(code) {
    try {
        const res = await fetch("/api/verify_juror", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: code })
        });
        const data = await res.json();
        if (res.ok) {
            window.state.isJuror = true;
            window.state.jurorCode = code;
            localStorage.setItem("cat_juror_code", code);
            updateTokensUI();
            playSFX('success');
            showStatus("👑", "¡Clave de Jurado aceptada! Modo Ilimitado activado.");
        } else {
            alert(data.detail || "Clave incorrecta.");
        }
    } catch (e) {
        alert("Error verificando clave: " + e.message);
    }
}

// ----------------------------------------------------
// 3. Floating Pastel Canvas Particles
// ----------------------------------------------------
function initPastelCanvas() {
    const canvas = getEl("pastelPawsCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    
    window.addEventListener("resize", () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const items = ["🐾", "🌸", "🫧", "🧶", "✨", "🐟"];
    const particles = Array.from({ length: 25 }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        char: items[Math.floor(Math.random() * items.length)],
        size: Math.random() * 16 + 18,
        speed: Math.random() * 0.4 + 0.15,
        angle: Math.random() * Math.PI * 2,
        opacity: Math.random() * 0.35 + 0.2
    }));

    function render() {
        ctx.clearRect(0, 0, width, height);
        particles.forEach(p => {
            p.y -= p.speed;
            p.angle += 0.01;
            p.x += Math.sin(p.angle) * 0.3;
            if (p.y < -30) {
                p.y = height + 30;
                p.x = Math.random() * width;
            }
            ctx.save();
            ctx.globalAlpha = p.opacity;
            ctx.font = `${p.size}px sans-serif`;
            ctx.fillText(p.char, p.x, p.y);
            ctx.restore();
        });
        requestAnimationFrame(render);
    }
    render();
}

function showStatus(icon, msg, isError = false) {
    const banner = getEl("statusBanner");
    const iconEl = getEl("statusIcon");
    const msgEl = getEl("statusMsg");
    if (!banner) return;
    
    if (iconEl) iconEl.innerText = icon;
    if (msgEl) msgEl.innerText = msg;
    banner.className = `pastel-toast active ${isError ? 'error' : ''}`;
    setTimeout(() => {
        banner.classList.remove("active");
    }, 6000);
}

// ----------------------------------------------------
// 4. Fullscreen Engine
// ----------------------------------------------------
window.toggleFullscreen = function() {
    playSFX('click');
    const container = getEl("appContainer") || document.documentElement;
    const video = getEl("mainVideo");
    const label = getEl("fsLabel");

    const isNativeFs = document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement;
    const isCssFs = document.body.classList.contains("immersive-fullscreen");

    if (isNativeFs || isCssFs) {
        if (document.exitFullscreen) {
            document.exitFullscreen().catch(() => {});
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        }
        document.body.classList.remove("immersive-fullscreen");
        if (label) label.innerText = "⛶ Pantalla Completa";
        showStatus("⛶", "Modo normal");
    } else {
        let requested = false;
        if (container.requestFullscreen) {
            container.requestFullscreen().then(() => { requested = true; }).catch(() => {});
        } else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
            requested = true;
        }

        if (!requested && video && video.webkitEnterFullscreen) {
            try {
                video.webkitEnterFullscreen();
                requested = true;
            } catch (e) {}
        }

        document.body.classList.add("immersive-fullscreen");
        if (label) label.innerText = "✕ Salir Pantalla";
        showStatus("✨", "¡Modo Cine a Pantalla Completa activado!");
    }
};

function handleFsChange() {
    const isFs = document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement;
    const label = getEl("fsLabel");
    if (!isFs) {
        document.body.classList.remove("immersive-fullscreen");
        if (label) label.innerText = "⛶ Pantalla Completa";
    } else {
        document.body.classList.add("immersive-fullscreen");
        if (label) label.innerText = "✕ Salir Pantalla";
    }
}
document.addEventListener("fullscreenchange", handleFsChange);
document.addEventListener("webkitfullscreenchange", handleFsChange);

// Mood Setting
window.setMood = function(moodKey) {
    playSFX('click');
    window.state.currentMood = moodKey;
    document.querySelectorAll(".mood-cute-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-mood") === moodKey);
    });
    showStatus("🎨", `Clima cambiado a: ${moodKey.replace('_', ' ').toUpperCase()}`);
};

// ----------------------------------------------------
// 5. Navigation: Main Menu Hub <-> Theater
// ----------------------------------------------------
window.showHubView = function() {
    playSFX('click');
    const hub = getEl("hubView");
    const theater = getEl("theaterView");
    const btnBack = getEl("btnBackToHub");
    const btnExport = getEl("btnExportMovie");
    const subtitle = getEl("headerSubtitle");
    
    if (hub) hub.style.display = "flex";
    if (theater) theater.style.display = "none";
    if (btnBack) btnBack.style.display = "none";
    if (btnExport) btnExport.style.display = "none";
    if (subtitle) subtitle.innerText = "🐾 Elige tu aventura favorita";
    
    const video = getEl("mainVideo");
    if (video) video.pause();
    
    loadWorldsGrid(); renderMyCustomWorlds();
};

window.showTheaterView = function() {
    const hub = getEl("hubView");
    const theater = getEl("theaterView");
    const btnBack = getEl("btnBackToHub");
    const btnExport = getEl("btnExportMovie");
    
    if (hub) hub.style.display = "none";
    if (theater) theater.style.display = "grid";
    if (btnBack) btnBack.style.display = "inline-flex";
    if (btnExport) btnExport.style.display = "inline-flex";
};

// Load World Cards in Grid
async function loadWorldsGrid() {
    const grid = getEl("worldsGrid");
    if (!grid) return;
    
    try {
        const res = await fetch("/api/universes");
        const list = await res.json();
        
        grid.innerHTML = "";
        list.forEach(u => {
            const card = document.createElement("div");
            card.className = "pastel-card";
            card.innerHTML = `
                <div class="pastel-card-top-3d">
                    <img src="${u.image_3d || '/static/icon_scratchers_3d.jpg'}" alt="${u.title}" class="world-image-3d">
                    <span class="world-badge-3d-icon">${u.icon}</span>
                </div>
                <div class="pastel-card-body">
                    <span class="world-subtitle">${u.subtitle}</span>
                    <h3 class="world-title">${u.title}</h3>
                    <p class="world-desc">${u.description}</p>
                    <button class="btn-enter-cute">🐾 ¡JUGAR ESTA AVENTURA!</button>
                </div>
            `;
            card.onmouseenter = () => playSFX('hover');
            card.onclick = () => {
                playSFX('click');
                selectUniverse(u);
            };
            grid.appendChild(card);
        });
    } catch (e) {
        console.error("Error cargando mundos:", e);
    }
}

// Select universe
window.selectUniverse = function(universe) {
    window.state.currentUniverse = universe;
    getEl("headerSubtitle").innerText = `${universe.icon} ${universe.title.toUpperCase()}`;
    getEl("currentWorldIcon").innerText = universe.icon;
    
    const starter = universe.starter;
    window.state.history = [{
        index: 1,
        title: starter.choices ? starter.choices[0].title || starter.choices[0].text.substring(0, 25) : "Inicio",
        narrative: starter.narrative,
        video_url: starter.video_url,
        prompt: starter.prompt
    }];
    
    showTheaterView();
    loadScene(starter);
    updateReel();
    showStatus("🌟", `¡Mundo de ${universe.title} listo!`);
};

// Custom world creation with H3 Max
window.createCustomWorld = async function() {
    playSFX('click');
    const titleInput = getEl("customWorldTitle");
    const themeInput = getEl("customWorldTheme");
    const title = titleInput ? titleInput.value.trim() : "";
    const theme = themeInput ? themeInput.value.trim() : "";
    
    if (!theme) {
        alert("Por favor describe qué quieres que haya en tu mundo felino.");
        return;
    }
    
    showStatus("✨", "¡Creando tu mundo mágico para el gatito con H3 Max (unos 9s)...");
    
    const overlay = getEl("videoOverlay");
    const titleEl = getEl("overlayTitle");
    const subEl = getEl("overlaySub");
    if (titleEl) titleEl.innerText = `¡CREANDO EL MUNDO: ${title.toUpperCase() || 'MÁGICO'}!`;
    if (subEl) subEl.innerText = "Renderizando la primera escena con H3 Max a partir de tu idea...";
    if (overlay) overlay.classList.add("active");
    startGenerationTimer();
    
    try {
        const res = await fetch("/api/universe/custom", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                universe_id: "custom",
                custom_title: title || "Mundo Mágico",
                custom_theme: theme
            })
        });
        
        const newUniverse = await res.json();
        if (!res.ok) throw new Error(newUniverse.detail || "Error creando mundo");
        
        if (titleInput) titleInput.value = "";
        if (themeInput) themeInput.value = "";
        
        // Save to personal custom worlds
        saveCustomWorldLocal(newUniverse);

        selectUniverse(newUniverse);
        playSFX('success');
        showStatus("🎉", `¡Mundo "${newUniverse.title}" creado con éxito!`);
        checkUserTokens();
    } catch (err) {
        alert("Aviso: " + err.message);
        showStatus("❌", err.message, true);
    } finally {
        stopGenerationTimer();
        if (overlay) overlay.classList.remove("active");
    }
};


function loadScene(scene) {
    const narText = getEl("narrativeText");
    const video = getEl("mainVideo");
    const grid = getEl("choicesGrid");
    const chapterTag = getEl("chapterTag");
    
    if (chapterTag) chapterTag.innerText = `ESCENA ${window.state.history.length}`;
    if (narText) narText.innerText = scene.narrative;
    if (video) {
        video.src = scene.video_url;
        video.play().catch(e => console.log("Autoplay:", e));
    }
    
    if (grid) {
        grid.innerHTML = "";
        if (scene.choices && scene.choices.length > 0) {
            scene.choices.forEach((ch, idx) => {
                const card = document.createElement("button");
                card.className = "bento-cute-card";
                card.innerHTML = `
                    <div class="bento-card-header">
                        <div class="bento-title-group">
                            <span class="bento-cute-icon">${ch.icon || '🐾'}</span>
                            <span class="bento-cute-title">${ch.title || `Opción ${idx + 1}`}</span>
                        </div>
                        <span class="bento-cute-badge">Opción ${idx + 1}</span>
                    </div>
                    <p class="bento-cute-desc">${ch.text}</p>
                `;
                card.onmouseenter = () => playSFX('hover');
                card.onclick = () => {
                    playSFX('click');
                    submitAction(ch.text);
                };
                grid.appendChild(card);
            });
        }
    }
}

async function submitAction(actionText) {
    if (window.state.isGenerating || !actionText.trim()) return;
    
    window.state.isGenerating = true;
    startGenerationTimer();
    
    const overlay = getEl("videoOverlay");
    const titleEl = getEl("overlayTitle");
    const subEl = getEl("overlaySub");
    const input = getEl("userInput");
    
    if (titleEl) titleEl.innerText = "¡DIBUJANDO LA SIGUIENTE ESCENA!";
    if (subEl) subEl.innerText = "Creando un momento mágico con gatitos...";
    showStatus("🚀", "¡Enviando orden mágica a H3 Max!");
    
    if (overlay) overlay.classList.add("active");
    if (input) input.value = "";
    
    try {
        const currentUid = window.state.currentUniverse ? window.state.currentUniverse.id : "scratchers_city";
        const res = await fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_input: actionText,
                universe: currentUid,
                mood: window.state.currentMood,
                history: window.state.history,
                juror_code: window.state.jurorCode
            })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Error en la generación");
        
        const nextScene = {
            video_url: data.video_url,
            narrative: data.narrative,
            choices: data.choices
        };
        
        window.state.history.push({
            index: window.state.history.length + 1,
            title: actionText.substring(0, 30) + "...",
            narrative: data.narrative,
            video_url: data.video_url,
            prompt: data.prompt_used
        });
        
        if (typeof data.tokens_left !== "undefined") {
            window.state.tokensLeft = data.tokens_left;
            window.state.isJuror = data.is_juror;
            updateTokensUI();
        }

        loadScene(nextScene);
        updateReel();
        playSFX('success');
        const badgeMsg = data.cache_hit ? `⚡ ¡Escena de Caché instantánea! ($0.00)` : `✨ ¡Generada con H3 Max en ${data.generation_time}!`;
        showStatus("✨", badgeMsg);
        
    } catch (err) {
        console.error("Error completo:", err);
        showStatus("❌", err.message, true);
        alert("Aviso: " + err.message);
    } finally {
        stopGenerationTimer();
        if (overlay) overlay.classList.remove("active");
        window.state.isGenerating = false;
    }
}

window.handleSendClick = function() {
    const input = getEl("userInput");
    if (input && input.value) {
        playSFX('click');
        submitAction(input.value);
    }
};

window.restartStory = function() {
    playSFX('click');
    if (confirm("¿Quieres empezar esta historia desde el principio?")) {
        if (window.state.currentUniverse) {
            selectUniverse(window.state.currentUniverse);
        }
    }
};

function updateReel() {
    const reelTimeline = getEl("reelTimeline");
    const reelCount = getEl("reelCount");
    if (!reelTimeline || !reelCount) return;
    
    reelTimeline.innerHTML = "";
    reelCount.innerText = `${window.state.history.length} ${window.state.history.length === 1 ? "Escena" : "Escenas"}`;
    
    window.state.history.forEach((item, i) => {
        const div = document.createElement("div");
        div.className = `scrap-card ${i === window.state.history.length - 1 ? "active" : ""}`;
        div.innerHTML = `
            <div class="scrap-card-header">
                <span>ESCENA ${item.index}</span>
                <span>${item.index === 1 ? "🐾 Apertura" : "✨ Elección"}</span>
            </div>
            <div class="scrap-card-desc">${item.narrative.substring(0, 75)}...</div>
        `;
        div.onmouseenter = () => playSFX('hover');
        div.onclick = () => {
            playSFX('click');
            const video = getEl("mainVideo");
            const nar = getEl("narrativeText");
            if (video) {
                video.src = item.video_url;
                video.play();
            }
            if (nar) nar.innerText = item.narrative;
        };
        reelTimeline.appendChild(div);
    });
}

// Export Movie with FFmpeg
window.exportFullMovie = async function() {
    playSFX('click');
    if (!window.state.history || window.state.history.length === 0) {
        alert("No hay escenas generadas para exportar.");
        return;
    }
    
    const urls = window.state.history.map(h => h.video_url);
    const uTitle = window.state.currentUniverse ? window.state.currentUniverse.title.replace(/\s+/g, '_') : "Pelicula_Gatitos";
    
    showStatus("⏳", "Uniendo todas las escenas en una sola película...");
    
    try {
        const res = await fetch("/api/export_movie", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                video_urls: urls,
                title: uTitle
            })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Error en la exportación");
        
        const a = document.createElement("a");
        a.href = data.download_url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        playSFX('success');
        showStatus("🎉", `¡Película descargada con éxito! (${data.clips_count} escenas unidas)`);
    } catch (e) {
        alert("Error al exportar la película: " + e.message);
    }
};

function startGenerationTimer() {
    let startTime = Date.now();
    const timer = getEl("genTimer");
    if (timer) timer.innerText = "0.0s";
    window.state.timerInterval = setInterval(() => {
        let elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        if (timer) timer.innerText = `${elapsed}s`;
    }, 100);
}

function stopGenerationTimer() {
    if (window.state.timerInterval) clearInterval(window.state.timerInterval);
}

// Voice Recognition
let recognition = null;
let isRecording = false;

function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    
    recognition = new SpeechRecognition();
    recognition.lang = "es-ES";
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const input = getEl("userInput");
        if (input) input.value = transcript;
        submitAction(transcript);
    };
    
    recognition.onend = () => {
        isRecording = false;
        const btn = getEl("btnMic");
        const lbl = getEl("micLabel");
        if (btn) btn.classList.remove("recording");
        if (lbl) lbl.innerText = "¡HABLA POR EL MICRO!";
    };
    
    recognition.onerror = (e) => {
        console.error("Error voz:", e.error);
        isRecording = false;
        const btn = getEl("btnMic");
        const lbl = getEl("micLabel");
        if (btn) btn.classList.remove("recording");
        if (lbl) lbl.innerText = "¡HABLA POR EL MICRO!";
    };
}

window.toggleVoice = function() {
    playSFX('click');
    if (!recognition) {
        alert("Tu navegador no soporta reconocimiento de voz nativo.");
        return;
    }
    
    const btn = getEl("btnMic");
    const lbl = getEl("micLabel");
    
    if (!isRecording) {
        try {
            recognition.start();
            isRecording = true;
            if (btn) btn.classList.add("recording");
            if (lbl) lbl.innerText = "🐾 ¡ESCUCHANDO TU VOZ!...";
        } catch (e) {
            console.error(e);
        }
    } else {
        recognition.stop();
    }
};

// Keyboard shortcuts
document.addEventListener("keydown", (e) => {
    if (document.activeElement.tagName === "INPUT") return;
    
    if (e.key === "f" || e.key === "F") {
        toggleFullscreen();
    } else if (e.key === "1" || e.key === "2" || e.key === "3") {
        const idx = parseInt(e.key) - 1;
        const cards = document.querySelectorAll(".bento-cute-card");
        if (cards && cards[idx]) {
            cards[idx].click();
        }
    }
});

// Init on load
window.addEventListener("DOMContentLoaded", () => {
    initPastelCanvas();
    loadWorldsGrid(); renderMyCustomWorlds();
    checkUserTokens();
    setupSpeechRecognition();
    
    const input = getEl("userInput");
    if (input) {
        input.onkeydown = (e) => {
            if (e.key === "Enter") handleSendClick();
        };
    }
});
