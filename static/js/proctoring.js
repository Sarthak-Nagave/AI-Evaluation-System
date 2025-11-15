let videoStream = null;
let violationCount = 0;
let isFullscreen = false;
let tabSwitchCount = 0;

async function initializeProctoring(roundName) {
    try {
        videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: true, 
            audio: false 
        });
        
        const videoElement = document.getElementById('videoElement');
        if (videoElement) {
            videoElement.srcObject = videoStream;
        }
        
        enableFullscreen();
        setupEventListeners(roundName);
        
        console.log('Proctoring initialized');
    } catch (error) {
        console.error('Camera access denied:', error);
        showWarning('Camera access is required for this test!');
    }
}

function enableFullscreen() {
    const elem = document.documentElement;
    
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }
    
    isFullscreen = true;
}

function setupEventListeners(roundName) {
    document.addEventListener('fullscreenchange', () => handleFullscreenChange(roundName));
    document.addEventListener('webkitfullscreenchange', () => handleFullscreenChange(roundName));
    
    document.addEventListener('visibilitychange', () => handleVisibilityChange(roundName));
    
    window.addEventListener('blur', () => handleBlur(roundName));
    
    window.addEventListener('beforeunload', (e) => {
        e.preventDefault();
        e.returnValue = '';
    });
    
    document.addEventListener('contextmenu', (e) => e.preventDefault());
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'F12' || 
            (e.ctrlKey && e.shiftKey && e.key === 'I') ||
            (e.ctrlKey && e.shiftKey && e.key === 'J') ||
            (e.ctrlKey && e.key === 'u')) {
            e.preventDefault();
            logViolation('dev_tools_attempt', roundName);
        }
    });
}

function handleFullscreenChange(roundName) {
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
        isFullscreen = false;
        logViolation('fullscreen_exit', roundName);
        showWarning('Please return to fullscreen mode!');
        
        setTimeout(() => {
            enableFullscreen();
        }, 2000);
    } else {
        isFullscreen = true;
    }
}

function handleVisibilityChange(roundName) {
    if (document.hidden) {
        tabSwitchCount++;
        logViolation('tab_switch', roundName, { count: tabSwitchCount });
        showWarning(`Tab switching detected! Warning ${tabSwitchCount}/5`);
    }
}

function handleBlur(roundName) {
    logViolation('window_blur', roundName);
}

async function logViolation(type, roundName, details = {}) {
    violationCount++;
    
    try {
        const response = await fetch('/api/proctor/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: type,
                round: roundName,
                details: details
            })
        });
        
        const data = await response.json();
        
        if (data.flagged) {
            showWarning('Too many violations! Your test may be invalidated.');
        }
    } catch (error) {
        console.error('Error logging violation:', error);
    }
}

function showWarning(message) {
    const warningDiv = document.getElementById('proctorWarning');
    const warningText = document.getElementById('warningText');
    
    if (warningDiv && warningText) {
        warningText.textContent = message;
        warningDiv.classList.remove('hidden');
        
        setTimeout(() => {
            warningDiv.classList.add('hidden');
        }, 3000);
    }
}

function stopProctoring() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
    }
    
    if (document.exitFullscreen) {
        document.exitFullscreen();
    }
}

if (typeof window !== 'undefined') {
    window.initializeProctoring = initializeProctoring;
    window.stopProctoring = stopProctoring;
    window.logViolation = logViolation;
}
