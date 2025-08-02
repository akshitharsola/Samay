// ChatGPT Automation Script
// Specialized automation for OpenAI ChatGPT interface

console.log('🤖 ChatGPT Automation Script Loaded');

class ChatGPTAutomator {
    constructor() {
        this.serviceName = 'chatgpt';
        this.baseUrl = 'https://chat.openai.com/';
        this.isReady = false;
        this.currentQuery = null;
        this.responseObserver = null;
        this.config = {
            selectors: {
                // Updated selectors for current ChatGPT interface
                input: 'textarea[data-id="root"], #prompt-textarea, textarea[placeholder*="Send a message"]',
                send_button: 'button[data-testid="send-button"], button[aria-label*="Send"], button:has(svg[data-testid="send-button"])',
                response_area: 'div[data-message-author-role="assistant"], .markdown, div[data-testid*="conversation"], .prose',
                loading_indicator: '.result-thinking, .text-token-text-secondary, .animate-pulse',
                message_container: 'div[data-testid*="conversation-turn"], .group',
                new_chat_button: 'a[href="/"], button[aria-label*="New chat"]',
                stop_button: 'button[aria-label*="Stop"], button[data-testid="stop-button"]'
            },
            timing: {
                page_load_wait: 3000,
                typing_speed: 25, // chars per second (human-like)
                char_delay_variance: 50, // ms variance between characters
                response_timeout: 120000, // 2 minutes
                polling_interval: 2000,
                submit_delay: 800
            },
            retry: {
                max_attempts: 3,
                delay_multiplier: 2000
            }
        };
    }

    async initialize() {
        console.log('🚀 Initializing ChatGPT Automator...');
        
        try {
            // Wait for page to load
            await this.waitForPageLoad();
            
            // Check if we're on ChatGPT
            if (!this.isOnChatGPT()) {
                throw new Error('Not on ChatGPT page');
            }
            
            // Wait for interface elements
            await this.waitForInterface();
            
            this.isReady = true;
            console.log('✅ ChatGPT Automator ready');
            
            return { success: true, message: 'ChatGPT automator initialized' };
            
        } catch (error) {
            console.error('❌ ChatGPT Automator initialization failed:', error);
            return { success: false, error: error.message };
        }
    }

    isOnChatGPT() {
        return window.location.hostname === 'chat.openai.com' || 
               window.location.hostname === 'chatgpt.com';
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
        console.log('⏳ Waiting for ChatGPT interface...');
        
        const maxWait = 30000; // 30 seconds
        const checkInterval = 1000;
        let waited = 0;
        
        while (waited < maxWait) {
            const input = document.querySelector(this.config.selectors.input);
            if (input && this.isElementInteractable(input)) {
                console.log('✅ ChatGPT interface ready');
                return true;
            }
            
            await this.sleep(checkInterval);
            waited += checkInterval;
        }
        
        throw new Error('ChatGPT interface not found or not ready');
    }

    isElementInteractable(element) {
        if (!element) return false;
        
        const style = window.getComputedStyle(element);
        return element.offsetHeight > 0 && 
               element.offsetWidth > 0 && 
               style.visibility !== 'hidden' && 
               style.display !== 'none' &&
               !element.disabled;
    }

    async submitQuery(query, options = {}) {
        console.log(`📝 Submitting query to ChatGPT: "${query.substring(0, 50)}..."`);
        
        if (!this.isReady) {
            throw new Error('ChatGPT automator not initialized');
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
            
            console.log('✅ ChatGPT query completed');
            return {
                success: true,
                service: this.serviceName,
                query: query,
                response: response,
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            console.error('❌ ChatGPT query failed:', error);
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
                
                // Focus the input
                input.focus();
                await this.sleep(200);
                
                console.log(`✅ Found and focused ChatGPT input: ${selector}`);
                return input;
            }
        }
        
        if (attempt < this.config.retry.max_attempts) {
            console.log(`⏳ Input not found, retrying... (${attempt}/${this.config.retry.max_attempts})`);
            await this.sleep(this.config.retry.delay_multiplier * attempt);
            return this.findAndFocusInput(attempt + 1);
        }
        
        throw new Error('ChatGPT input field not found or not interactable');
    }

    async clearInput(input) {
        try {
            // Select all and delete
            input.select();
            await this.sleep(100);
            
            // Clear with different methods
            input.value = '';
            input.textContent = '';
            input.innerText = '';
            
            // Trigger input events
            this.triggerInputEvents(input);
            await this.sleep(200);
            
            console.log('🧹 Cleared ChatGPT input');
        } catch (error) {
            console.warn('⚠️ Could not clear input:', error);
        }
    }

    async typeQuery(input, query) {
        console.log('⌨️ Typing query with human-like behavior...');
        
        const chars = query.split('');
        
        for (let i = 0; i < chars.length; i++) {
            const char = chars[i];
            
            // Simulate human typing patterns
            if (input.tagName === 'TEXTAREA' || input.type === 'text') {
                input.value += char;
            } else {
                // For contenteditable divs
                input.textContent += char;
            }
            
            // Trigger input events
            this.triggerInputEvents(input);
            
            // Human-like delay with variance
            const baseDelay = 1000 / this.config.timing.typing_speed;
            const variance = (Math.random() - 0.5) * this.config.timing.char_delay_variance;
            const delay = Math.max(10, baseDelay + variance);
            
            // Add longer pauses for punctuation and spaces (more human-like)
            if (char === '.' || char === '!' || char === '?') {
                await this.sleep(delay * 3);
            } else if (char === ',' || char === ';') {
                await this.sleep(delay * 2);
            } else if (char === ' ') {
                await this.sleep(delay * 1.5);
            } else {
                await this.sleep(delay);
            }
        }
        
        console.log('✅ Query typed successfully');
    }

    triggerInputEvents(input) {
        // Trigger comprehensive input events
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
    }

    async submitInput() {
        console.log('📤 Submitting ChatGPT query...');
        
        // Wait a moment for UI to stabilize
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
                console.log(`✅ Clicked submit button: ${selector}`);
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
        console.log('👁️ Monitoring ChatGPT response...');
        
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            let lastResponseLength = 0;
            let stableCount = 0;
            const stableThreshold = 3; // Check 3 times to ensure response is complete
            
            const checkResponse = () => {
                try {
                    // Check for loading indicators
                    const loadingElement = document.querySelector(this.config.selectors.loading_indicator);
                    const isLoading = loadingElement && this.isElementVisible(loadingElement);
                    
                    // Find response area
                    const responseElements = document.querySelectorAll(this.config.selectors.response_area);
                    let latestResponse = '';
                    
                    if (responseElements.length > 0) {
                        // Get the last response element
                        const lastElement = responseElements[responseElements.length - 1];
                        latestResponse = this.extractTextContent(lastElement);
                    }
                    
                    // Check if response is complete
                    if (!isLoading && latestResponse.length > 20) {
                        if (latestResponse.length === lastResponseLength) {
                            stableCount++;
                            if (stableCount >= stableThreshold) {
                                console.log('✅ ChatGPT response complete');
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
                        reject(new Error('ChatGPT response timeout'));
                        return;
                    }
                    
                    // Continue monitoring
                    setTimeout(checkResponse, this.config.timing.polling_interval);
                    
                } catch (error) {
                    console.error('❌ Error monitoring response:', error);
                    reject(error);
                }
            };
            
            // Start monitoring after initial delay
            setTimeout(checkResponse, 2000);
        });
    }

    extractTextContent(element) {
        if (!element) return '';
        
        // Try different content extraction methods
        let content = '';
        
        if (element.innerText) {
            content = element.innerText;
        } else if (element.textContent) {
            content = element.textContent;
        } else {
            content = element.innerHTML.replace(/<[^>]*>/g, ' ');
        }
        
        // Clean up the content
        return content
            .replace(/\s+/g, ' ')  // Replace multiple spaces with single space
            .replace(/\n\s*\n/g, '\n')  // Replace multiple newlines
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
        console.log('🛑 ChatGPT Emergency Stop');
        
        try {
            // Try to click stop button if available
            const stopButton = document.querySelector(this.config.selectors.stop_button);
            if (stopButton && this.isElementInteractable(stopButton)) {
                stopButton.click();
                console.log('✅ Clicked ChatGPT stop button');
            }
            
            // Stop response monitoring
            this.stopResponseMonitoring();
            
            return { success: true, message: 'ChatGPT automation stopped' };
            
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
            onCorrectPage: this.isOnChatGPT(),
            timestamp: new Date().toISOString()
        };
    }
}

// Export for use in background script
if (typeof window !== 'undefined') {
    window.ChatGPTAutomator = ChatGPTAutomator;
}

console.log('✅ ChatGPT Automation Script Ready');