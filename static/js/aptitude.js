let questions = [];
let currentIndex = 0;
let answers = {};
let startTime = Date.now();
let questionOrder = [];

window.addEventListener('load', async () => {
    await initializeProctoring('Round 1 - Aptitude');
    await loadQuestions();
    startTimer(3600);
});

async function loadQuestions() {
    try {
        const response = await fetch('/api/aptitude/questions');
        const data = await response.json();
        
        questions = data.questions;
        questionOrder = data.question_order;
        
        document.getElementById('totalQuestions').textContent = questions.length;
        
        displayQuestion();
    } catch (error) {
        console.error('Error loading questions:', error);
        alert('Failed to load questions. Please refresh the page.');
    }
}

function displayQuestion() {
    const question = questions[currentIndex];
    
    document.getElementById('currentQuestion').textContent = currentIndex + 1;
    document.getElementById('questionText').textContent = question.question;
    
    const optionsContainer = document.getElementById('optionsContainer');
    optionsContainer.innerHTML = '';
    
    for (const [key, value] of Object.entries(question.options)) {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'flex items-center p-4 border rounded-lg hover:bg-blue-50 cursor-pointer transition';
        
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'answer';
        radio.value = key;
        radio.id = `option_${key}`;
        radio.className = 'mr-3 w-5 h-5';
        
        if (answers[question.id] === key) {
            radio.checked = true;
        }
        
        radio.addEventListener('change', () => {
            answers[question.id] = key;
        });
        
        const label = document.createElement('label');
        label.htmlFor = `option_${key}`;
        label.className = 'flex-1 cursor-pointer';
        label.innerHTML = `<strong>${key}.</strong> ${value}`;
        
        optionDiv.appendChild(radio);
        optionDiv.appendChild(label);
        optionsContainer.appendChild(optionDiv);
    }
    
    document.getElementById('prevBtn').disabled = currentIndex === 0;
    document.getElementById('prevBtn').classList.toggle('opacity-50', currentIndex === 0);
    
    if (currentIndex === questions.length - 1) {
        document.getElementById('nextBtn').classList.add('hidden');
        document.getElementById('submitBtn').classList.remove('hidden');
    } else {
        document.getElementById('nextBtn').classList.remove('hidden');
        document.getElementById('submitBtn').classList.add('hidden');
    }
}

document.getElementById('prevBtn').addEventListener('click', () => {
    if (currentIndex > 0) {
        currentIndex--;
        displayQuestion();
    }
});

document.getElementById('nextBtn').addEventListener('click', () => {
    if (currentIndex < questions.length - 1) {
        currentIndex++;
        displayQuestion();
    }
});

document.getElementById('submitBtn').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to submit? You cannot change answers after submission.')) {
        return;
    }
    
    const timeTaken = Math.floor((Date.now() - startTime) / 1000);
    
    try {
        const response = await fetch('/api/aptitude/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                answers: answers,
                time_taken: timeTaken,
                question_order: questionOrder
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            stopProctoring();
            alert(`Test submitted successfully!\nYour score: ${data.score}/${data.total}`);
            window.location.href = '/student/dashboard';
        }
    } catch (error) {
        console.error('Error submitting test:', error);
        alert('Failed to submit test. Please try again.');
    }
});

function startTimer(seconds) {
    let remaining = seconds;
    
    const timerElement = document.getElementById('timer');
    
    const interval = setInterval(() => {
        const minutes = Math.floor(remaining / 60);
        const secs = remaining % 60;
        
        timerElement.textContent = `${minutes}:${secs.toString().padStart(2, '0')}`;
        
        if (remaining <= 300) {
            timerElement.classList.add('text-red-600');
        }
        
        remaining--;
        
        if (remaining < 0) {
            clearInterval(interval);
            document.getElementById('submitBtn').click();
        }
    }, 1000);
}
