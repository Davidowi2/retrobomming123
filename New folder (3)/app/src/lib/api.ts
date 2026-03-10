const API_BASE_URL = 'http://localhost:8000';

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.detail || error.error || 'Request failed');
    }

    return response.json();
  }

  // Auth
  async register(data: {
    email: string;
    phone: string;
    password: string;
    full_name: string;
    country?: string;
    state?: string;
  }) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async login(email: string, password: string) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async verifyOTP(phone: string, otp: string) {
    return this.request('/api/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ phone, otp }),
    });
  }

  async getMe() {
    return this.request('/api/auth/me');
  }

  // Skills
  async getSkillHeaders() {
    return this.request('/api/headers');
  }

  async addUserSkills(jobTypeIds: string[]) {
    return this.request('/api/user/skills', {
      method: 'POST',
      body: JSON.stringify({ job_type_ids: jobTypeIds }),
    });
  }

  async getUserSkills() {
    return this.request('/api/user/skills');
  }

  // Simulations
  async startSimulation(jobTypeId: string, level: string) {
    return this.request('/api/simulations/start', {
      method: 'POST',
      body: JSON.stringify({ job_type_id: jobTypeId, level }),
    });
  }

  async submitAnswer(sessionId: string, questionId: string, answer: string, timeSpentSeconds: number) {
    return this.request(`/api/simulations/${sessionId}/answer`, {
      method: 'POST',
      body: JSON.stringify({
        question_id: questionId,
        answer,
        time_spent_seconds: timeSpentSeconds,
      }),
    });
  }

  async submitMiniTask(sessionId: string, content?: string, file?: File) {
    const formData = new FormData();
    if (content) formData.append('submission_content', content);
    if (file) formData.append('file', file);

    return fetch(`${API_BASE_URL}/api/simulations/${sessionId}/mini-task`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
      body: formData,
    }).then(res => res.json());
  }

  async getSimulationResults(sessionId: string) {
    return this.request(`/api/simulations/${sessionId}/results`);
  }

  async sessionHeartbeat(sessionId: string) {
    return this.request(`/api/simulations/${sessionId}/heartbeat`, {
      method: 'POST',
    });
  }
}

export const api = new ApiClient();
