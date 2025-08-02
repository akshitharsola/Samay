// Gemini Automation Script
// Specialized automation for Google Gemini interface

console.log('💎 Gemini Automation Script Loaded');

class GeminiAutomator {
    constructor() {
        this.serviceName = 'gemini';
        this.baseUrl = 'https://gemini.google.com/';
        this.isReady = false;
        this.currentQuery = null;
        this.responseObserver = null;
        this.config = {
            selectors: {
                // Updated selectors for current Gemini interface
                input: 'rich-textarea > div > p, .ql-editor p, div[contenteditable="true"], textarea[placeholder*="Enter"]',
                send_button: 'button[aria-label*="Send"], button[data-testid="send-button"], button:has(svg[aria-label*="send"])',
                response_area: 'div[data-testid*="response"], .response-content, .model-response, .markdown',
                loading_indicator: '.loading, .spinner, .thinking, .generating',
                message_container: '.conversation-turn, .message-pair',
                new_chat_button: 'button[aria-label*="New"], a[href*="new"], button[data-testid="new-chat"]',
                stop_button: 'button[aria-label*="Stop"], button[data-testid="stop-button"]'
            },
            timing: {
                page_load_wait: 3500,
                typing_speed: 22, // chars per second
                char_delay_variance: 45,
                response_timeout: 120000, // 2 minutes
                polling_interval: 1500,
                submit_delay: 700
            },
            retry: {
                max_attempts: 3,
                delay_multiplier: 2000
            }
        };
    }

    async initialize() {
        console.log('🚀 Initializing Gemini Automator...');
        
        try {
            // Wait for page to load
            await this.waitForPageLoad();
            
            // Check if we're on Gemini
            if (!this.isOnGemini()) {
                throw new Error('Not on Gemini page');
            }
            
            // Wait for interface elements
            await this.waitForInterface();
            
            this.isReady = true;
            console.log('✅ Gemini Automator ready');
            
            return { success: true, message: 'Gemini automator initialized' };
            
        } catch (error) {
            console.error('❌ Gemini Automator initialization failed:', error);
            return { success: false, error: error.message };
        }
    }

    isOnGemini() {
        return window.location.hostname === 'gemini.google.com' ||
               window.location.hostname === 'bard.google.com';
    }

    async waitForPageLoad() {
        return new Promise((resolve) => {
            if (document.readyState === 'complete') {
                setTimeout(resolve, this.config.timing.page_load_wait);
            } else {
                window.addEventListener('load', () => {
                    setTimeout(resolve, this.config.timing.page_load_wait);
                });
            }
        });
    }

    async waitForInterface() {
        console.log('⏳ Waiting for Gemini interface...');
        
        const maxWait = 35000; // 35 seconds
        const checkInterval = 1000;
        let waited = 0;
        
        while (waited < maxWait) {
            const input = document.querySelector(this.config.selectors.input);
            if (input && this.isElementInteractable(input)) {
                console.log('✅ Gemini interface ready');
                return true;
            }
            
            await this.sleep(checkInterval);
            waited += checkInterval;
        }
        
        throw new Error('Gemini interface not found or not ready');
    }

    isElementInteractable(element) {
        if (!element) return false;
        
        const style = window.getComputedStyle(element);
        return element.offsetHeight > 0 && 
               element.offsetWidth > 0 && 
               style.visibility !== 'hidden' && 
               style.display !== 'none' &&
               !element.disabled &&
               !element.getAttribute('aria-disabled');
    }

    async submitQuery(query, options = {}) {
        console.log(`📝 Submitting query to Gemini: "${query.substring(0, 50)}..."`);
        
        if (!this.isReady) {
            throw new Error('Gemini automator not initialized');
        }

        try {
            // Clear any existing response monitoring
            this.stopResponseMonitoring();
            
            // Find and focus input
            const input = await this.findAndFocusInput();
            
            // Clear existing text
            await this.clearInput(input);
            
            // Type the query with human-like behavior
            await this.typeQuery(input, query);
            
            // Submit the query
            await this.submitInput();
            
            // Start monitoring for response
            const response = await this.monitorResponse();
            
            console.log('✅ Gemini query completed');
            return {
                success: true,
                service: this.serviceName,
                query: query,
                response: response,
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            console.error('❌ Gemini query failed:', error);
            return {
                success: false,
                service: this.serviceName,
                query: query,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    async findAndFocusInput(attempt = 1) {
        const selectors = this.config.selectors.input.split(', ');
        
        for (const selector of selectors) {
            const input = document.querySelector(selector);
            if (input && this.isElementInteractable(input)) {
                // Scroll into view
                input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await this.sleep(500);
                
                // Focus the input with multiple methods for different Gemini versions
                input.focus();
                input.click();
                
                // For rich text editors, ensure cursor is placed
                if (input.contentEditable === 'true') {
                    const range = document.createRange();
                    const selection = window.getSelection();
                    range.selectNodeContents(input);
                    range.collapse(false);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
                
                await this.sleep(300);
                
                console.log(`✅ Found and focused Gemini input: ${selector}`);
                return input;
            }
        }
        
        if (attempt < this.config.retry.max_attempts) {
            console.log(`⏳ Input not found, retrying... (${attempt}/${this.config.retry.max_attempts})`);
            await this.sleep(this.config.retry.delay_multiplier * attempt);
            return this.findAndFocusInput(attempt + 1);
        }
        
        throw new Error('Gemini input field not found or not interactable');
    }

    async clearInput(input) {
        try {
            if (input.contentEditable === 'true') {
                // Handle rich text input (common in newer Gemini)
                const range = document.createRange();
                range.selectNodeContents(input);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                
                await this.sleep(100);
                document.execCommand('delete');
                
                // Clear with multiple methods
                input.innerHTML = '';
                input.textContent = '';
                input.innerText = '';
                
            } else if (input.tagName === 'TEXTAREA' || input.type === 'text') {
                // Handle regular textarea/input
                input.select();
                input.value = '';
            } else {
                // Handle other content editable elements
                input.textContent = '';
                input.innerHTML = '';
            }
            
            // Trigger input events
            this.triggerInputEvents(input);
            await this.sleep(200);
            
            console.log('🧹 Cleared Gemini input');
        } catch (error) {
            console.warn('⚠️ Could not clear input:', error);
        }
    }

    async typeQuery(input, query) {
        console.log('⌨️ Typing query to Gemini with human-like behavior...');
        
        const chars = query.split('');
        
        for (let i = 0; i < chars.length; i++) {
            const char = chars[i];
            
            // Handle different input types
            if (input.contentEditable === 'true') {
                // Rich text editor - use execCommand
                document.execCommand('insertText', false, char);
            } else if (input.tagName === 'TEXTAREA' || input.type === 'text') {
                // Regular input/textarea
                input.value += char;
            } else {
                // Fallback for other elements
                input.textContent += char;
            }
            
            // Trigger input events
            this.triggerInputEvents(input);
            
            // Human-like delay with variance
            const baseDelay = 1000 / this.config.timing.typing_speed;
            const variance = (Math.random() - 0.5) * this.config.timing.char_delay_variance;
            const delay = Math.max(10, baseDelay + variance);
            
            // Add longer pauses for punctuation and spaces
            if (char === '.' || char === '!' || char === '?') {
                await this.sleep(delay * 3.5);
            } else if (char === ',' || char === ';' || char === ':') {
                await this.sleep(delay * 2);
            } else if (char === ' ') {
                await this.sleep(delay * 1.5);
            } else {
                await this.sleep(delay);
            }
        }
        
        console.log('✅ Query typed successfully to Gemini');
    }

    triggerInputEvents(input) {
        const events = ['input', 'change', 'keyup', 'keydown'];
        
        events.forEach(eventType => {
            try {
                input.dispatchEvent(new Event(eventType, { 
                    bubbles: true, 
                    cancelable: true 
                }));
            } catch (e) {
                // Ignore event dispatch errors
            }
        });
        
        // Special handling for content editable
        if (input.contentEditable === 'true') {
            try {
                input.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText'
                }));
            } catch (e) {
                // Ignore if InputEvent not supported
            }
        }
    }

    async submitInput() {
        console.log('📤 Submitting Gemini query...');
        
        // Wait for UI to stabilize
        await this.sleep(this.config.timing.submit_delay);
        
        const selectors = this.config.selectors.send_button.split(', ');
        
        for (const selector of selectors) {
            const button = document.querySelector(selector);
            if (button && this.isElementInteractable(button) && !button.disabled) {
                
                // Scroll button into view
                button.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await this.sleep(300);
                
                // Click the button
                button.click();
                console.log(`✅ Clicked Gemini submit button: ${selector}`);
                return;
            }
        }
        
        // Fallback: try Enter key
        console.log('🔄 Submit button not found, trying Enter key...');
        const input = document.querySelector(this.config.selectors.input);
        if (input) {
            const enterEvent = new KeyboardEvent('keydown', {
                key: 'Enter',
                code: 'Enter',
                keyCode: 13,
                which: 13,
                bubbles: true
            });
            input.dispatchEvent(enterEvent);
        }
    }

    async monitorResponse() {
        console.log('👁️ Monitoring Gemini response...');
        
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            let lastResponseLength = 0;
            let stableCount = 0;
            const stableThreshold = 3;
            
            const checkResponse = () => {
                try {
                    // Check for loading indicators
                    const loadingElements = document.querySelectorAll(this.config.selectors.loading_indicator);
                    const isLoading = Array.from(loadingElements).some(el => this.isElementVisible(el));
                    
                    // Find response area - Gemini might have multiple response containers
                    const responseElements = document.querySelectorAll(this.config.selectors.response_area);
                    let latestResponse = '';
                    
                    if (responseElements.length > 0) {
                        // Get the last response element that contains substantial content
                        for (let i = responseElements.length - 1; i >= 0; i--) {
                            const element = responseElements[i];
                            const content = this.extractTextContent(element);
                            
                            // Skip user messages and empty responses
                            const isUserMessage = element.closest('[data-is-user]') ||
                                                element.closest('.user-input') ||
                                                content.length < 10;
                            
                            if (!isUserMessage && content.length > latestResponse.length) {
                                latestResponse = content;
                            }
                        }
                    }
                    
                    // Check if response is complete
                    if (!isLoading && latestResponse.length > 20) {
                        if (latestResponse.length === lastResponseLength) {
                            stableCount++;
                            if (stableCount >= stableThreshold) {
                                console.log('✅ Gemini response complete');
                                resolve({
                                    content: latestResponse,
                                    wordCount: latestResponse.split(' ').length,
                                    timestamp: new Date().toISOString()
                                });
                                return;
                            }
                        } else {
                            stableCount = 0;
                            lastResponseLength = latestResponse.length;
                        }
                    }
                    
                    // Check timeout
                    if (Date.now() - startTime > this.config.timing.response_timeout) {
                        reject(new Error('Gemini response timeout'));
                        return;
                    }
                    
                    // Continue monitoring
                    setTimeout(checkResponse, this.config.timing.polling_interval);
                    
                } catch (error) {
                    console.error('❌ Error monitoring Gemini response:', error);
                    reject(error);
                }
            };
            
            // Start monitoring after initial delay
            setTimeout(checkResponse, 2500);
        });
    }

    extractTextContent(element) {
        if (!element) return '';
        
        // Gemini specific content extraction
        let content = '';
        
        // Try different content extraction methods
        if (element.innerText) {
            content = element.innerText;
        } else if (element.textContent) {
            content = element.textContent;
        } else {
            // Extract text from HTML, preserving some structure
            content = element.innerHTML
                .replace(/<br\s*\/?>/gi, '\n')
                .replace(/<\/p>/gi, '\n')
                .replace(/<\/div>/gi, '\n')
                .replace(/<[^>]*>/g, ' ')
                .replace(/&nbsp;/g, ' ');
        }
        
        // Clean up the content
        return content
            .replace(/\s+/g, ' ')  // Replace multiple spaces
            .replace(/\n\s*\n/g, '\n')  // Replace multiple newlines
            .replace(/^\s*Gemini\s*:?\s*/i, '')  // Remove "Gemini:" prefix
            .replace(/^\s*Bard\s*:?\s*/i, '')    // Remove "Bard:" prefix (legacy)
            .trim();
    }

    isElementVisible(element) {
        if (!element) return false;
        
        const style = window.getComputedStyle(element);
        return element.offsetHeight > 0 && 
               element.offsetWidth > 0 && 
               style.visibility !== 'hidden' && 
               style.display !== 'none';
    }

    stopResponseMonitoring() {
        if (this.responseObserver) {
            this.responseObserver.disconnect();
            this.responseObserver = null;
        }
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Emergency stop function
    emergencyStop() {
        console.log('🛑 Gemini Emergency Stop');
        
        try {
            // Try to click stop button if available
            const stopButton = document.querySelector(this.config.selectors.stop_button);
            if (stopButton && this.isElementInteractable(stopButton)) {
                stopButton.click();
                console.log('✅ Clicked Gemini stop button');
            }
            
            // Stop response monitoring
            this.stopResponseMonitoring();
            
            return { success: true, message: 'Gemini automation stopped' };
            
        } catch (error) {
            console.error('❌ Emergency stop failed:', error);
            return { success: false, error: error.message };
        }
    }

    // Get automation status
    getStatus() {
        return {
            service: this.serviceName,
            ready: this.isReady,
            currentQuery: this.currentQuery,
            onCorrectPage: this.isOnGemini(),
            timestamp: new Date().toISOString()
        };
    }
}

// Export for use in background script
if (typeof window !== 'undefined') {
    window.GeminiAutomator = GeminiAutomator;
}

console.log('✅ Gemini Automation Script Ready');