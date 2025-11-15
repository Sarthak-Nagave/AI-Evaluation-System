let recognition = null;
let isRecording = false;
let transcript = '';

window.addEventListener('load', async () => {
    await initializeProctoring('Round 3 - Interview');
    initializeSpeechRecognition();
});

function initializeSpeechRecognition() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
    } else if ('SpeechRecognition' in window) {
        recognition = new SpeechRecognition();
    } else {
        alert('Speech recognition is not supported in your browser. Please use Chrome or Edge.');
        return;
    }
    
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
        isRecording = true;
        document.getElementById('micStatus').innerHTML = `
            <i class="fas fa-microphone text-red-600 mr-2"></i>
            <span class="text-red-600">Recording...</span>
        `;
    };
    
    recognition.onresult = (event) => {
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcriptPiece = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                transcript += transcriptPiece + ' ';
            } else {
                interimTranscript += transcriptPiece;
            }
        }
        
        document.getElementById('transcript').textContent = transcript + interimTranscript;
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
            console.log('No speech detected, continuing...');
        }
    };
    
    recognition.onend = () => {
        if (isRecording) {
            recognition.start();
        }
    };
}

document.getElementById('startRecording').addEventListener('click', () => {
    if (recognition) {
        recognition.start();
        document.getElementById('startRecording').classList.add('hidden');
        document.getElementById('stopRecording').classList.remove('hidden');
    }
});

document.getElementById('stopRecording').addEventListener('click', () => {
    if (recognition) {
        isRecording = false;
        recognition.stop();
        document.getElementById('stopRecording').classList.add('hidden');
        document.getElementById('startRecording').classList.remove('hidden');
        
        document.getElementById('micStatus').innerHTML = `
            <i class="fas fa-microphone-slash text-gray-600 mr-2"></i>
            <span>Microphone Off</span>
        `;
    }
});

document.getElementById('submitInterview').addEventListener('click', async () => {
    if (!transcript.trim()) {
        alert('Please record your interview answers before submitting!');
        return;
    }
    
    if (!confirm('Submit your interview? You cannot change it after submission.')) {
        return;
    }
    
    if (isRecording) {
        isRecording = false;
        recognition.stop();
    }
    
    const button = document.getElementById('submitInterview');
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Evaluating...';
    
    try {
        const response = await fetch('/api/interview/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript: transcript })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('commScore').textContent = data.scores.communication_score;
            document.getElementById('confScore').textContent = data.scores.confidence_score;
            document.getElementById('clarScore').textContent = data.scores.clarity_score;
            document.getElementById('relScore').textContent = data.scores.relevance_score;
            document.getElementById('feedback').textContent = data.scores.feedback;
            
            document.querySelector('.bg-white.rounded-lg.shadow-lg.p-6.mb-4').classList.add('hidden');
            document.getElementById('resultsContainer').classList.remove('hidden');
            
            stopProctoring();
        }
    } catch (error) {
        console.error('Error submitting interview:', error);
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-check mr-2"></i>Submit Interview';
        alert('Failed to submit interview. Please try again.');
    }
});
