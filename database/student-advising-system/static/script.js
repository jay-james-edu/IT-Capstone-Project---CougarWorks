let students = [];
let advisors = [];
let progress = [];

document.addEventListener('DOMContentLoaded', async () => {
    await checkConnection();
    await loadAdvisors();
    await loadStudents();
    await loadProgress();
});

// Check connection with Atlas
async function checkConnection() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        const statusEl = document.querySelector('.status-indicator');
        const statusTextEl = document.getElementById('connectionStatus');
        
        if (data.status === 'connected') {
            statusEl.className = 'status-indicator connected';
            statusTextEl.innerHTML = '<span class="status-indicator connected"></span> Connected to MongoDB Atlas';
            loadDatabaseInfo();
        } else {
            statusEl.className = 'status-indicator disconnected';
            statusTextEl.innerHTML = '<span class="status-indicator disconnected"></span> Connection failed';
        }
    } catch (error) {
        console.error('Connection check failed:', error);
        document.querySelector('.status-indicator').className = 'status-indicator disconnected';
        document.getElementById('connectionStatus').innerHTML = 
            '<span class="status-indicator disconnected"></span> Cannot connect to server';
    }
}

// Load database info
async function loadDatabaseInfo() {
    try {
        const response = await fetch('/api/info');
        const info = await response.json();
        console.log('Database info:', info);
    } catch (error) {
        console.error('Error loading db info:', error);
    }
}

// Load department stats
async function loadDepartmentStats() {
    try {
        const response = await fetch('/api/department-stats');
        const stats = await response.json();
        
        const statsHtml = `
            <div class="stat-card">
                <div class="stat-value">${stats.overview[0]?.totalStudents || 0}</div>
                <div class="stat-label">Total Students</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${(stats.overview[0]?.averageGPA || 0).toFixed(2)}</div>
                <div class="stat-label">Average GPA</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.overview[0]?.honorRoll || 0}</div>
                <div class="stat-label">Honor Roll</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.byStanding?.length || 0}</div>
                <div class="stat-label">Class Levels</div>
            </div>
        `;
        
        document.getElementById('departmentStats').innerHTML = statsHtml;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load students
async function loadStudents() {
    const studentGrid = document.getElementById('studentGrid');
    studentGrid.innerHTML = '<div class="loading">Loading students...</div>';
    
    try {
        const response = await fetch('/api/students');
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error ${response.status}`);
        }
        
        students = await response.json();
        console.log(`✅ Loaded ${students.length} students`);
        
        if (students.length === 0) {
            studentGrid.innerHTML = '<div class="loading">No students found in database</div>';
        } else {
            displayStudents(students);
        }
        
        loadDepartmentStats();
        
    } catch (error) {
        console.error('Error loading students:', error);
        studentGrid.innerHTML = `
            <div class="error-message">
                <h3>❌ Error Loading Students</h3>
                <p>${error.message}</p>
                <button onclick="loadStudents()" class="retry-button">Retry</button>
            </div>
        `;
    }
}

// Display students
function displayStudents(studentsToShow) {
    const grid = document.getElementById('studentGrid');
    
    if (studentsToShow.length === 0) {
        grid.innerHTML = '<div class="loading">No students found</div>';
        return;
    }
    
    grid.innerHTML = studentsToShow.map(student => {
        let advisorDisplay = 'Unknown';
        if (student.advisorId) {
            const advisor = advisors.find(a => a.advisorId === student.advisorId);
            if (advisor) {
                advisorDisplay = `${advisor.personalInfo?.firstName || ''} ${advisor.personalInfo?.lastName || ''}`.trim();
            } else {
                advisorDisplay = `ID: ${student.advisorId}`;
            }
        }
        
        return `
            <div class="student-card" onclick="viewStudent('${student.studentId}')">
                <div class="student-name">${student.personalInfo?.firstName || ''} ${student.personalInfo?.lastName || ''}</div>
                <div class="student-id">ID: ${student.studentId || ''}</div>
                <div class="student-email">${student.personalInfo?.email || ''}</div>
                <div class="student-badges">
                    <span class="badge standing">${student.academicInfo?.standing || 'N/A'}</span>
                    <span class="badge gpa">GPA: ${student.academicInfo?.gpa || 0}</span>
                    <span class="badge credits">${student.academicInfo?.creditsEarned || 0} credits</span>
                </div>
                <div class="student-footer">
                    <span class="advisor-tag">Advisor: ${advisorDisplay}</span>
                    <span class="status-badge ${(student.enrollmentStatus || '').toLowerCase()}">${student.enrollmentStatus || 'Unknown'}</span>
                </div>
            </div>
        `;
    }).join('');
}

// Get advisor name by ID
function getAdvisorName(advisorId) {
    if (!advisorId) return 'No Advisor Assigned';
    
    if (!advisors || advisors.length === 0) {
        return 'Loading advisor...';
    }
    
    const advisor = advisors.find(a => a.advisorId === advisorId);
    if (advisor) {
        return `${advisor.personalInfo?.firstName || ''} ${advisor.personalInfo?.lastName || ''}`.trim() || advisorId;
    }
    
    loadAdvisors();
    return `Advisor: ${advisorId}`;
}

// Load advisors
async function loadAdvisors() {
    const advisorGrid = document.getElementById('advisorGrid');
    advisorGrid.innerHTML = '<div class="loading">Loading advisors...</div>';
    
    try {
        console.log("📡 Fetching advisors...");
        const response = await fetch('/api/advisors');
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error ${response.status}`);
        }
        
        advisors = await response.json();
        console.log(`✅ Loaded ${advisors.length} advisors`);
        
        if (advisors.length === 0) {
            advisorGrid.innerHTML = '<div class="loading">No advisors found in database</div>';
        } else {
            displayAdvisors(advisors);
        }
        
    } catch (error) {
        console.error('❌ Error loading advisors:', error);
        advisorGrid.innerHTML = `
            <div class="error-message">
                <h3>❌ Error Loading Advisors</h3>
                <p>${error.message}</p>
                <button onclick="loadAdvisors()" class="retry-button">Retry</button>
                <button onclick="showAdvisorDebug()" class="debug-button">Debug</button>
            </div>
        `;
    }
}

// Display advisors
function displayAdvisors(advisorsToShow) {
    const grid = document.getElementById('advisorGrid');
    
    if (!advisorsToShow || advisorsToShow.length === 0) {
        grid.innerHTML = '<div class="loading">No advisors to display</div>';
        return;
    }
    
    grid.innerHTML = advisorsToShow.map(advisor => {
        const firstName = advisor.personalInfo?.firstName || '';
        const lastName = advisor.personalInfo?.lastName || '';
        const advisorName = `${firstName} ${lastName}`.trim() || 'Unknown Name';
        const email = advisor.personalInfo?.email || 'No email';
        const department = advisor.department || 'Computer Science';
        const studentList = advisor.students || [];
        
        return `
            <div class="advisor-card">
                <div class="advisor-name">${advisorName}</div>
                <div class="advisor-dept">${department}</div>
                <div class="advisor-stats">
                    <div><strong>Email:</strong> ${email}</div>
                    <div><strong>Advisor ID:</strong> ${advisor.advisorId || 'N/A'}</div>
                    <div><strong>Students:</strong> ${studentList.length}</div>
                    <div style="margin-top: 10px;">
                        ${studentList.map(studentId => {
                            const student = students.find(s => s.studentId === studentId);
                            const studentName = student ? 
                                `${student.personalInfo?.firstName || ''} ${student.personalInfo?.lastName || ''}`.trim() : 
                                studentId;
                            return `<span class="student-chip">${studentName}</span>`;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Debug function for advisors
async function showAdvisorDebug() {
    try {
        const response = await fetch('/api/advisors');
        const data = await response.json();
        alert(JSON.stringify(data, null, 2));
    } catch (error) {
        alert('Debug error: ' + error.message);
    }
}

// Load academic progress
async function loadProgress() {
    try {
        const response = await fetch('/api/academic-progress');
        progress = await response.json();
        displayProgress(progress);
    } catch (error) {
        console.error('Error loading progress:', error);
        document.getElementById('progressList').innerHTML = 
            '<div class="loading">Error loading progress</div>';
    }
}

// Display academic progress
function displayProgress(progressToShow) {
    const list = document.getElementById('progressList');
    
    if (progressToShow.length === 0) {
        list.innerHTML = '<div class="loading">No progress records found</div>';
        return;
    }
    
    list.innerHTML = progressToShow.map(p => {
        const student = students.find(s => s.studentId === p.studentId);
        const percent = Math.round((p.degreeProgress?.totalCreditsEarned || 0) / 120 * 100);
        
        return `
            <div class="progress-item">
                <div class="progress-header">
                    <h3>${student ? `${student.personalInfo?.firstName || ''} ${student.personalInfo?.lastName || ''}` : p.studentId}</h3>
                    <span class="semester">${p.currentSemester || ''}</span>
                </div>
                <div>Catalog Year: ${p.catalogYear || ''}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percent}%"></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                    <span>${p.degreeProgress?.totalCreditsEarned || 0} credits earned</span>
                    <span>${p.degreeProgress?.remainingCredits || 0} credits remaining</span>
                </div>
                <div><strong>Current Courses:</strong></div>
                <div style="margin-top: 10px;">
                    ${(p.degreeProgress?.currentSemesterCourses || []).map(course => 
                        `<span class="course-tag">${course.code} - ${course.name} (${course.credits} cr)</span>`
                    ).join('')}
                </div>
            </div>
        `;
    }).join('');
}

// View single student
async function viewStudent(studentId) {
    try {
        const response = await fetch(`/api/students/${studentId}`);
        const student = await response.json();
        
        const modalContent = document.getElementById('modalContent');
        
        if (!student || !student.studentId) {
            modalContent.innerHTML = '<div class="loading">Student not found</div>';
        } else {
            modalContent.innerHTML = `
                <h2 style="margin-bottom: 20px; color: #333;">${student.name || ''}</h2>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
                        <h3 style="color: #667eea; margin-bottom: 10px;">Student Info</h3>
                        <p><strong>ID:</strong> ${student.studentId || ''}</p>
                        <p><strong>Email:</strong> ${student.email || ''}</p>
                        <p><strong>Phone:</strong> ${student.phone || ''}</p>
                        <p><strong>Status:</strong> ${student.enrollmentStatus || ''}</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
                        <h3 style="color: #764ba2; margin-bottom: 10px;">Academic Info</h3>
                        <p><strong>Major:</strong> ${student.major || ''}</p>
                        <p><strong>Standing:</strong> ${student.standing || ''}</p>
                        <p><strong>GPA:</strong> ${student.gpa || 0}</p>
                        <p><strong>Expected Graduation:</strong> ${student.expectedGraduation || ''}</p>
                    </div>
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #333; margin-bottom: 10px;">Advisor</h3>
                    <p><strong>Name:</strong> ${student.advisor?.name || ''}</p>
                    <p><strong>Email:</strong> ${student.advisor?.email || ''}</p>
                    <p><strong>Department:</strong> ${student.advisor?.department || ''}</p>
                </div>
                
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white;">
                    <h3 style="margin-bottom: 15px;">Current Semester: ${student.currentSemester || ''}</h3>
                    <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                        <div><strong>Credits Earned:</strong> ${student.totalCreditsEarned || 0}/120</div>
                        <div><strong>Remaining:</strong> ${student.remainingCredits || 0}</div>
                    </div>
                    <div><strong>Current Courses:</strong></div>
                    <div style="margin-top: 10px;">
                        ${(student.currentCourses || []).map(course => `
                            <span style="background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 15px; margin: 3px; display: inline-block;">
                                ${course.code} - ${course.name}
                            </span>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        document.getElementById('studentModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading student details:', error);
        document.getElementById('modalContent').innerHTML = 
            '<div class="loading">Error loading student details</div>';
        document.getElementById('studentModal').style.display = 'block';
    }
}

// Close modal
function closeModal() {
    document.getElementById('studentModal').style.display = 'none';
}

// Switch tabs
function switchTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName + 'Tab').classList.add('active');
}

// Search students
function searchStudents() {
    const searchTerm = document.getElementById('studentSearch').value.toLowerCase();
    const standing = document.getElementById('standingFilter').value;
    
    const filtered = students.filter(student => {
        const matchesSearch = 
            student.studentId?.toLowerCase().includes(searchTerm) ||
            student.personalInfo?.firstName?.toLowerCase().includes(searchTerm) ||
            student.personalInfo?.lastName?.toLowerCase().includes(searchTerm) ||
            student.personalInfo?.email?.toLowerCase().includes(searchTerm);
        
        const matchesStanding = !standing || student.academicInfo?.standing === standing;
        
        return matchesSearch && matchesStanding;
    });
    
    displayStudents(filtered);
}

// Filter students
function filterStudents() {
    searchStudents();
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('studentModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}