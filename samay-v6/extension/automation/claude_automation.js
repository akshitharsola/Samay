// Claude Automation Script
// Specialized automation for Anthropic Claude interface

console.log('🧠 Claude Automation Script Loaded');

class ClaudeAutomator {
    constructor() {
        this.serviceName = 'claude';
        this.baseUrl = 'https://claude.ai/';
        this.isReady = false;
        this.currentQuery = null;
        this.responseObserver = null;
        this.config = {
            selectors: {
                // Updated selectors for current Claude interface
                input: 'div[contenteditable="true"], .ProseMirror, div[data-testid="chat-input"], div[role="textbox"]',
                send_button: 'button[aria-label*="Send"], button[type="submit"], button[data-testid="send-button"], button:has(svg[data-testid="send-icon"])',
                response_area: 'div[data-testid*="message"], .font-claude-message, div[data-is-streaming], .prose',
                loading_indicator: '.thinking, .loading-dots, .animate-pulse, div[data-is-streaming="true"]',
                message_container: 'div[data-testid*="message"], .message',
                new_chat_button: 'button[aria-label*="New"], a[href*="new"], button[data-testid="new-chat"]',
                stop_button: 'button[aria-label*="Stop"], button[data-testid="stop-button"]'
            },
            timing: {
                page_load_wait: 4000,
                typing_speed: 20, // chars per second (slightly slower for Claude)
                char_delay_variance: 60,
                response_timeout: 150000, // 2.5 minutes (Claude can be slower)
                polling_interval: 2000,
                submit_delay: 1000
            },
            retry: {
                max_attempts: 3,
                delay_multiplier: 2500
            }
        };
    }

    async initialize() {
        console.log('🚀 Initializing Claude Automator...');
        
        try {
            // Wait for page to load
            await this.waitForPageLoad();
            
            // Check if we're on Claude
            if (!this.isOnClaude()) {
                throw new Error('Not on Claude page');
            }
            
            // Wait for interface elements
            await this.waitForInterface();
            
            this.isReady = true;
            console.log('✅ Claude Automator ready');
            
            return { success: true, message: 'Claude automator initialized' };
            
        } catch (error) {
            console.error('❌ Claude Automator initialization failed:', error);
            return { success: false, error: error.message };
        }
    }

    isOnClaude() {
        return window.location.hostname === 'claude.ai';
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
        console.log('⏳ Waiting for Claude interface...');
        
        const maxWait = 40000; // 40 seconds (Claude can be slow to load)
        const checkInterval = 1000;
        let waited = 0;
        
        while (waited < maxWait) {
            const input = document.querySelector(this.config.selectors.input);
            if (input && this.isElementInteractable(input)) {
                console.log('✅ Claude interface ready');
                return true;
            }
            
            await this.sleep(checkInterval);
            waited += checkInterval;
        }
        
        throw new Error('Claude interface not found or not ready');
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
        console.log(`📝 Submitting query to Claude: "${query.substring(0, 50)}..."`);
        
        if (!this.isReady) {
            throw new Error('Claude automator not initialized');
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
            
            console.log('✅ Claude query completed');
            return {
                success: true,
                service: this.serviceName,
                query: query,
                response: response,
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            console.error('❌ Claude query failed:', error);
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
                
                // Focus the input with multiple methods
                input.focus();
                input.click();
                await this.sleep(300);
                
                console.log(`✅ Found and focused Claude input: ${selector}`);
                return input;
            }
        }
        
        if (attempt < this.config.retry.max_attempts) {
            console.log(`⏳ Input not found, retrying... (${attempt}/${this.config.retry.max_attempts})`);
            await this.sleep(this.config.retry.delay_multiplier * attempt);
            return this.findAndFocusInput(attempt + 1);
        }
        
        throw new Error('Claude input field not found or not interactable');
    }

    async clearInput(input) {
        try {
            // Claude uses contenteditable, so we need special handling
            if (input.contentEditable === 'true') {
                // Select all content
                const range = document.createRange();
                range.selectNodeContents(input);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                
                await this.sleep(100);
                
                // Delete selected content
                document.execCommand('delete');
                
                // Alternative methods
                input.innerHTML = '';
                input.textContent = '';
                input.innerText = '';
                
            } else {
                // Regular input handling
                input.select();
                input.value = '';
            }
            
            // Trigger input events
            this.triggerInputEvents(input);
            await this.sleep(200);
            
            console.log('🧹 Cleared Claude input');
        } catch (error) {
            console.warn('⚠️ Could not clear input:', error);
        }
    }

    async typeQuery(input, query) {
        console.log('⌨️ Typing query to Claude with human-like behavior...');
        
        const chars = query.split('');
        
        for (let i = 0; i < chars.length; i++) {
            const char = chars[i];
            
            // Handle contenteditable divs (Claude's preferred input method)
            if (input.contentEditable === 'true') {
                // Insert text at cursor position
                document.execCommand('insertText', false, char);
            } else {
                // Regular input fields
                if (input.tagName === 'TEXTAREA' || input.type === 'text') {
                    input.value += char;
                } else {
                    input.textContent += char;
                }
            }
            
            // Trigger input events
            this.triggerInputEvents(input);
            
            // Human-like delay with variance
            const baseDelay = 1000 / this.config.timing.typing_speed;
            const variance = (Math.random() - 0.5) * this.config.timing.char_delay_variance;
            const delay = Math.max(15, baseDelay + variance);
            
            // Add longer pauses for punctuation and spaces
            if (char === '.' || char === '!' || char === '?') {
                await this.sleep(delay * 4);
            } else if (char === ',' || char === ';') {
                await this.sleep(delay * 2.5);
            } else if (char === ' ') {
                await this.sleep(delay * 1.8);
            } else {
                await this.sleep(delay);
            }
        }
        
        console.log('✅ Query typed successfully to Claude');
    }

    triggerInputEvents(input) {
        const events = ['input', 'change', 'keyup', 'keydown', 'textInput'];
        
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
        
        // Special handling for contenteditable
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
        console.log('📤 Submitting Claude query...');
        
        // Wait for UI to stabilize
        await this.sleep(this.config.timing.submit_delay);
        
        const selectors = this.config.selectors.send_button.split(', ');
        
        for (const selector of selectors) {
            const button = document.querySelector(selector);
            if (button && this.isElementInteractable(button) && !button.disabled) {
                
                // Scroll button into view
                button.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await this.sleep(400);
                
                // Click the button
                button.click();
                console.log(`✅ Clicked Claude submit button: ${selector}`);
                return;
            }
        }
        
        // Fallback: try Cmd+Enter (Claude's shortcut)
        console.log('🔄 Submit button not found, trying Cmd+Enter...');
        const input = document.querySelector(this.config.selectors.input);
        if (input) {
            const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
            const enterEvent = new KeyboardEvent('keydown', {
                key: 'Enter',
                code: 'Enter',
                keyCode: 13,
                which: 13,
                ctrlKey: !isMac,
                metaKey: isMac,
                bubbles: true
            });
            input.dispatchEvent(enterEvent);
        }
    }

    async monitorResponse() {
        console.log('👁️ Monitoring Claude response...');
        
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            let lastResponseLength = 0;
            let stableCount = 0;
            const stableThreshold = 4; // Claude needs more stability checks
            
            const checkResponse = () => {
                try {
                    // Check for loading/streaming indicators
                    const loadingElement = document.querySelector(this.config.selectors.loading_indicator);
                    const isLoading = loadingElement && this.isElementVisible(loadingElement);
                    
                    // Check for streaming attribute
                    const streamingElement = document.querySelector('[data-is-streaming="true"]');
                    const isStreaming = streamingElement && this.isElementVisible(streamingElement);
                    
                    // Find response area
                    const responseElements = document.querySelectorAll(this.config.selectors.response_area);
                    let latestResponse = '';
                    
                    if (responseElements.length > 0) {
                        // Get the last response element that's not from user
                        for (let i = responseElements.length - 1; i >= 0; i--) {
                            const element = responseElements[i];
                            // Skip user messages by checking for common user indicators
                            const isUserMessage = element.closest('[data-is-user-message="true"]') ||
                                                element.closest('.user-message') ||
                                                element.textContent.includes('Human:');
                            
                            if (!isUserMessage) {
                                latestResponse = this.extractTextContent(element);
                                break;
                            }
                        }
                    }
                    
                    // Check if response is complete
                    if (!isLoading && !isStreaming && latestResponse.length > 30) {
                        if (latestResponse.length === lastResponseLength) {
                            stableCount++;
                            if (stableCount >= stableThreshold) {
                                console.log('✅ Claude response complete');
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
                        reject(new Error('Claude response timeout'));
                        return;
                    }
                    
                    // Continue monitoring
                    setTimeout(checkResponse, this.config.timing.polling_interval);
                    
                } catch (error) {
                    console.error('❌ Error monitoring Claude response:', error);
                    reject(error);
                }
            };
            
            // Start monitoring after initial delay
            setTimeout(checkResponse, 3000);
        });
    }

    extractTextContent(element) {
        if (!element) return '';
        
        // Claude specific content extraction
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
                .replace(/<[^>]*>/g, ' ')
                .replace(/&nbsp;/g, ' ');
        }
        
        // Clean up the content
        return content
            .replace(/\s+/g, ' ')  // Replace multiple spaces
            .replace(/\n\s*\n/g, '\n')  // Replace multiple newlines
            .replace(/^\s*Claude\s*:?\s*/i, '')  // Remove "Claude:" prefix
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
        console.log('🛑 Claude Emergency Stop');
        
        try {
            // Try to click stop button if available
            const stopButton = document.querySelector(this.config.selectors.stop_button);
            if (stopButton && this.isElementInteractable(stopButton)) {
                stopButton.click();
                console.log('✅ Clicked Claude stop button');
            }
            
            // Stop response monitoring
            this.stopResponseMonitoring();
            
            return { success: true, message: 'Claude automation stopped' };
            
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
            onCorrectPage: this.isOnClaude(),
            timestamp: new Date().toISOString()
        };
    }
}

// Export for use in background script
if (typeof window !== 'undefined') {
    window.ClaudeAutomator = ClaudeAutomator;
}

console.log('✅ Claude Automation Script Ready');