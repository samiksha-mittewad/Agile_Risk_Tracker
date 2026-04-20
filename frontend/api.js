// ===========================================
// API SERVICE LAYER
// ===========================================
// This file handles ALL communication with the FastAPI backend
// Adjust endpoint URLs to match your backend routes
// ===========================================

const API = {
    /**
     * Generic HTTP request handler
     */
    request: async (endpoint, options = {}) => {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaultOptions, ...options };

        try {
            log(`API Request: ${options.method || 'GET'} ${url}`);
            
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            log(`API Response:`, data);
            return data;

        } catch (error) {
            logError(`API Error (${endpoint}):`, error);
            throw error;
        }
    },

    /**
     * GET request
     */
    get: async (endpoint) => {
        return API.request(endpoint, {
            method: 'GET',
        });
    },

    /**
     * POST request
     */
    post: async (endpoint, data) => {
        return API.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    /**
     * PUT request
     */
    put: async (endpoint, data) => {
        return API.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    /**
     * DELETE request
     */
    delete: async (endpoint) => {
        return API.request(endpoint, {
            method: 'DELETE',
        });
    },

    /**
     * File upload handler
     */
    upload: async (endpoint, file, fieldName = 'file') => {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const formData = new FormData();
        formData.append(fieldName, file);

        try {
            log(`API Upload: POST ${url}`);
            
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                // Don't set Content-Type header - browser will set it with boundary
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            log(`API Upload Response:`, data);
            return data;

        } catch (error) {
            logError(`API Upload Error (${endpoint}):`, error);
            throw error;
        }
    },

    // ===========================================
    // RISK ENDPOINTS
    // ===========================================
    // 🔧 ADJUST THESE TO MATCH YOUR BACKEND ROUTES
    // ===========================================

    risks: {
        /**
         * Get all risks
         * Backend route example: GET /api/risks or GET /risks
         */
        getAll: async () => {
            return API.get('/api/risks');
        },

        /**
         * Get risk by ID
         * Backend route example: GET /api/risks/{risk_id}
         */
        getById: async (id) => {
            return API.get(`/api/risks/${id}`);
        },

        /**
         * Create new risk
         * Backend route example: POST /api/risks
         * Expected payload: { title, description, category, impact, probability }
         */
        create: async (riskData) => {
            return API.post('/api/risks', riskData);
        },

        /**
         * Update risk
         * Backend route example: PUT /api/risks/{risk_id}
         */
        update: async (id, riskData) => {
            return API.put(`/api/risks/${id}`, riskData);
        },

        /**
         * Delete risk
         * Backend route example: DELETE /api/risks/{risk_id}
         */
        delete: async (id) => {
            return API.delete(`/api/risks/${id}`);
        },

        /**
         * Upload CSV file with risks
         * Backend route example: POST /api/risks/upload
         */
        uploadCSV: async (file) => {
            return API.upload('/api/risks/upload', file);
        },

        /**
         * Get ML prediction for a risk
         * Backend route example: GET /api/risks/{risk_id}/predict
         * Expected response: { ml_score, historical_score, final_score, severity, confidence }
         */
        predict: async (id) => {
            return API.get(`/api/risks/${id}/predict`);
        },
    },

    // ===========================================
    // DASHBOARD ENDPOINTS
    // ===========================================

    dashboard: {
        /**
         * Get dashboard statistics
         * Backend route example: GET /api/dashboard/stats
         * Expected response: { total_risks, critical_risks, average_score, resolved }
         */
        getStats: async () => {
            return API.get('/api/dashboard/stats');
        },

        /**
         * Get risk trends over time
         * Backend route example: GET /api/dashboard/trends
         * Expected response: { labels: [...], scores: [...] }
         */
        getTrends: async () => {
            return API.get('/api/dashboard/trends');
        },

        /**
         * Get risk distribution by category
         * Backend route example: GET /api/dashboard/distribution
         */
        getDistribution: async () => {
            return API.get('/api/dashboard/distribution');
        },
    },

    // ===========================================
    // AUTOMATION/ALERTS ENDPOINTS
    // ===========================================

    automation: {
        /**
         * Get all alerts
         * Backend route example: GET /api/alerts
         */
        getAlerts: async () => {
            return API.get('/api/alerts');
        },

        /**
         * Configure automation settings
         * Backend route example: POST /api/automation/configure
         * Expected payload: { threshold, enabled, channels: {...} }
         */
        configure: async (config) => {
            return API.post('/api/automation/configure', config);
        },

        /**
         * Get automation settings
         * Backend route example: GET /api/automation/settings
         */
        getSettings: async () => {
            return API.get('/api/automation/settings');
        },
    },

    // ===========================================
    // ANALYTICS ENDPOINTS
    // ===========================================

    analytics: {
        /**
         * Get risks by category
         * Backend route example: GET /api/analytics/by-category
         */
        getByCategory: async () => {
            return API.get('/api/analytics/by-category');
        },

        /**
         * Get resolution rate
         * Backend route example: GET /api/analytics/resolution-rate
         */
        getResolutionRate: async () => {
            return API.get('/api/analytics/resolution-rate');
        },

        /**
         * Get risk heatmap data
         * Backend route example: GET /api/analytics/heatmap
         */
        getHeatmap: async () => {
            return API.get('/api/analytics/heatmap');
        },
    },

    // ===========================================
    // SPRINT ENDPOINTS (Optional)
    // ===========================================

    sprints: {
        /**
         * Get current sprint
         * Backend route example: GET /api/sprints/current
         */
        getCurrent: async () => {
            return API.get('/api/sprints/current');
        },

        /**
         * Get all sprints
         * Backend route example: GET /api/sprints
         */
        getAll: async () => {
            return API.get('/api/sprints');
        },
    },

    // ===========================================
    // HEALTH CHECK
    // ===========================================

    /**
     * Check if backend is healthy
     * Backend route example: GET /health or GET /api/health
     */
    healthCheck: async () => {
        try {
            return await API.get('/health');
        } catch (error) {
            logError('Backend health check failed:', error);
            return { status: 'unhealthy', error: error.message };
        }
    },
};

// Test backend connection on load
window.addEventListener('load', async () => {
    log('Testing backend connection...');
    try {
        const health = await API.healthCheck();
        if (health.status === 'healthy' || health.status === 'ok') {
            log('✅ Backend connected successfully!');
        } else {
            logError('⚠️ Backend returned unhealthy status:', health);
        }
    } catch (error) {
        logError('❌ Cannot connect to backend. Make sure your FastAPI server is running on', CONFIG.API_BASE_URL);
        logError('Start backend with: uvicorn main:app --reload');
    }
});
