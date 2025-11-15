let questions = [];
let submittedCount = 0;

window.addEventListener('load', async () => {
    await initializeProctoring('Round 2 - Non-Technical');
    await loadQuestions();
});

async function loadQuestions() {
    try {
        const response = await fetch('/api/non-technical/questions');
        const data = await response.json();
        
        questions = data.questions;
        displayQuestions();
    } catch (error) {
        console.error('Error loading questions:', error);
    }
}

function displayQuestions() {
    const container = document.getElementById('questionsContainer');
    container.innerHTML = '';
    
    questions.forEach((q, index) => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'bg-white rounded-lg shadow-lg p-6 mb-4';
        questionDiv.innerHTML = `
            <h3 class="text-xl font-bold mb-4">Question ${index + 1}</h3>
            <p class="text-gray-700 mb-4">${q.question}</p>
            <textarea 
                id="answer_${q.id}" 
                rows="6" 
                class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500"
                placeholder="Type your answer here... (Minimum 50 words recommended)"
            ></textarea>
            <div class="mt-4 flex justify-between items-center">
                <span id="wordcount_${q.id}" class="text-sm text-gray-600">0 words</span>
                <button 
                    id="submit_${q.id}" 
                    class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg"
                    onclick="submitAnswer(${q.id})"
                >
                    Submit Answer
                </button>
            </div>
            <div id="result_${q.id}" class="hidden mt-4 p-4 bg-blue-50 rounded-lg">
                <p class="font-bold mb-2">AI Evaluation:</p>
                <p class="mb-2">Score: <span id="score_${q.id}" class="text-2xl font-bold text-blue-600"></span>/100</p>
                <p class="text-gray-700" id="feedback_${q.id}"></p>
            </div>
        `;
        
        container.appendChild(questionDiv);
        
        const textarea = document.getElementById(`answer_${q.id}`);
        textarea.addEventListener('input', () => {
            const words = textarea.value.trim().split(/\s+/).filter(w => w.length > 0).length;
            document.getElementById(`wordcount_${q.id}`).textContent = `${words} words`;
        });
    });
}

async function submitAnswer(questionId) {
    const answer = document.getElementById(`answer_${questionId}`).value.trim();
    
    if (answer.length < 20) {
        alert('Please write a more detailed answer (at least 20 characters).');
        return;
    }
    
    const button = document.getElementById(`submit_${questionId}`);
    button.disabled = true;
    button.textContent = 'Evaluating...';
    
    try {
        const response = await fetch('/api/non-technical/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: questionId,
                answer: answer
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById(`score_${questionId}`).textContent = data.score;
            document.getElementById(`feedback_${questionId}`).textContent = data.feedback;
            document.getElementById(`result_${questionId}`).classList.remove('hidden');
            
            button.textContent = 'Submitted ✓';
            button.classList.remove('bg-green-600', 'hover:bg-green-700');
            button.classList.add('bg-gray-400');
            
            submittedCount++;
            
            if (submittedCount >= questions.length) {
                setTimeout(() => {
                    if (confirm('All questions submitted! Return to dashboard?')) {
                        stopProctoring();
                        window.location.href = '/student/dashboard';
                    }
                }, 2000);
            }
        }
    } catch (error) {
        console.error('Error submitting answer:', error);
        button.disabled = false;
        button.textContent = 'Submit Answer';
        alert('Failed to submit answer. Please try again.');
    }
}

window.submitAnswer = submitAnswer;
