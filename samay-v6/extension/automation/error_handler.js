// Error Handler and Fallback System
// Manages errors and provides fallback mechanisms for automation

console.log('🛡️ Error Handler Loaded');

class AutomationErrorHandler {
    constructor() {
        this.errorLog = [];
        this.fallbackStrategies = new Map();
        this.retryConfig = {
            maxRetries: 3,
            baseDelay: 2000,
            maxDelay: 30000,
            exponentialBackoff: true
        };
        this.setupFallbackStrategies();
    }

    setupFallbackStrategies() {
        // Define fallback strategies for different error types
        this.fallbackStrategies.set('page_not_loaded', {
            name: 'Page Reload Strategy',
            action: 'reload_and_retry',
            maxAttempts: 2
        });
        
        this.fallbackStrategies.set('element_not_found', {
            name: 'Alternative Selector Strategy',
            action: 'try_alternative_selectors',
            maxAttempts: 3
        });
        
        this.fallbackStrategies.set('network_timeout', {
            name: 'Extended Timeout Strategy',
            action: 'extend_timeout_and_retry',
            maxAttempts: 2
        });
        
        this.fallbackStrategies.set('submission_failed', {
            name: 'Alternative Submission Strategy',
            action: 'try_keyboard_shortcut',
            maxAttempts: 2
        });
        
        this.fallbackStrategies.set('response_timeout', {
            name: 'Extended Monitoring Strategy',
            action: 'extend_monitoring_time',
            maxAttempts: 1
        });
        
        this.fallbackStrategies.set('automation_blocked', {
            name: 'Human-like Behavior Strategy',
            action: 'increase_delays_and_retry',
            maxAttempts: 2
        });
    }

    async handleError(error, context) {
        console.log(`🚨 Handling error: ${error.message}`);
        
        // Log the error
        this.logError(error, context);
        
        // Classify the error
        const errorType = this.classifyError(error, context);
        
        // Get appropriate fallback strategy
        const strategy = this.fallbackStrategies.get(errorType);
        
        if (strategy && context.attemptCount < strategy.maxAttempts) {
            console.log(`🔄 Applying fallback strategy: ${strategy.name}`);
            return await this.applyFallbackStrategy(strategy, error, context);
        } else {
            console.log(`❌ No fallback available for error type: ${errorType}`);
            return this.createFailureResponse(error, context);
        }
    }

    classifyError(error, context) {
        const errorMessage = error.message.toLowerCase();
        
        // Page loading issues
        if (errorMessage.includes('page') && 
            (errorMessage.includes('not loaded') || errorMessage.includes('not ready'))) {
            return 'page_not_loaded';
        }
        
        // Element not found issues
        if (errorMessage.includes('not found') || 
            errorMessage.includes('not interactable') ||
            errorMessage.includes('element')) {
            return 'element_not_found';
        }
        
        // Network/timeout issues
        if (errorMessage.includes('timeout') && 
            (errorMessage.includes('network') || errorMessage.includes('connection'))) {
            return 'network_timeout';
        }
        
        // Submission failures
        if (errorMessage.includes('submit') || 
            errorMessage.includes('send') ||
            errorMessage.includes('button')) {
            return 'submission_failed';
        }
        
        // Response monitoring timeouts
        if (errorMessage.includes('response timeout') ||
            errorMessage.includes('monitoring')) {
            return 'response_timeout';
        }
        
        // Automation detection/blocking
        if (errorMessage.includes('blocked') ||
            errorMessage.includes('detected') ||
            errorMessage.includes('captcha')) {
            return 'automation_blocked';
        }
        
        // Default classification
        return 'unknown_error';
    }

    async applyFallbackStrategy(strategy, error, context) {
        const { action } = strategy;
        const { automator, serviceName, query, options } = context;
        
        try {
            switch (action) {
                case 'reload_and_retry':
                    return await this.reloadAndRetry(automator, query, context);
                
                case 'try_alternative_selectors':
                    return await this.tryAlternativeSelectors(automator, query, context);
                
                case 'extend_timeout_and_retry':
                    return await this.extendTimeoutAndRetry(automator, query, context);
                
                case 'try_keyboard_shortcut':
                    return await this.tryKeyboardShortcut(automator, query, context);
                
                case 'extend_monitoring_time':
                    return await this.extendMonitoringTime(automator, query, context);
                
                case 'increase_delays_and_retry':
                    return await this.increaseDelaysAndRetry(automator, query, context);
                
                default:
                    throw new Error(`Unknown fallback action: ${action}`);
            }
        } catch (fallbackError) {
            console.error(`❌ Fallback strategy failed:`, fallbackError);
            return this.createFailureResponse(fallbackError, context);
        }
    }

    async reloadAndRetry(automator, query, context) {
        console.log('🔄 Reloading page and retrying...');
        
        // Reload the page
        window.location.reload();
        
        // Wait for page to load
        await this.waitForPageLoad(10000);
        
        // Reinitialize automator
        const initResult = await automator.initialize();
        if (!initResult.success) {
            throw new Error(`Reinitialization failed: ${initResult.error}`);
        }
        
        // Retry the query
        return await automator.submitQuery(query, context.options);
    }

    async tryAlternativeSelectors(automator, query, context) {
        console.log('🔍 Trying alternative selectors...');
        
        // Create a modified automator with alternative selectors
        const altConfig = this.getAlternativeSelectors(context.serviceName);
        if (altConfig) {
            // Temporarily modify automator config
            const originalConfig = automator.config;
            automator.config = { ...originalConfig, selectors: altConfig };
            
            try {
                return await automator.submitQuery(query, context.options);
            } finally {
                // Restore original config
                automator.config = originalConfig;
            }
        }
        
        throw new Error('No alternative selectors available');
    }

    async extendTimeoutAndRetry(automator, query, context) {
        console.log('⏱️ Extending timeout and retrying...');
        
        // Increase timeout values
        const originalConfig = automator.config;
        automator.config = {
            ...originalConfig,
            timing: {
                ...originalConfig.timing,
                response_timeout: originalConfig.timing.response_timeout * 2,
                polling_interval: originalConfig.timing.polling_interval * 1.5
            }
        };
        
        try {
            return await automator.submitQuery(query, context.options);
        } finally {
            // Restore original config
            automator.config = originalConfig;
        }
    }

    async tryKeyboardShortcut(automator, query, context) {
        console.log('⌨️ Trying keyboard shortcut submission...');
        
        // This would be implemented in the specific automator
        // For now, we'll try the standard Enter approach
        const input = document.querySelector(automator.config.selectors.input);
        if (input) {
            input.focus();
            
            // Try different keyboard combinations
            const shortcuts = [
                { key: 'Enter', ctrlKey: true },
                { key: 'Enter', metaKey: true },
                { key: 'Enter' }
            ];
            
            for (const shortcut of shortcuts) {
                const event = new KeyboardEvent('keydown', shortcut);
                input.dispatchEvent(event);
                await this.sleep(1000);
                
                // Check if submission was successful
                const loadingElement = document.querySelector(automator.config.selectors.loading_indicator);
                if (loadingElement) {
                    // Looks like it worked, continue with monitoring
                    return await automator.monitorResponse();
                }
            }
        }
        
        throw new Error('Keyboard shortcut submission failed');
    }

    async extendMonitoringTime(automator, query, context) {
        console.log('👁️ Extending monitoring time...');
        
        // Double the monitoring time
        const extendedTimeout = automator.config.timing.response_timeout * 2;
        
        // Restart monitoring with extended timeout
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            
            const checkForResponse = () => {
                try {
                    const responseArea = document.querySelector(automator.config.selectors.response_area);
                    const loadingIndicator = document.querySelector(automator.config.selectors.loading_indicator);
                    
                    if (responseArea && !loadingIndicator) {
                        const content = automator.extractTextContent(responseArea);
                        if (content && content.length > 20) {
                            resolve({
                                success: true,
                                service: context.serviceName,
                                response: {
                                    content: content,
                                    wordCount: content.split(' ').length,
                                    timestamp: new Date().toISOString()
                                }
                            });
                            return;
                        }
                    }
                    
                    if (Date.now() - startTime > extendedTimeout) {
                        reject(new Error('Extended monitoring timeout'));
                        return;
                    }
                    
                    setTimeout(checkForResponse, 2000);
                } catch (error) {
                    reject(error);
                }
            };
            
            checkForResponse();
        });
    }

    async increaseDelaysAndRetry(automator, query, context) {
        console.log('🐌 Increasing delays for more human-like behavior...');
        
        // Significantly slow down the automation
        const originalConfig = automator.config;
        automator.config = {
            ...originalConfig,
            timing: {
                ...originalConfig.timing,
                typing_speed: Math.max(5, originalConfig.timing.typing_speed * 0.3), // Much slower typing
                char_delay_variance: originalConfig.timing.char_delay_variance * 3,
                submit_delay: originalConfig.timing.submit_delay * 3,
                page_load_wait: originalConfig.timing.page_load_wait * 2
            }
        };
        
        try {
            // Also add random delays throughout the process
            await this.sleep(Math.random() * 5000 + 2000); // 2-7 second delay
            return await automator.submitQuery(query, context.options);
        } finally {
            // Restore original config
            automator.config = originalConfig;
        }
    }

    getAlternativeSelectors(serviceName) {
        const alternatives = {
            chatgpt: {
                input: 'textarea, input[type="text"], div[contenteditable="true"]',
                send_button: 'button, input[type="submit"], [role="button"]',
                response_area: '.markdown, .prose, div[role="main"], .message'
            },
            claude: {
                input: 'div[contenteditable="true"], textarea, .ProseMirror',
                send_button: 'button[type="submit"], button[aria-label*="Send"], [role="button"]',
                response_area: '.prose, .message, div[data-testid*="message"], .markdown'
            },
            gemini: {
                input: 'div[contenteditable="true"], textarea, rich-textarea',
                send_button: 'button[aria-label*="Send"], button[type="submit"], [role="button"]',
                response_area: '.markdown, .prose, .response-content, div[role="main"]'
            },
            perplexity: {
                input: 'input, textarea, div[contenteditable="true"]',
                send_button: 'button[type="submit"], button[aria-label*="Submit"], [role="button"]',
                response_area: '.prose, .answer-content, #main, .result-content'
            }
        };
        
        return alternatives[serviceName] || null;
    }

    logError(error, context) {
        const errorEntry = {
            timestamp: new Date().toISOString(),
            service: context.serviceName,
            error: error.message,
            stack: error.stack,
            context: {
                query: context.query?.substring(0, 100),
                attemptCount: context.attemptCount,
                url: window.location.href
            }
        };
        
        this.errorLog.push(errorEntry);
        
        // Keep only last 50 errors
        if (this.errorLog.length > 50) {
            this.errorLog.shift();
        }
        
        console.log('📝 Error logged:', errorEntry);
    }

    createFailureResponse(error, context) {
        return {
            success: false,
            service: context.serviceName,
            error: error.message,
            errorType: this.classifyError(error, context),
            timestamp: new Date().toISOString(),
            fallbacksAttempted: context.attemptCount || 0
        };
    }

    async waitForPageLoad(timeout = 10000) {
        return new Promise((resolve) => {
            if (document.readyState === 'complete') {
                resolve();
            } else {
                const checkReady = () => {
                    if (document.readyState === 'complete') {
                        resolve();
                    } else {
                        setTimeout(checkReady, 100);
                    }
                };
                checkReady();
                
                // Timeout fallback
                setTimeout(resolve, timeout);
            }
        });
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Get error statistics
    getErrorStats() {
        const stats = {
            totalErrors: this.errorLog.length,
            errorsByService: {},
            errorsByType: {},
            recentErrors: this.errorLog.slice(-10)
        };
        
        this.errorLog.forEach(entry => {
            // Count by service
            stats.errorsByService[entry.service] = (stats.errorsByService[entry.service] || 0) + 1;
            
            // Count by type (simplified)
            const errorType = entry.error.includes('timeout') ? 'timeout' :
                            entry.error.includes('not found') ? 'element_not_found' :
                            entry.error.includes('failed') ? 'automation_failed' : 'other';
            stats.errorsByType[errorType] = (stats.errorsByType[errorType] || 0) + 1;
        });
        
        return stats;
    }

    // Clear error log
    clearErrors() {
        this.errorLog = [];
        console.log('🧹 Error log cleared');
    }
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.AutomationErrorHandler = AutomationErrorHandler;
}

console.log('✅ Error Handler Ready');