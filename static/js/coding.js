let questions = [];
let currentQuestionId = null;
let editor = null;
let submittedQuestions = new Set();

window.addEventListener('load', async () => {
    await initializeProctoring('Round 2 - Coding');
    await loadQuestions();
    initializeEditor();
});

async function loadQuestions() {
    try {
        const response = await fetch('/api/coding/questions');
        const data = await response.json();
        
        questions = data.questions;
        displayQuestionTabs();
    } catch (error) {
        console.error('Error loading questions:', error);
    }
}

function displayQuestionTabs() {
    const tabsContainer = document.getElementById('questionTabs');
    tabsContainer.innerHTML = '';
    
    questions.forEach((q, index) => {
        const button = document.createElement('button');
        button.className = 'w-full text-left px-4 py-3 rounded-lg font-semibold transition';
        button.classList.add(index === 0 ? 'bg-blue-600 text-white' : 'bg-white hover:bg-gray-100');
        button.innerHTML = `
            <div class="flex justify-between items-center">
                <span>${index + 1}. ${q.title}</span>
                ${submittedQuestions.has(q.id) ? '<i class="fas fa-check text-green-500"></i>' : ''}
            </div>
            <div class="text-sm opacity-75">${q.difficulty}</div>
        `;
        
        button.addEventListener('click', () => {
            selectQuestion(q.id);
            
            document.querySelectorAll('#questionTabs button').forEach(btn => {
                btn.classList.remove('bg-blue-600', 'text-white');
                btn.classList.add('bg-white');
            });
            button.classList.add('bg-blue-600', 'text-white');
            button.classList.remove('bg-white');
        });
        
        tabsContainer.appendChild(button);
    });
    
    if (questions.length > 0) {
        selectQuestion(questions[0].id);
    }
}

function selectQuestion(questionId) {
    currentQuestionId = questionId;
    const question = questions.find(q => q.id === questionId);
    
    document.getElementById('questionTitle').textContent = question.title;
    document.getElementById('questionDescription').textContent = question.description;
    
    if (question.is_sql) {
        document.getElementById('languageSelect').value = 'sql';
        document.getElementById('languageSelect').disabled = true;
    } else {
        document.getElementById('languageSelect').disabled = false;
    }
    
    editor.setValue('', -1);
}

function initializeEditor() {
    editor = ace.edit('editor');
    editor.setTheme('ace/theme/monokai');
    editor.session.setMode('ace/mode/python');
    editor.setOptions({
        fontSize: '14px',
        enableBasicAutocompletion: true,
        enableLiveAutocompletion: true
    });
    
    document.getElementById('languageSelect').addEventListener('change', (e) => {
        const langMap = {
            'python': 'python',
            'c': 'c_cpp',
            'cpp': 'c_cpp',
            'java': 'java',
            'sql': 'sql'
        };
        editor.session.setMode(`ace/mode/${langMap[e.target.value]}`);
    });
}

document.getElementById('runBtn').addEventListener('click', async () => {
    const code = editor.getValue();
    const language = document.getElementById('languageSelect').value;
    
    if (!code.trim()) {
        alert('Please write some code first!');
        return;
    }
    
    document.getElementById('output').textContent = 'Running...';
    document.getElementById('errorOutput').classList.add('hidden');
    
    try {
        const response = await fetch('/api/coding/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                language: language,
                question_id: currentQuestionId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('output').textContent = data.output || 'No output';
            
            if (data.error) {
                document.getElementById('errorOutput').textContent = data.error;
                document.getElementById('errorOutput').classList.remove('hidden');
            }
        } else {
            document.getElementById('errorOutput').textContent = data.error || 'Execution failed';
            document.getElementById('errorOutput').classList.remove('hidden');
        }
    } catch (error) {
        document.getElementById('errorOutput').textContent = 'Error: ' + error.message;
        document.getElementById('errorOutput').classList.remove('hidden');
    }
});

document.getElementById('submitCodeBtn').addEventListener('click', async () => {
    const code = editor.getValue();
    const language = document.getElementById('languageSelect').value;
    const output = document.getElementById('output').textContent;
    const error = document.getElementById('errorOutput').textContent;
    
    if (!code.trim()) {
        alert('Please write some code before submitting!');
        return;
    }
    
    if (!confirm('Submit this solution? You can still submit other questions.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/coding/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: currentQuestionId,
                code: code,
                language: language,
                output: output,
                error: error
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            submittedQuestions.add(currentQuestionId);
            alert('Solution submitted successfully!');
            displayQuestionTabs();
            
            if (submittedQuestions.size >= 4) {
                if (confirm('All questions submitted! Return to dashboard?')) {
                    stopProctoring();
                    window.location.href = '/student/dashboard';
                }
            }
        }
    } catch (error) {
        alert('Failed to submit solution. Please try again.');
    }
});
