/* ═══════════════════════════════════════════════════════════════
   CODEVERSE — API Client Engine (api.js)
   Communicates directly with FastAPI backend services
   ═══════════════════════════════════════════════════════════════ */

const API = (() => {
  const BASE_URL = window.location.origin;

  function getStudentId() {
    return localStorage.getItem('codeverse_user_id') || 'STU2024001';
  }

  function getRole() {
    return localStorage.getItem('codeverse_role') || 'student';
  }

  async function request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error (${response.status})`);
      }
      return await response.json();
    } catch (err) {
      console.warn(`[API] Endpoint call failed: ${endpoint}`, err);
      throw err;
    }
  }

  // ── Auth API ──
  async function login(userId, role = 'student') {
    const data = await request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, role })
    });
    if (data.success) {
      localStorage.setItem('codeverse_user_id', data.user_id);
      localStorage.setItem('codeverse_user_name', data.full_name);
      localStorage.setItem('codeverse_role', data.role);
    }
    return data;
  }

  // ── Problems API ──
  async function getProblems() {
    const studentId = getStudentId();
    return await request(`/api/problems?student_id=${studentId}`);
  }

  async function getProblem(id) {
    const studentId = getStudentId();
    return await request(`/api/problems/${id}?student_id=${studentId}`);
  }

  // ── Compiler & Submission API ──
  async function runCode(code, problemId = null, inputData = null, mode = 'practice') {
    return await request('/api/compiler/run', {
      method: 'POST',
      body: JSON.stringify({
        code,
        problem_id: problemId,
        input_data: inputData,
        mode
      })
    });
  }

  async function submitSolution(problemId, code, mode = 'practice') {
    const studentId = getStudentId();
    return await request('/api/submissions', {
      method: 'POST',
      body: JSON.stringify({
        student_id: studentId,
        problem_id: problemId,
        code,
        mode
      })
    });
  }

  async function submitFeedback(problemId, rating, comment = '') {
    const studentId = getStudentId();
    return await request('/api/feedback', {
      method: 'POST',
      body: JSON.stringify({
        student_id: studentId,
        problem_id: problemId,
        difficulty_rating: rating,
        comment
      })
    });
  }

  // ── Write-Ups API ──
  async function getWriteups() {
    const studentId = getStudentId();
    return await request(`/api/writeups?student_id=${studentId}`);
  }

  async function startWriteup(id) {
    const studentId = getStudentId();
    return await request(`/api/writeups/${id}/start`, {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId })
    });
  }

  async function autosaveWriteup(id, codeMap) {
    const studentId = getStudentId();
    return await request(`/api/writeups/${id}/autosave`, {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId, code_map: codeMap })
    });
  }

  async function submitWriteup(id, codeMap) {
    const studentId = getStudentId();
    return await request(`/api/writeups/${id}/submit`, {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId, code_map: codeMap })
    });
  }

  // ── Exams API ──
  async function getExams() {
    const studentId = getStudentId();
    return await request(`/api/exams?student_id=${studentId}`);
  }

  async function startExam(id) {
    const studentId = getStudentId();
    return await request(`/api/exams/${id}/start`, {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId })
    });
  }

  async function autosaveExam(id, codeMap) {
    const studentId = getStudentId();
    return await request(`/api/exams/${id}/autosave`, {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId, code_map: codeMap })
    });
  }

  async function submitExam(id, codeMap) {
    const studentId = getStudentId();
    return await request(`/api/exams/${id}/submit`, {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId, code_map: codeMap })
    });
  }

  // ── Student Progress API ──
  async function getStudentProgress() {
    const studentId = getStudentId();
    return await request(`/api/student/progress?student_id=${studentId}`);
  }

  // ── Faculty Console API ──
  async function getFacultyDashboard() {
    return await request('/api/faculty/dashboard');
  }

  async function getFacultyStudents() {
    return await request('/api/faculty/students');
  }

  async function createWriteup(writeupData) {
    return await request('/api/faculty/writeups', {
      method: 'POST',
      body: JSON.stringify(writeupData)
    });
  }

  async function createExam(examData) {
    return await request('/api/faculty/exams', {
      method: 'POST',
      body: JSON.stringify(examData)
    });
  }

  async function getSuspiciousSubmissions() {
    return await request('/api/faculty/suspicious_submissions');
  }

  async function reviewSubmission(analysisId, status = 'approved') {
    return await request(`/api/faculty/review_submission/${analysisId}?status=${status}`, {
      method: 'POST'
    });
  }

  return {
    getStudentId,
    getRole,
    login,
    getProblems,
    getProblem,
    runCode,
    submitSolution,
    submitFeedback,
    getWriteups,
    startWriteup,
    autosaveWriteup,
    submitWriteup,
    getExams,
    startExam,
    autosaveExam,
    submitExam,
    getStudentProgress,
    getFacultyDashboard,
    getFacultyStudents,
    createWriteup,
    createExam,
    getSuspiciousSubmissions,
    reviewSubmission
  };
})();
