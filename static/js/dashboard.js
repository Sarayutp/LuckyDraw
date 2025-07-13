// Global variables
let eventId;
let eventType;
let drumRollSound;
let tadaSound;
let isDrawing = false;
let eventConfig = {};

// Initialize dashboard
function initializeDashboard() {
    eventId = window.eventId;
    eventType = window.eventType;
    
    // Initialize audio
    initializeAudio();
    
    // Load initial state
    loadEventState();
    
    // Setup event listeners
    setupEventListeners();
}

// Setup all event listeners
function setupEventListeners() {
    // Add participant form
    document.getElementById('addParticipantForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addParticipant();
    });
    
    // Add prize form (if exists)
    const addPrizeForm = document.getElementById('addPrizeForm');
    if (addPrizeForm) {
        addPrizeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addPrize();
        });
    }
    
    // Draw button
    document.getElementById('drawButton').addEventListener('click', function() {
        if (!isDrawing) {
            performDraw();
        }
    });
    
    // Reset button
    document.getElementById('resetButton').addEventListener('click', function() {
        resetEvent();
    });
    
    // Settings button
    document.getElementById('settingsButton').addEventListener('click', function() {
        openSettingsModal();
    });
    
    // Settings form
    document.getElementById('settingsForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings();
    });
    
    // Test mode toggle
    document.getElementById('testModeToggle').addEventListener('change', function(e) {
        toggleTestMode();
    });
    
    // Undo button
    document.getElementById('undoButton').addEventListener('click', function() {
        undoLastDraw();
    });
    
    // File upload forms
    document.getElementById('uploadParticipantsForm').addEventListener('submit', function(e) {
        e.preventDefault();
        uploadParticipants();
    });
    
    const uploadPrizesForm = document.getElementById('uploadPrizesForm');
    if (uploadPrizesForm) {
        uploadPrizesForm.addEventListener('submit', function(e) {
            e.preventDefault();
            uploadPrizes();
        });
    }
    
    // Prize selection handlers
    const selectAllPrizes = document.getElementById('selectAllPrizes');
    if (selectAllPrizes) {
        selectAllPrizes.addEventListener('change', function(e) {
            toggleAllPrizes(e.target.checked);
        });
    }
}

// Initialize audio elements
function initializeAudio() {
    drumRollSound = document.getElementById('drumRollSound');
    tadaSound = document.getElementById('tadaSound');
    
    // Set volume levels and create fallback sounds
    if (drumRollSound) {
        drumRollSound.volume = 0.6;
        // Add error handler for missing audio files
        drumRollSound.addEventListener('error', function() {
            console.warn('Drum roll audio file not found, using Web Audio fallback');
        });
        // Check if audio can load
        drumRollSound.addEventListener('canplay', function() {
            console.log('Drum roll audio loaded successfully');
        });
    }
    if (tadaSound) {
        tadaSound.volume = 0.8;
        // Add error handler for missing audio files
        tadaSound.addEventListener('error', function() {
            console.warn('Tada audio file not found, using Web Audio fallback');
        });
        // Check if audio can load
        tadaSound.addEventListener('canplay', function() {
            console.log('Tada audio loaded successfully');
        });
    }
    
    // Initialize Web Audio API context for fallback sounds
    initializeWebAudio();
    
    // Enable audio on first user interaction
    document.addEventListener('click', enableAudio, { once: true });
}

// Load current event state
async function loadEventState() {
    try {
        const response = await fetch(`/api/event/${eventId}/state`);
        const data = await response.json();
        
        updateParticipantsList(data.remaining_participants);
        updatePrizesList(data.remaining_prizes);
        updatePrizeSelectionList(data.remaining_prizes);
        updateHistoryList(data.history);
        
        // Update event config
        if (data.config) {
            eventConfig = data.config;
            applyEventConfig();
        }
        
    } catch (error) {
        console.error('Error loading event state:', error);
        showError('เกิดข้อผิดพลาดในการโหลดข้อมูล');
    }
}

// Update participants list
function updateParticipantsList(participants) {
    const participantsList = document.getElementById('participantsList');
    const participantsCount = document.getElementById('participantsCount');
    
    if (participants.length === 0) {
        participantsList.innerHTML = '<div class="text-gray-500 text-center py-4">ยังไม่มีผู้เข้าร่วม</div>';
    } else {
        participantsList.innerHTML = participants.map(participant => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="font-medium text-gray-800">${escapeHtml(participant.name)}</span>
                <span class="text-xs text-gray-500">ID: ${participant.id}</span>
            </div>
        `).join('');
    }
    
    participantsCount.textContent = `ทั้งหมด ${participants.length} คน`;
}

// Update prizes list
function updatePrizesList(prizes) {
    const prizesList = document.getElementById('prizesList');
    const prizesCount = document.getElementById('prizesCount');
    
    if (!prizesList) return; // Exchange mode doesn't have prizes
    
    if (prizes.length === 0) {
        prizesList.innerHTML = '<div class="text-gray-500 text-center py-4">ยังไม่มีรางวัล</div>';
    } else {
        prizesList.innerHTML = prizes.map(prize => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="font-medium text-gray-800">${escapeHtml(prize.name)}</span>
                <span class="text-xs text-blue-600 font-semibold">เหลือ ${prize.remaining_quantity}</span>
            </div>
        `).join('');
    }
    
    const totalPrizes = prizes.reduce((sum, prize) => sum + prize.remaining_quantity, 0);
    prizesCount.textContent = `ทั้งหมด ${totalPrizes} รางวัล`;
}

// Update history list
function updateHistoryList(history) {
    const historyList = document.getElementById('historyList');
    const historyCount = document.getElementById('historyCount');
    const undoButton = document.getElementById('undoButton');
    
    if (history.length === 0) {
        historyList.innerHTML = '<div class="text-gray-500 text-center py-4">ยังไม่มีประวัติการจับรางวัล</div>';
        undoButton.classList.add('hidden');
    } else {
        historyList.innerHTML = history.map((record, index) => `
            <div class="p-3 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border-l-4 border-green-400">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="font-semibold text-gray-800">
                            ${eventType === 'classic' ? '🎉' : '🎁'} ${escapeHtml(record.receiver_name)}
                            ${record.prize_name ? ` ได้รับ ${escapeHtml(record.prize_name)}` : ''}
                            ${record.giver_name ? ` จาก ${escapeHtml(record.giver_name)}` : ''}
                        </div>
                        <div class="text-xs text-gray-600 mt-1">${record.drawn_at}</div>
                    </div>
                    <span class="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded-full">
                        #${history.length - index}
                    </span>
                </div>
            </div>
        `).join('');
        undoButton.classList.remove('hidden');
    }
    
    historyCount.textContent = `ทั้งหมด ${history.length} รายการ`;
}

// Add participant
async function addParticipant() {
    const nameInput = document.getElementById('participantName');
    const name = nameInput.value.trim();
    
    if (!name) {
        showError('กรุณากรอกชื่อผู้เข้าร่วม');
        return;
    }
    
    try {
        const response = await fetch(`/api/event/${eventId}/add_participant`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name })
        });
        
        const data = await response.json();
        
        if (data.success) {
            nameInput.value = '';
            showSuccess(`เพิ่ม ${data.participant.name} เรียบร้อยแล้ว`);
            loadEventState(); // Refresh the lists
        } else {
            showError(data.error || 'เกิดข้อผิดพลาด');
        }
        
    } catch (error) {
        console.error('Error adding participant:', error);
        showError('เกิดข้อผิดพลาดในการเพิ่มผู้เข้าร่วม');
    }
}

// Add prize
async function addPrize() {
    const nameInput = document.getElementById('prizeName');
    const quantityInput = document.getElementById('prizeQuantity');
    const name = nameInput.value.trim();
    const quantity = parseInt(quantityInput.value);
    
    if (!name) {
        showError('กรุณากรอกชื่อรางวัล');
        return;
    }
    
    if (!quantity || quantity <= 0) {
        showError('กรุณากรอกจำนวนที่ถูกต้อง');
        return;
    }
    
    try {
        const response = await fetch(`/api/event/${eventId}/add_prize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name, quantity: quantity })
        });
        
        const data = await response.json();
        
        if (data.success) {
            nameInput.value = '';
            quantityInput.value = '';
            showSuccess(`เพิ่มรางวัล ${data.prize.name} (${data.prize.total_quantity} รางวัล) เรียบร้อยแล้ว`);
            loadEventState(); // Refresh the lists
        } else {
            showError(data.error || 'เกิดข้อผิดพลาด');
        }
        
    } catch (error) {
        console.error('Error adding prize:', error);
        showError('เกิดข้อผิดพลาดในการเพิ่มรางวัล');
    }
}

// Perform draw
async function performDraw() {
    if (isDrawing) return;
    
    isDrawing = true;
    const drawButton = document.getElementById('drawButton');
    const drawStatus = document.getElementById('drawStatus');
    
    // Disable button during draw
    drawButton.disabled = true;
    drawButton.textContent = '🎲 กำลังจับรางวัล...';
    drawStatus.textContent = 'กำลังดำเนินการ...';
    
    // Start randomization animation and sound
    startRandomizationEffect();
    
    try {
        // Use configured delay or default
        const delayMs = eventConfig.delay_ms || 2000;
        await new Promise(resolve => setTimeout(resolve, delayMs + Math.random() * 1000));
        
        // Get selected prizes for classic mode
        let requestBody = {};
        if (eventType === 'classic') {
            const selectedPrizes = getSelectedPrizes();
            if (selectedPrizes.length > 0) {
                requestBody.selected_prizes = selectedPrizes;
            }
        }
        
        const response = await fetch(`/api/event/${eventId}/draw`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        // Stop randomization effect
        stopRandomizationEffect();
        
        if (data.success) {
            // Play tada sound
            playTadaSound();
            
            // Show winner announcement with confetti
            showWinnerAnnouncement(data);
            
            // Refresh the event state
            setTimeout(() => {
                loadEventState();
            }, 1000);
            
        } else {
            showError(data.error || 'เกิดข้อผิดพลาดในการจับรางวัล');
        }
        
    } catch (error) {
        console.error('Error performing draw:', error);
        stopRandomizationEffect();
        showError('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์');
    } finally {
        // Re-enable button
        isDrawing = false;
        drawButton.disabled = false;
        drawButton.innerHTML = '🎲 จับรางวัล';
        drawStatus.textContent = '';
    }
}


// Close winner modal
function closeWinnerModal() {
    const modal = document.getElementById('winnerModal');
    modal.classList.add('hidden');
}

// Start randomization effect
function startRandomizationEffect() {
    const overlay = document.getElementById('randomizationOverlay');
    const randomizingText = document.getElementById('randomizingText');
    
    overlay.classList.remove('hidden');
    
    // Play drum roll sound
    playDrumRollSound();
    
    // Start text randomization
    const possibleTexts = ['🎲', '🎯', '🎪', '✨', '🎊', '🎉'];
    let textIndex = 0;
    
    window.randomizationInterval = setInterval(() => {
        randomizingText.textContent = possibleTexts[textIndex % possibleTexts.length];
        textIndex++;
    }, 100);
}

// Stop randomization effect
function stopRandomizationEffect() {
    const overlay = document.getElementById('randomizationOverlay');
    
    overlay.classList.add('hidden');
    
    // Stop drum roll sound
    stopDrumRollSound();
    
    // Stop text randomization
    if (window.randomizationInterval) {
        clearInterval(window.randomizationInterval);
        window.randomizationInterval = null;
    }
}

// Web Audio API setup
let audioContext;
let drumRollOscillator;

function initializeWebAudio() {
    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {
        console.warn('Web Audio API not supported, audio disabled');
    }
}

function enableAudio() {
    if (audioContext && audioContext.state === 'suspended') {
        audioContext.resume().then(() => {
            console.log('Audio context resumed successfully');
        }).catch((e) => {
            console.warn('Failed to resume audio context:', e);
        });
    }
}

// Audio functions
function playDrumRollSound() {
    // Check if music is disabled in config
    if (eventConfig.music_id === 'none') {
        return;
    }
    
    if (drumRollSound) {
        drumRollSound.currentTime = 0;
        drumRollSound.play().catch(e => {
            console.log('Audio file play failed, using Web Audio fallback:', e);
            playDrumRollFallback();
        });
    } else {
        playDrumRollFallback();
    }
}

function stopDrumRollSound() {
    if (drumRollSound) {
        drumRollSound.pause();
        drumRollSound.currentTime = 0;
    }
    stopDrumRollFallback();
}

function playTadaSound() {
    // Check if music is disabled in config
    if (eventConfig.music_id === 'none') {
        return;
    }
    
    if (tadaSound) {
        tadaSound.currentTime = 0;
        tadaSound.play().catch(e => {
            console.log('Audio file play failed, using Web Audio fallback:', e);
            playTadaFallback();
        });
    } else {
        playTadaFallback();
    }
}

// Web Audio API fallback sounds
function playDrumRollFallback() {
    if (!audioContext) return;
    
    try {
        // Stop any existing drum roll first
        stopDrumRollFallback();
        
        // Resume audio context if needed (browser autoplay policy)
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
        
        // Create drum roll effect using oscillator
        drumRollOscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        drumRollOscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Configure based on music setting
        const musicType = eventConfig.music_id || 'default_upbeat';
        switch (musicType) {
            case 'dramatic':
                drumRollOscillator.frequency.setValueAtTime(80, audioContext.currentTime);
                drumRollOscillator.frequency.exponentialRampToValueAtTime(120, audioContext.currentTime + 2);
                break;
            case 'festive':
                drumRollOscillator.frequency.setValueAtTime(200, audioContext.currentTime);
                drumRollOscillator.frequency.exponentialRampToValueAtTime(400, audioContext.currentTime + 1);
                break;
            default: // default_upbeat
                drumRollOscillator.frequency.setValueAtTime(150, audioContext.currentTime);
                drumRollOscillator.frequency.exponentialRampToValueAtTime(300, audioContext.currentTime + 1.5);
                break;
        }
        
        drumRollOscillator.type = 'sawtooth';
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        
        // Add auto-stop after 10 seconds as safety measure
        drumRollOscillator.start();
        drumRollOscillator.stop(audioContext.currentTime + 10);
        
        // Store gain node reference for proper cleanup
        drumRollOscillator.gainNode = gainNode;
    } catch (e) {
        console.warn('Web Audio fallback failed:', e);
    }
}

function stopDrumRollFallback() {
    if (drumRollOscillator) {
        try {
            // Fade out the gain instead of abrupt stop
            if (drumRollOscillator.gainNode) {
                drumRollOscillator.gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.1);
            }
            // Stop the oscillator after fade out
            drumRollOscillator.stop(audioContext.currentTime + 0.1);
            drumRollOscillator = null;
        } catch (e) {
            // If oscillator already stopped, just clear the reference
            drumRollOscillator = null;
            console.warn('Error stopping drum roll oscillator:', e);
        }
    }
}

function playTadaFallback() {
    if (!audioContext) return;
    
    try {
        // Resume audio context if needed
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
        
        // Create celebratory sound effect with multiple tones
        playTadaTone(440, 0, 0.3); // A4
        playTadaTone(554, 0.1, 0.3); // C#5  
        playTadaTone(659, 0.2, 0.4); // E5
        
    } catch (e) {
        console.warn('Web Audio tada fallback failed:', e);
    }
}

function playTadaTone(frequency, delay, duration) {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime + delay);
    oscillator.type = 'sine';
    
    // Set up gain envelope
    gainNode.gain.setValueAtTime(0, audioContext.currentTime + delay);
    gainNode.gain.linearRampToValueAtTime(0.15, audioContext.currentTime + delay + 0.05);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + delay + duration);
    
    // Start and stop with proper timing
    oscillator.start(audioContext.currentTime + delay);
    oscillator.stop(audioContext.currentTime + delay + duration);
}

// Confetti effect using canvas-confetti
function triggerConfetti() {
    // Multiple confetti bursts for better effect
    const count = 200;
    const defaults = {
        origin: { y: 0.7 }
    };

    function fire(particleRatio, opts) {
        confetti(Object.assign({}, defaults, opts, {
            particleCount: Math.floor(count * particleRatio)
        }));
    }

    fire(0.25, {
        spread: 26,
        startVelocity: 55,
    });
    fire(0.2, {
        spread: 60,
    });
    fire(0.35, {
        spread: 100,
        decay: 0.91,
        scalar: 0.8
    });
    fire(0.1, {
        spread: 120,
        startVelocity: 25,
        decay: 0.92,
        scalar: 1.2
    });
    fire(0.1, {
        spread: 120,
        startVelocity: 45,
    });
}

// Reset event function
async function resetEvent() {
    const confirmed = confirm('คุณแน่ใจหรือไม่ว่าต้องการรีเซ็ตอีเวนต์?\n\nการดำเนินการนี้จะ:\n- ลบประวัติการจับรางวัลทั้งหมด\n- รีเซ็ตจำนวนรางวัลกลับสู่สถานะเริ่มต้น\n\nการกระทำนี้ไม่สามารถยกเลิกได้!');
    
    if (!confirmed) return;
    
    const resetButton = document.getElementById('resetButton');
    resetButton.disabled = true;
    resetButton.textContent = '🔄 กำลังรีเซ็ต...';
    
    try {
        const response = await fetch(`/api/event/${eventId}/reset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('รีเซ็ตอีเวนต์เรียบร้อยแล้ว');
            loadEventState(); // Refresh the state
        } else {
            showError(data.error || 'เกิดข้อผิดพลาดในการรีเซ็ตอีเวนต์');
        }
        
    } catch (error) {
        console.error('Error resetting event:', error);
        showError('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์');
    } finally {
        resetButton.disabled = false;
        resetButton.textContent = '🗑️ รีเซ็ตอีเวนต์';
    }
}

// Settings functions
function openSettingsModal() {
    // Populate form with current settings
    populateSettingsForm();
    
    const modal = document.getElementById('settingsModal');
    modal.classList.remove('hidden');
}

function closeSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.classList.add('hidden');
}

function populateSettingsForm() {
    if (!eventConfig) return;
    
    // Populate form fields with current config
    document.getElementById('configDelay').value = (eventConfig.delay_ms || 2000) / 1000;
    document.getElementById('configDrawText').value = eventConfig.draw_text || 'จับรางวัล';
    document.getElementById('configMusic').value = eventConfig.music_id || 'default_upbeat';
    document.getElementById('configRandomAnimation').value = eventConfig.random_animation || 'scrolling_names';
    document.getElementById('configWinnerAnimation').value = eventConfig.winner_animation || 'confetti';
    document.getElementById('configBackgroundUrl').value = eventConfig.background_url || '';
    document.getElementById('configLogoUrl').value = eventConfig.logo_url || '';
}

async function saveSettings() {
    const formData = {
        delay: parseFloat(document.getElementById('configDelay').value),
        draw_text: document.getElementById('configDrawText').value,
        music: document.getElementById('configMusic').value,
        random_animation: document.getElementById('configRandomAnimation').value,
        winner_animation: document.getElementById('configWinnerAnimation').value,
        background_url: document.getElementById('configBackgroundUrl').value,
        logo_url: document.getElementById('configLogoUrl').value
    };
    
    try {
        const response = await fetch(`/api/event/${eventId}/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            eventConfig = data.config;
            applyEventConfig();
            closeSettingsModal();
            showSuccess('บันทึกการตั้งค่าเรียบร้อยแล้ว');
        } else {
            showError(data.error || 'เกิดข้อผิดพลาดในการบันทึกการตั้งค่า');
        }
        
    } catch (error) {
        console.error('Error saving settings:', error);
        showError('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์');
    }
}

// Apply event configuration to the UI
function applyEventConfig() {
    if (!eventConfig) return;
    
    // Update draw button text
    const drawButton = document.getElementById('drawButton');
    if (drawButton && eventConfig.draw_text) {
        const buttonText = drawButton.innerHTML;
        const newText = buttonText.replace(/🎲 .+/, `🎲 ${eventConfig.draw_text}`);
        drawButton.innerHTML = newText;
    }
    
    // Apply background image
    if (eventConfig.background_url) {
        document.body.style.backgroundImage = `url('${eventConfig.background_url}')`;
        document.body.style.backgroundSize = 'cover';
        document.body.style.backgroundPosition = 'center';
        document.body.style.backgroundAttachment = 'fixed';
    } else {
        document.body.style.backgroundImage = '';
    }
    
    // Apply logo
    const logo = document.getElementById('eventLogo');
    if (logo) {
        if (eventConfig.logo_url) {
            logo.src = eventConfig.logo_url;
            logo.classList.remove('hidden');
            logo.onerror = function() {
                console.warn('Failed to load logo:', eventConfig.logo_url);
                logo.classList.add('hidden');
            };
        } else {
            logo.classList.add('hidden');
        }
    }
}

// Enhanced confetti based on winner animation config
function triggerConfetti() {
    const animationType = eventConfig.winner_animation || 'confetti';
    
    switch (animationType) {
        case 'fireworks':
            triggerFireworks();
            break;
        case 'balloons':
            triggerBalloons();
            break;
        case 'sparkles':
            triggerSparkles();
            break;
        case 'confetti':
        default:
            triggerDefaultConfetti();
            break;
    }
}

function triggerDefaultConfetti() {
    // Original confetti effect
    const count = 200;
    const defaults = {
        origin: { y: 0.7 }
    };

    function fire(particleRatio, opts) {
        confetti(Object.assign({}, defaults, opts, {
            particleCount: Math.floor(count * particleRatio)
        }));
    }

    fire(0.25, {
        spread: 26,
        startVelocity: 55,
    });
    fire(0.2, {
        spread: 60,
    });
    fire(0.35, {
        spread: 100,
        decay: 0.91,
        scalar: 0.8
    });
    fire(0.1, {
        spread: 120,
        startVelocity: 25,
        decay: 0.92,
        scalar: 1.2
    });
    fire(0.1, {
        spread: 120,
        startVelocity: 45,
    });
}

function triggerFireworks() {
    const duration = 3 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    function randomInRange(min, max) {
        return Math.random() * (max - min) + min;
    }

    const interval = setInterval(function() {
        const timeLeft = animationEnd - Date.now();

        if (timeLeft <= 0) {
            return clearInterval(interval);
        }

        const particleCount = 50 * (timeLeft / duration);
        confetti(Object.assign({}, defaults, { 
            particleCount, 
            origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } 
        }));
        confetti(Object.assign({}, defaults, { 
            particleCount, 
            origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } 
        }));
    }, 250);
}

function triggerBalloons() {
    confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff']
    });
}

function triggerSparkles() {
    const count = 200;
    const defaults = {
        origin: { y: 0.7 },
        shapes: ['star'],
        colors: ['#FFD700', '#FFA500', '#FF69B4', '#00CED1', '#9370DB']
    };

    function fire(particleRatio, opts) {
        confetti(Object.assign({}, defaults, opts, {
            particleCount: Math.floor(count * particleRatio)
        }));
    }

    fire(0.25, {
        spread: 26,
        startVelocity: 55,
    });
    fire(0.2, {
        spread: 60,
    });
    fire(0.35, {
        spread: 100,
        decay: 0.91,
        scalar: 0.8
    });
}

// Enhanced randomization animation based on config
function startRandomizationEffect() {
    const overlay = document.getElementById('randomizationOverlay');
    const randomizingText = document.getElementById('randomizingText');
    
    overlay.classList.remove('hidden');
    
    // Play drum roll sound
    playDrumRollSound();
    
    // Choose animation based on config
    const animationType = eventConfig.random_animation || 'scrolling_names';
    startRandomAnimation(randomizingText, animationType);
}

function startRandomAnimation(element, type) {
    let animationData;
    
    switch (type) {
        case 'spinning_wheel':
            animationData = ['🎯', '🎲', '🎪', '🎭', '🎨', '🎬'];
            break;
        case 'bouncing_icons':
            animationData = ['⭐', '✨', '🌟', '💫', '⚡', '🔥'];
            break;
        case 'matrix_rain':
            animationData = ['0', '1', '💾', '🔢', '📊', '💻'];
            break;
        case 'scrolling_names':
        default:
            // Use actual participant names for scrolling animation
            animationData = getParticipantNamesForAnimation();
            if (animationData.length === 0) {
                // Fallback to icons if no participants
                animationData = ['🎲', '🎯', '🎪', '✨', '🎊', '🎉'];
            }
            break;
    }
    
    let textIndex = 0;
    window.randomizationInterval = setInterval(() => {
        element.textContent = animationData[textIndex % animationData.length];
        textIndex++;
    }, type === 'scrolling_names' ? 150 : 100); // Slower for names to be readable
}


// Get participant names for scrolling animation
function getParticipantNamesForAnimation() {
    const participantsList = document.getElementById('participantsList');
    if (!participantsList) return [];
    
    const names = [];
    const participantElements = participantsList.querySelectorAll('.font-medium');
    participantElements.forEach(element => {
        const name = element.textContent.trim();
        if (name) names.push(name);
    });
    
    return names;
}

// Utility functions
function showSuccess(message) {
    // You can implement a toast notification here
    console.log('Success:', message);
    alert(message); // Temporary implementation
}

function showError(message) {
    // You can implement a toast notification here
    console.error('Error:', message);
    alert('ข้อผิดพลาด: ' + message); // Temporary implementation
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Test Mode and Undo functions
async function toggleTestMode() {
    const toggle = document.getElementById('testModeToggle');
    const originalState = toggle.checked;
    
    // Disable toggle during request
    toggle.disabled = true;
    
    try {
        const response = await fetch(`/api/event/${eventId}/toggle_test_mode`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update toggle state
            toggle.checked = data.is_test_mode;
            
            // Show confirmation message
            if (data.is_test_mode) {
                showSuccess('เปิดโหมดทดสอบแล้ว - การจับรางวัลจะไม่ถูกบันทึก');
            } else {
                showSuccess('ปิดโหมดทดสอบแล้ว - การจับรางวัลจะถูกบันทึกจริง');
            }
            
            // Reload state to update banner
            loadEventState();
        } else {
            // Revert toggle state on error
            toggle.checked = !originalState;
            showError(data.error || 'เกิดข้อผิดพลาดในการเปลี่ยนโหมดทดสอบ');
        }
        
    } catch (error) {
        console.error('Error toggling test mode:', error);
        toggle.checked = !originalState;
        showError('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์');
    } finally {
        toggle.disabled = false;
    }
}

async function undoLastDraw() {
    console.log('undoLastDraw function called'); // Debug log
    
    const confirmed = confirm('คุณแน่ใจหรือไม่ว่าต้องการยกเลิกการจับรางวัลครั้งล่าสุด?\n\nการกระทำนี้จะ:\n- ลบผลการจับรางวัลครั้งล่าสุด\n- คืนสถานะรางวัลและผู้เข้าร่วม\n\nการกระทำนี้ไม่สามารถยกเลิกได้!');
    
    if (!confirmed) {
        console.log('User cancelled undo'); // Debug log
        return;
    }
    
    const undoButton = document.getElementById('undoButton');
    undoButton.disabled = true;
    undoButton.textContent = '⏳ กำลังยกเลิก...';
    
    try {
        console.log('Making undo API call to:', `/api/event/${eventId}/undo_draw`); // Debug log
        
        const response = await fetch(`/api/event/${eventId}/undo_draw`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        console.log('Undo API response status:', response.status); // Debug log
        
        const data = await response.json();
        console.log('Undo API response data:', data); // Debug log
        
        if (data.success) {
            if (data.multiple_undone) {
                // Multiple records undone
                const winnerNames = data.undone_records.map(record => record.receiver_name).join(', ');
                showSuccess(`ยกเลิกการจับรางวัลเรียบร้อยแล้ว\nยกเลิกผู้ชนะ ${data.total_undone} คน: ${winnerNames}`);
            } else {
                // Single record undone
                showSuccess(`ยกเลิกการจับรางวัลเรียบร้อยแล้ว\nผู้โชคดี: ${data.undone_record.receiver_name}`);
            }
            loadEventState(); // Refresh the state
        } else {
            showError(data.error || 'เกิดข้อผิดพลาดในการยกเลิกการจับรางวัล');
        }
        
    } catch (error) {
        console.error('Error undoing last draw:', error);
        showError('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์');
    } finally {
        undoButton.disabled = false;
        undoButton.textContent = '↶ ยกเลิกครั้งล่าสุด';
    }
}

// Update winner announcement to show test mode
function showWinnerAnnouncement(data) {
    const modal = document.getElementById('winnerModal');
    const title = document.getElementById('winnerTitle');
    const content = document.getElementById('winnerContent');
    
    if (data.draw_type === 'classic') {
        if (data.multiple_winners) {
            // Multiple winners in Winner Showcase style
            title.innerHTML = data.is_test_mode ? 
                '🧪 ผลทดสอบ! 🧪' : 
                '🎉 ยินดีกับผู้โชคดี! 🎉';
            
            // Create winner cards grid
            const winnersGrid = data.results.map((result, index) => `
                <div class="winner-card-modal bg-slate-800 rounded-lg shadow-lg border-2 border-yellow-400 p-6 text-center transform hover:scale-105 transition-transform duration-300">
                    <div class="text-sm font-semibold text-slate-400 mb-2">WINNER #${index + 1}</div>
                    <div class="text-2xl md:text-3xl font-bold text-white mb-4 break-words">${escapeHtml(result.winner_name)}</div>
                    <div class="flex justify-center mb-3">
                        <svg class="w-8 h-8 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.715-5.349L11 6.477V16h2a1 1 0 110 2H7a1 1 0 110-2h2V6.477L6.237 7.582l1.715 5.349a1 1 0 01-.285 1.05A3.989 3.989 0 015 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L9 4.323V3a1 1 0 011-1z" clip-rule="evenodd"></path>
                        </svg>
                    </div>
                    <div class="text-sm text-yellow-300 font-medium break-words">${escapeHtml(result.prize_name)}</div>
                </div>
            `).join('');
            
            content.innerHTML = `
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 md:gap-6">
                    ${winnersGrid}
                </div>
                ${data.is_test_mode ? '<div class="text-center text-yellow-200 mt-6 text-lg">🧪 นี่เป็นโหมดทดสอบ - ไม่ถูกบันทึก</div>' : ''}
            `;
            
            // Animate cards in sequence after modal is shown
            setTimeout(() => animateWinnerCardsIn(), 100);
            
        } else {
            // Single winner in Winner Showcase style
            title.innerHTML = data.is_test_mode ? 
                '🧪 ผลทดสอบ! 🧪' : 
                '🎉 ยินดีกับผู้โชคดี! 🎉';
            
            content.innerHTML = `
                <div class="flex justify-center">
                    <div class="winner-card-modal bg-slate-800 rounded-lg shadow-lg border-2 border-yellow-400 p-8 text-center transform hover:scale-105 transition-transform duration-300 max-w-md">
                        <div class="text-lg font-semibold text-slate-400 mb-3">WINNER #1</div>
                        <div class="text-4xl font-bold text-white mb-6 break-words">${escapeHtml(data.winner_name)}</div>
                        <div class="flex justify-center mb-4">
                            <svg class="w-12 h-12 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.715-5.349L11 6.477V16h2a1 1 0 110 2H7a1 1 0 110-2h2V6.477L6.237 7.582l1.715 5.349a1 1 0 01-.285 1.05A3.989 3.989 0 015 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L9 4.323V3a1 1 0 011-1z" clip-rule="evenodd"></path>
                            </svg>
                        </div>
                        <div class="text-lg text-yellow-300 font-medium break-words">${escapeHtml(data.prize_name)}</div>
                    </div>
                </div>
                ${data.is_test_mode ? '<div class="text-center text-yellow-200 mt-6 text-lg">🧪 นี่เป็นโหมดทดสอบ - ไม่ถูกบันทึก</div>' : ''}
            `;
            
            // Animate single card
            setTimeout(() => animateWinnerCardsIn(), 100);
        }
    } else {
        // Exchange mode (keep simpler design)
        title.innerHTML = data.is_test_mode ? '🧪 ผลทดสอบ!' : '🎁 การแลกเปลี่ยนของขวัญ!';
        content.innerHTML = `
            <div class="flex justify-center">
                <div class="winner-card-modal bg-slate-800 rounded-lg shadow-lg border-2 border-yellow-400 p-8 text-center max-w-md">
                    <div class="text-2xl font-bold text-white mb-4">${escapeHtml(data.giver_name)}</div>
                    <div class="text-lg text-slate-300 mb-4">จะให้ของขวัญแก่</div>
                    <div class="text-4xl font-bold text-yellow-300">${escapeHtml(data.receiver_name)}</div>
                </div>
            </div>
            ${data.is_test_mode ? '<div class="text-center text-yellow-200 mt-6 text-lg">🧪 นี่เป็นโหมดทดสอบ - ไม่ถูกบันทึก</div>' : ''}
        `;
        
        setTimeout(() => animateWinnerCardsIn(), 100);
    }
    
    modal.classList.remove('hidden');
    
    // Create confetti effect using canvas-confetti
    triggerConfetti();
    
    // Auto close after longer time for multiple winners
    const autoCloseTime = data.multiple_winners ? (data.total_drawn * 3000 + 5000) : 8000;
    setTimeout(() => {
        closeWinnerModal();
    }, autoCloseTime);
}

// Animate winner cards appearing one by one
function animateWinnerCardsIn() {
    const cards = document.querySelectorAll('.winner-card-modal');
    
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('animate-in');
            
            // Add a small bounce effect for each card
            setTimeout(() => {
                card.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    card.style.transform = 'scale(1)';
                }, 100);
            }, 300);
            
        }, index * 150); // 150ms stagger between each card
    });
}

// File upload functions
async function uploadParticipants() {
    const fileInput = document.getElementById('participantsFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('กรุณาเลือกไฟล์');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const uploadButton = document.querySelector('#uploadParticipantsForm button[type="submit"]');
    uploadButton.disabled = true;
    uploadButton.textContent = '📤 กำลังอัปโหลด...';
    
    try {
        const response = await fetch(`/api/event/${eventId}/import_participants`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            fileInput.value = '';
            showSuccess(data.message);
            
            if (data.details.errors && data.details.errors.length > 0) {
                console.warn('Import errors:', data.details.errors);
                alert('มีข้อผิดพลาดบางรายการ กรุณาตรวจสอบ Console สำหรับรายละเอียด');
            }
            
            loadEventState(); // Refresh the lists
        } else {
            showError(data.error || 'เกิดข้อผิดพลาดในการอัปโหลด');
        }
        
    } catch (error) {
        console.error('Error uploading participants:', error);
        showError('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์');
    } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = '📤 อัปโหลดผู้เข้าร่วม';
    }
}

async function uploadPrizes() {
    const fileInput = document.getElementById('prizesFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('กรุณาเลือกไฟล์');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const uploadButton = document.querySelector('#uploadPrizesForm button[type="submit"]');
    uploadButton.disabled = true;
    uploadButton.textContent = '📤 กำลังอัปโหลด...';
    
    try {
        const response = await fetch(`/api/event/${eventId}/import_prizes`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            fileInput.value = '';
            showSuccess(data.message);
            
            if (data.details.errors && data.details.errors.length > 0) {
                console.warn('Import errors:', data.details.errors);
                alert('มีข้อผิดพลาดบางรายการ กรุณาตรวจสอบ Console สำหรับรายละเอียด');
            }
            
            loadEventState(); // Refresh the lists
        } else {
            showError(data.error || 'เกิดข้อผิดพลาดในการอัปโหลด');
        }
        
    } catch (error) {
        console.error('Error uploading prizes:', error);
        showError('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์');
    } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = '📤 อัปโหลดรางวัล';
    }
}

// Prize selection functions
function updatePrizeSelectionList(prizes) {
    const prizeSelectionList = document.getElementById('prizeSelectionList');
    
    if (!prizeSelectionList) return; // Exchange mode doesn't have prize selection
    
    if (prizes.length === 0) {
        prizeSelectionList.innerHTML = '<div class="text-gray-500 text-center py-4">ยังไม่มีรางวัล</div>';
    } else {
        prizeSelectionList.innerHTML = prizes.map(prize => `
            <div class="flex items-center justify-between p-2 bg-white rounded border">
                <div class="flex items-center space-x-2 flex-1">
                    <input type="checkbox" id="prize_${prize.id}" class="prize-checkbox rounded border-gray-300 text-blue-600 focus:ring-blue-500" data-prize-id="${prize.id}">
                    <label for="prize_${prize.id}" class="text-sm font-medium text-gray-800 flex-1 cursor-pointer">${escapeHtml(prize.name)}</label>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="text-xs text-gray-500">เหลือ ${prize.remaining_quantity}</span>
                    <input type="number" id="quantity_${prize.id}" min="1" max="${prize.remaining_quantity}" value="1" 
                           class="prize-quantity w-16 px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500" 
                           data-prize-id="${prize.id}" disabled>
                </div>
            </div>
        `).join('');
        
        // Add event listeners for checkboxes
        document.querySelectorAll('.prize-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updatePrizeQuantityInput(this);
                updateSelectAllCheckbox();
            });
        });
        
        // Add event listeners for quantity inputs
        document.querySelectorAll('.prize-quantity').forEach(input => {
            input.addEventListener('change', function() {
                validateQuantityInput(this);
            });
        });
    }
}

function updatePrizeQuantityInput(checkbox) {
    const prizeId = checkbox.dataset.prizeId;
    const quantityInput = document.getElementById(`quantity_${prizeId}`);
    
    if (quantityInput) {
        quantityInput.disabled = !checkbox.checked;
        if (!checkbox.checked) {
            quantityInput.value = 1;
        }
    }
}

function validateQuantityInput(input) {
    const max = parseInt(input.getAttribute('max'));
    const value = parseInt(input.value);
    
    if (isNaN(value) || value < 1) {
        input.value = 1;
    } else if (value > max) {
        input.value = max;
    }
}

function toggleAllPrizes(checked) {
    document.querySelectorAll('.prize-checkbox').forEach(checkbox => {
        checkbox.checked = checked;
        updatePrizeQuantityInput(checkbox);
    });
}

function updateSelectAllCheckbox() {
    const selectAllPrizes = document.getElementById('selectAllPrizes');
    const prizeCheckboxes = document.querySelectorAll('.prize-checkbox');
    const checkedBoxes = document.querySelectorAll('.prize-checkbox:checked');
    
    if (selectAllPrizes) {
        if (checkedBoxes.length === 0) {
            selectAllPrizes.checked = false;
            selectAllPrizes.indeterminate = false;
        } else if (checkedBoxes.length === prizeCheckboxes.length) {
            selectAllPrizes.checked = true;
            selectAllPrizes.indeterminate = false;
        } else {
            selectAllPrizes.checked = false;
            selectAllPrizes.indeterminate = true;
        }
    }
}

function getSelectedPrizes() {
    const selectedPrizes = [];
    
    document.querySelectorAll('.prize-checkbox:checked').forEach(checkbox => {
        const prizeId = parseInt(checkbox.dataset.prizeId);
        const quantityInput = document.getElementById(`quantity_${prizeId}`);
        const quantity = quantityInput ? parseInt(quantityInput.value) : 1;
        
        selectedPrizes.push({
            prize_id: prizeId,
            quantity: quantity
        });
    });
    
    return selectedPrizes;
}

// Global functions for template onclick handlers
window.closeSettingsModal = closeSettingsModal;
window.closeWinnerModal = closeWinnerModal;