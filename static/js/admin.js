let studentsData = [];
let chart = null;

window.addEventListener('load', async () => {
    await loadStudents();
    await loadAnalytics();
});

document.getElementById('departmentFilter').addEventListener('change', async (e) => {
    await loadStudents(e.target.value);
});

async function loadStudents(department = '') {
    try {
        const url = department ? `/api/admin/students?department=${department}` : '/api/admin/students';
        const response = await fetch(url);
        const data = await response.json();
        
        studentsData = data.students;
        displayStudents();
    } catch (error) {
        console.error('Error loading students:', error);
    }
}

function displayStudents() {
    const tbody = document.getElementById('studentsList');
    tbody.innerHTML = '';
    
    if (studentsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4">No students found</td></tr>';
        return;
    }
    
    studentsData.forEach(student => {
        const row = document.createElement('tr');
        row.className = 'border-b hover:bg-gray-50';
        row.innerHTML = `
            <td class="px-4 py-3">${student.name}</td>
            <td class="px-4 py-3">${student.email}</td>
            <td class="px-4 py-3">
                <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">${student.department}</span>
            </td>
            <td class="px-4 py-3 text-center font-semibold">${student.aptitude_score}</td>
            <td class="px-4 py-3 text-center font-semibold">${student.round2_score}</td>
            <td class="px-4 py-3 text-center font-semibold">${student.interview_score}</td>
            <td class="px-4 py-3 text-center">
                <span class="px-2 py-1 ${student.flagged ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'} rounded-full text-sm">
                    ${student.violations}
                </span>
            </td>
            <td class="px-4 py-3 text-center">
                <button onclick="viewStudent(${student.id})" class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm mr-1">
                    <i class="fas fa-eye"></i> View
                </button>
                <a href="/api/admin/export/${student.id}" class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm inline-block">
                    <i class="fas fa-download"></i> PDF
                </a>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function viewStudent(studentId) {
    try {
        const response = await fetch(`/api/admin/student/${studentId}`);
        const data = await response.json();
        
        let detailsHTML = `
            <div class="space-y-6">
                <div class="border-b pb-4">
                    <h3 class="text-xl font-bold mb-2">${data.student.name}</h3>
                    <p class="text-gray-600">${data.student.email} | ${data.student.department}</p>
                </div>
        `;
        
        if (data.aptitude) {
            detailsHTML += `
                <div>
                    <h4 class="text-lg font-bold mb-2">Round 1 - Aptitude Test</h4>
                    <p>Score: <strong>${data.aptitude.score}/${data.aptitude.total}</strong></p>
                    <p>Time Taken: ${Math.floor(data.aptitude.time_taken / 60)} minutes</p>
                </div>
            `;
        }
        
        if (data.coding_tests && data.coding_tests.length > 0) {
            detailsHTML += `
                <div>
                    <h4 class="text-lg font-bold mb-2">Round 2 - Coding Tests</h4>
            `;
            data.coding_tests.forEach((test, i) => {
                detailsHTML += `
                    <div class="mb-4 p-4 bg-gray-50 rounded-lg">
                        <h5 class="font-bold mb-2">${i + 1}. ${test.question_title}</h5>
                        <p class="mb-2">Language: <strong>${test.language}</strong> | Score: <strong>${test.score}</strong></p>
                        <div class="bg-white p-3 rounded border overflow-x-auto">
                            <pre class="text-sm">${test.code || 'No code submitted'}</pre>
                        </div>
                        ${test.output ? `<p class="mt-2 text-sm text-gray-600">Output: ${test.output}</p>` : ''}
                        ${test.error ? `<p class="mt-2 text-sm text-red-600">Error: ${test.error}</p>` : ''}
                    </div>
                `;
            });
            detailsHTML += `</div>`;
        }
        
        if (data.non_technical_tests && data.non_technical_tests.length > 0) {
            detailsHTML += `
                <div>
                    <h4 class="text-lg font-bold mb-2">Round 2 - Non-Technical Tests</h4>
            `;
            data.non_technical_tests.forEach((test, i) => {
                detailsHTML += `
                    <div class="mb-4 p-4 bg-gray-50 rounded-lg">
                        <h5 class="font-bold mb-2">${i + 1}. ${test.question}</h5>
                        <p class="mb-2">AI Score: <strong>${test.score}/100</strong></p>
                        <p class="mb-2 italic">"${test.answer}"</p>
                        <p class="text-sm text-gray-700"><strong>AI Feedback:</strong> ${test.feedback}</p>
                    </div>
                `;
            });
            detailsHTML += `</div>`;
        }
        
        if (data.interview) {
            detailsHTML += `
                <div>
                    <h4 class="text-lg font-bold mb-2">Round 3 - Mock Interview</h4>
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div class="text-center p-3 bg-blue-50 rounded">
                            <p class="text-sm text-gray-600">Communication</p>
                            <p class="text-2xl font-bold text-blue-600">${data.interview.communication}</p>
                        </div>
                        <div class="text-center p-3 bg-green-50 rounded">
                            <p class="text-sm text-gray-600">Confidence</p>
                            <p class="text-2xl font-bold text-green-600">${data.interview.confidence}</p>
                        </div>
                        <div class="text-center p-3 bg-purple-50 rounded">
                            <p class="text-sm text-gray-600">Clarity</p>
                            <p class="text-2xl font-bold text-purple-600">${data.interview.clarity}</p>
                        </div>
                        <div class="text-center p-3 bg-orange-50 rounded">
                            <p class="text-sm text-gray-600">Relevance</p>
                            <p class="text-2xl font-bold text-orange-600">${data.interview.relevance}</p>
                        </div>
                    </div>
                    <div class="p-4 bg-gray-50 rounded-lg">
                        <h5 class="font-bold mb-2">Transcript:</h5>
                        <p class="text-sm text-gray-700">${data.interview.transcript}</p>
                    </div>
                    <div class="mt-3 p-4 bg-blue-50 rounded-lg">
                        <p class="text-sm"><strong>AI Feedback:</strong> ${data.interview.feedback}</p>
                    </div>
                </div>
            `;
        }
        
        if (data.violations && data.violations.length > 0) {
            detailsHTML += `
                <div>
                    <h4 class="text-lg font-bold mb-2 text-red-600">Proctoring Violations (${data.violations.length})</h4>
                    <div class="space-y-2">
            `;
            data.violations.forEach(v => {
                detailsHTML += `
                    <div class="p-3 bg-red-50 rounded text-sm">
                        <p><strong>${v.type}</strong> - ${v.round}</p>
                        <p class="text-gray-600">${new Date(v.timestamp).toLocaleString()}</p>
                    </div>
                `;
            });
            detailsHTML += `</div></div>`;
        }
        
        detailsHTML += `</div>`;
        
        document.getElementById('studentDetails').innerHTML = detailsHTML;
        document.getElementById('studentModal').classList.remove('hidden');
    } catch (error) {
        console.error('Error loading student details:', error);
        alert('Failed to load student details.');
    }
}

function closeModal() {
    document.getElementById('studentModal').classList.add('hidden');
}

async function loadAnalytics() {
    try {
        const response = await fetch('/api/admin/analytics');
        const data = await response.json();
        
        const labels = Object.keys(data);
        const aptitudeData = labels.map(dept => data[dept].avg_aptitude);
        const interviewData = labels.map(dept => data[dept].avg_interview);
        
        const ctx = document.getElementById('departmentChart').getContext('2d');
        
        if (chart) {
            chart.destroy();
        }
        
        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Avg Aptitude Score',
                        data: aptitudeData,
                        backgroundColor: 'rgba(59, 130, 246, 0.5)',
                        borderColor: 'rgb(59, 130, 246)',
                        borderWidth: 1
                    },
                    {
                        label: 'Avg Interview Score',
                        data: interviewData,
                        backgroundColor: 'rgba(16, 185, 129, 0.5)',
                        borderColor: 'rgb(16, 185, 129)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        let statsHTML = '<div class="space-y-4">';
        labels.forEach(dept => {
            statsHTML += `
                <div class="border-b pb-3">
                    <h4 class="font-bold text-lg">${dept}</h4>
                    <p class="text-sm">Students: ${data[dept].total_students}</p>
                    <p class="text-sm">Avg Aptitude: ${data[dept].avg_aptitude.toFixed(1)}</p>
                    <p class="text-sm">Avg Interview: ${data[dept].avg_interview.toFixed(1)}</p>
                </div>
            `;
        });
        statsHTML += '</div>';
        
        document.getElementById('statsDisplay').innerHTML = statsHTML;
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

window.viewStudent = viewStudent;
window.closeModal = closeModal;
