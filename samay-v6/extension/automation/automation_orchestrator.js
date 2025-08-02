// Automation Orchestrator
// Central coordinator for all AI service automation

console.log('🎼 Automation Orchestrator Loaded');

class AutomationOrchestrator {
    constructor() {
        this.automators = new Map();
        this.activeSession = null;
        this.sessionProgress = new Map();
        this.responseStorage = new Map();
        this.config = {
            maxConcurrentQueries: 4,
            defaultTimeout: 180000, // 3 minutes
            retryAttempts: 2,
            progressUpdateInterval: 1000
        };
        this.eventListeners = new Map();
        this.isInitialized = false;
    }

    async initialize() {
        console.log('🚀 Initializing Automation Orchestrator...');
        
        try {
            // Load all automation scripts dynamically
            await this.loadAutomationScripts();
            
            // Initialize individual automators
            await this.initializeAutomators();
            
            // Set up event listeners
            this.setupEventListeners();
            
            this.isInitialized = true;
            console.log('✅ Automation Orchestrator ready');
            
            return { success: true, message: 'Orchestrator initialized successfully' };
            
        } catch (error) {
            console.error('❌ Orchestrator initialization failed:', error);
            return { success: false, error: error.message };
        }
    }

    async loadAutomationScripts() {
        console.log('📂 Loading automation scripts...');
        
        const scripts = [
            'automation/chatgpt_automation.js',
            'automation/claude_automation.js', 
            'automation/gemini_automation.js',
            'automation/perplexity_automation.js'
        ];
        
        const loadPromises = scripts.map(script => this.loadScript(script));
        await Promise.all(loadPromises);
        
        console.log('✅ All automation scripts loaded');
    }

    async loadScript(scriptPath) {
        return new Promise((resolve, reject) => {
            if (typeof window === 'undefined') {
                // Running in service worker context
                importScripts(chrome.runtime.getURL(scriptPath));
                resolve();
            } else {
                // Running in page context
                const script = document.createElement('script');
                script.src = chrome.runtime.getURL(scriptPath);
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            }
        });
    }

    async initializeAutomators() {
        console.log('🔧 Initializing service automators...');
        
        const services = {
            'chatgpt': 'ChatGPTAutomator',
            'claude': 'ClaudeAutomator',
            'gemini': 'GeminiAutomator',
            'perplexity': 'PerplexityAutomator'
        };
        
        for (const [serviceName, className] of Object.entries(services)) {
            try {
                if (typeof window !== 'undefined' && window[className]) {
                    const automator = new window[className]();
                    this.automators.set(serviceName, automator);
                    console.log(`✅ ${serviceName} automator created`);
                }
            } catch (error) {
                console.warn(`⚠️ Failed to create ${serviceName} automator:`, error);
            }
        }
        
        console.log(`✅ ${this.automators.size} automators initialized`);
    }

    setupEventListeners() {
        // Listen for messages from background script
        if (typeof chrome !== 'undefined' && chrome.runtime) {
            chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
                this.handleMessage(message, sender, sendResponse);
                return true; // Keep response channel open
            });
        }
    }

    async handleMessage(message, sender, sendResponse) {
        const { action, data } = message;
        
        switch (action) {
            case 'startAutomation':
                return this.startAutomation(data, sendResponse);
            case 'stopAutomation':
                return this.stopAutomation(data, sendResponse);
            case 'getProgress':
                return this.getProgress(data, sendResponse);
            case 'getResponses':
                return this.getResponses(data, sendResponse);
            default:
                sendResponse({ success: false, error: 'Unknown action' });
        }
    }

    async startAutomation({ sessionId, query, services = [], options = {} }) {
        console.log(`🚀 Starting automation session: ${sessionId}`);
        
        if (!this.isInitialized) {
            throw new Error('Orchestrator not initialized');
        }
        
        try {
            // Set up session
            this.activeSession = sessionId;
            this.sessionProgress.set(sessionId, {
                status: 'starting',
                services: services,
                completed: [],
                failed: [],
                responses: new Map(),
                startTime: Date.now()
            });
            
            // Clear previous responses
            this.responseStorage.set(sessionId, new Map());
            
            // Start automation for each service
            const automationPromises = services.map(service => 
                this.runServiceAutomation(sessionId, service, query, options)
            );
            
            // Wait for all services to complete
            const results = await Promise.allSettled(automationPromises);
            
            // Process results
            const responses = new Map();
            const errors = [];
            
            results.forEach((result, index) => {
                const service = services[index];
                if (result.status === 'fulfilled' && result.value.success) {
                    responses.set(service, result.value.response);
                } else {
                    errors.push({
                        service: service,
                        error: result.reason || result.value?.error || 'Unknown error'
                    });
                }
            });
            
            // Update session status
            const progress = this.sessionProgress.get(sessionId);
            progress.status = 'completed';
            progress.responses = responses;
            progress.errors = errors;
            progress.endTime = Date.now();
            
            console.log(`✅ Automation session completed: ${sessionId}`);
            
            return {
                success: true,
                sessionId: sessionId,
                responses: Object.fromEntries(responses),
                errors: errors,
                duration: progress.endTime - progress.startTime
            };
            
        } catch (error) {
            console.error(`❌ Automation session failed: ${sessionId}`, error);
            
            // Update session status
            const progress = this.sessionProgress.get(sessionId);
            if (progress) {
                progress.status = 'failed';
                progress.error = error.message;
                progress.endTime = Date.now();
            }
            
            throw error;
        }
    }

    async runServiceAutomation(sessionId, serviceName, query, options) {
        console.log(`🎯 Running automation for ${serviceName}`);
        
        try {
            // Update progress
            this.updateServiceProgress(sessionId, serviceName, 'initializing');
            
            // Get automator for this service
            const automator = this.automators.get(serviceName);
            if (!automator) {
                throw new Error(`Automator not found for service: ${serviceName}`);
            }
            
            // Check if automator is on correct page
            const status = automator.getStatus();
            if (!status.onCorrectPage) {
                throw new Error(`Not on correct page for ${serviceName}`);
            }
            
            // Initialize automator if needed
            if (!status.ready) {
                this.updateServiceProgress(sessionId, serviceName, 'loading');
                const initResult = await automator.initialize();
                if (!initResult.success) {
                    throw new Error(initResult.error);
                }
            }
            
            // Submit query
            this.updateServiceProgress(sessionId, serviceName, 'querying');
            const result = await automator.submitQuery(query, options);
            
            if (result.success) {
                this.updateServiceProgress(sessionId, serviceName, 'completed');
                
                // Store response
                const responses = this.responseStorage.get(sessionId);
                responses.set(serviceName, result.response);
                
                console.log(`✅ ${serviceName} automation completed`);
                return result;
            } else {
                this.updateServiceProgress(sessionId, serviceName, 'failed');
                throw new Error(result.error);
            }
            
        } catch (error) {
            console.error(`❌ ${serviceName} automation failed:`, error);
            this.updateServiceProgress(sessionId, serviceName, 'failed');
            throw error;
        }
    }

    updateServiceProgress(sessionId, serviceName, status) {
        const progress = this.sessionProgress.get(sessionId);
        if (progress) {
            progress[serviceName] = status;
            
            // Emit progress update event
            this.emitProgressUpdate(sessionId, progress);
        }
    }

    emitProgressUpdate(sessionId, progress) {
        // Send progress update to background script
        if (typeof chrome !== 'undefined' && chrome.runtime) {
            chrome.runtime.sendMessage({
                action: 'progressUpdate',
                sessionId: sessionId,
                progress: progress
            });
        }
        
        // Emit custom event for page listeners
        if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('samayProgressUpdate', {
                detail: { sessionId, progress }
            }));
        }
    }

    async stopAutomation(sessionId) {
        console.log(`🛑 Stopping automation session: ${sessionId}`);
        
        try {
            // Stop all active automators
            for (const [serviceName, automator] of this.automators) {
                try {
                    await automator.emergencyStop();
                } catch (error) {
                    console.warn(`⚠️ Failed to stop ${serviceName}:`, error);
                }
            }
            
            // Update session status
            const progress = this.sessionProgress.get(sessionId);
            if (progress) {
                progress.status = 'stopped';
                progress.endTime = Date.now();
            }
            
            // Clear active session
            if (this.activeSession === sessionId) {
                this.activeSession = null;
            }
            
            console.log(`✅ Automation session stopped: ${sessionId}`);
            return { success: true, message: 'Automation stopped' };
            
        } catch (error) {
            console.error(`❌ Failed to stop automation: ${sessionId}`, error);
            return { success: false, error: error.message };
        }
    }

    getProgress(sessionId) {
        const progress = this.sessionProgress.get(sessionId);
        if (!progress) {
            return { success: false, error: 'Session not found' };
        }
        
        return {
            success: true,
            sessionId: sessionId,
            progress: progress
        };
    }

    getResponses(sessionId) {
        const responses = this.responseStorage.get(sessionId);
        if (!responses) {
            return { success: false, error: 'Session responses not found' };
        }
        
        return {
            success: true,
            sessionId: sessionId,
            responses: Object.fromEntries(responses)
        };
    }

    // Get current automation status
    getStatus() {
        return {
            initialized: this.isInitialized,
            activeSession: this.activeSession,
            availableServices: Array.from(this.automators.keys()),
            activeSessions: Array.from(this.sessionProgress.keys()),
            timestamp: new Date().toISOString()
        };
    }

    // Clean up old sessions
    cleanupSessions(maxAge = 3600000) { // 1 hour
        const now = Date.now();
        for (const [sessionId, progress] of this.sessionProgress) {
            if (progress.endTime && (now - progress.endTime) > maxAge) {
                this.sessionProgress.delete(sessionId);
                this.responseStorage.delete(sessionId);
                console.log(`🧹 Cleaned up old session: ${sessionId}`);
            }
        }
    }

    // Validate service availability
    async validateServices(services) {
        const results = {};
        
        for (const service of services) {
            const automator = this.automators.get(service);
            if (automator) {
                const status = automator.getStatus();
                results[service] = {
                    available: true,
                    ready: status.ready,
                    onCorrectPage: status.onCorrectPage
                };
            } else {
                results[service] = {
                    available: false,
                    error: 'Automator not found'
                };
            }
        }
        
        return results;
    }
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.AutomationOrchestrator = AutomationOrchestrator;
} else if (typeof self !== 'undefined') {
    self.AutomationOrchestrator = AutomationOrchestrator;
}

console.log('✅ Automation Orchestrator Ready');