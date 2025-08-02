// Perplexity Automation Script
// Specialized automation for Perplexity AI interface

console.log('🔍 Perplexity Automation Script Loaded');

class PerplexityAutomator {
    constructor() {
        this.serviceName = 'perplexity';
        this.baseUrl = 'https://www.perplexity.ai/';
        this.isReady = false;
        this.currentQuery = null;
        this.responseObserver = null;
        this.config = {
            selectors: {
                // Updated selectors for current Perplexity interface
                input: 'input[placeholder*="Ask"], textarea[placeholder*="Ask"], div[contenteditable="true"], .query-input',
                send_button: 'button[aria-label*="Submit"], .submit-button, button[type="submit"], button:has(svg[data-icon="arrow"])',
                response_area: '#main, .answer-content, .response-container, .prose, .result-content',
                loading_indicator: '.loading, .searching, .spinner, .thinking',
                message_container: '.conversation-item, .qa-pair',
                new_chat_button: 'button[aria-label*="New"], a[href="/"], button[data-testid="new-thread"]',
                stop_button: 'button[aria-label*="Stop"], button[data-testid="stop-button"]'
            },
            timing: {
                page_load_wait: 2500,
                typing_speed: 28, // chars per second (fastest - Perplexity is snappy)
                char_delay_variance: 30,
                response_timeout: 150000, // 2.5 minutes (give more time for complex queries)
                polling_interval: 1500,
                submit_delay: 500
            },
            retry: {
                max_attempts: 3,
                delay_multiplier: 1500
            }
        };
    }

    async initialize() {
        console.log('🚀 Initializing Perplexity Automator...');
        
        try {
            // Wait for page to load
            await this.waitForPageLoad();
            
            // Check if we're on Perplexity
            if (!this.isOnPerplexity()) {
                throw new Error('Not on Perplexity page');
            }
            
            // Wait for interface elements
            await this.waitForInterface();
            
            this.isReady = true;
            console.log('✅ Perplexity Automator ready');
            
            return { success: true, message: 'Perplexity automator initialized' };
            
        } catch (error) {
            console.error('❌ Perplexity Automator initialization failed:', error);
            return { success: false, error: error.message };
        }
    }

    isOnPerplexity() {
        return window.location.hostname === 'www.perplexity.ai' ||
               window.location.hostname === 'perplexity.ai';
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
        console.log('⏳ Waiting for Perplexity interface...');
        
        const maxWait = 25000; // 25 seconds (Perplexity loads quickly)
        const checkInterval = 1000;
        let waited = 0;
        
        while (waited < maxWait) {
            const input = document.querySelector(this.config.selectors.input);
            if (input && this.isElementInteractable(input)) {
                console.log('✅ Perplexity interface ready');
                return true;
            }
            
            await this.sleep(checkInterval);
            waited += checkInterval;
        }
        
        throw new Error('Perplexity interface not found or not ready');
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
        console.log(`📝 Submitting query to Perplexity: "${query.substring(0, 50)}..."`);
        
        if (!this.isReady) {
            throw new Error('Perplexity automator not initialized');
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
            
            console.log('✅ Perplexity query completed');
            return {
                success: true,
                service: this.serviceName,
                query: query,
                response: response,
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            console.error('❌ Perplexity query failed:', error);
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
                await this.sleep(400);
                
                // Focus the input
                input.focus();
                input.click();
                await this.sleep(200);
                
                console.log(`✅ Found and focused Perplexity input: ${selector}`);
                return input;
            }
        }
        
        if (attempt < this.config.retry.max_attempts) {
            console.log(`⏳ Input not found, retrying... (${attempt}/${this.config.retry.max_attempts})`);
            await this.sleep(this.config.retry.delay_multiplier * attempt);
            return this.findAndFocusInput(attempt + 1);
        }
        
        throw new Error('Perplexity input field not found or not interactable');
    }

    async clearInput(input) {
        try {
            if (input.contentEditable === 'true') {
                // Handle contenteditable div
                const range = document.createRange();
                range.selectNodeContents(input);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                
                await this.sleep(100);
                document.execCommand('delete');
                
                input.innerHTML = '';
                input.textContent = '';
                
            } else {
                // Handle regular input/textarea
                input.select();
                input.value = '';
            }
            
            // Trigger input events
            this.triggerInputEvents(input);
            await this.sleep(150);
            
            console.log('🧹 Cleared Perplexity input');
        } catch (error) {
            console.warn('⚠️ Could not clear input:', error);
        }
    }

    async typeQuery(input, query) {
        console.log('⌨️ Typing query to Perplexity with human-like behavior...');
        
        const chars = query.split('');
        
        for (let i = 0; i < chars.length; i++) {
            const char = chars[i];
            
            // Handle different input types
            if (input.contentEditable === 'true') {
                document.execCommand('insertText', false, char);
            } else if (input.tagName === 'TEXTAREA' || input.tagName === 'INPUT') {
                input.value += char;
            } else {
                input.textContent += char;
            }
            
            // Trigger input events
            this.triggerInputEvents(input);
            
            // Human-like delay with variance (faster for Perplexity)
            const baseDelay = 1000 / this.config.timing.typing_speed;
            const variance = (Math.random() - 0.5) * this.config.timing.char_delay_variance;
            const delay = Math.max(8, baseDelay + variance);
            
            // Shorter pauses for punctuation (Perplexity style)
            if (char === '.' || char === '!' || char === '?') {
                await this.sleep(delay * 2.5);
            } else if (char === ',' || char === ';') {
                await this.sleep(delay * 1.5);
            } else if (char === ' ') {
                await this.sleep(delay * 1.2);
            } else {
                await this.sleep(delay);
            }
        }
        
        console.log('✅ Query typed successfully to Perplexity');
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
        
        // Additional events for modern inputs
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

    async submitInput() {
        console.log('📤 Submitting Perplexity query...');
        
        // Wait for UI to stabilize (shorter for Perplexity)
        await this.sleep(this.config.timing.submit_delay);
        
        const selectors = this.config.selectors.send_button.split(', ');
        
        for (const selector of selectors) {
            const button = document.querySelector(selector);
            if (button && this.isElementInteractable(button) && !button.disabled) {
                
                // Scroll button into view
                button.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await this.sleep(200);
                
                // Click the button
                button.click();
                console.log(`✅ Clicked Perplexity submit button: ${selector}`);
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
        console.log('👁️ Monitoring Perplexity response...');
        
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
                    
                    // Check for "searching" text or other loading states
                    const searchingText = document.body.textContent.toLowerCase().includes('searching') ||
                                        document.body.textContent.toLowerCase().includes('thinking');
                    
                    // Find response area
                    const responseElements = document.querySelectorAll(this.config.selectors.response_area);
                    let latestResponse = '';
                    
                    if (responseElements.length > 0) {
                        // Get the response with the most content
                        let bestResponse = '';
                        for (const element of responseElements) {
                            const content = this.extractTextContent(element);
                            if (content.length > bestResponse.length) {
                                bestResponse = content;
                            }
                        }
                        latestResponse = bestResponse;
                    }
                    
                    // Check if response is complete
                    if (!isLoading && !searchingText && latestResponse.length > 30) {
                        if (latestResponse.length === lastResponseLength) {
                            stableCount++;
                            if (stableCount >= stableThreshold) {
                                console.log('✅ Perplexity response complete');
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
                        console.error('❌ Perplexity response timeout details:', {
                            timeElapsed: Date.now() - startTime,
                            isLoading: isLoading,
                            searchingText: searchingText,
                            responseLength: latestResponse.length,
                            loadingElements: loadingElements.length,
                            responseElements: responseElements.length
                        });
                        
                        // Try to get partial response if available
                        if (latestResponse.length > 10) {
                            console.log('🔄 Partial response available, returning it instead of failing');
                            resolve({
                                content: latestResponse + '\n\n[Note: Response was truncated due to timeout]',
                                wordCount: latestResponse.split(' ').length,
                                timestamp: new Date().toISOString(),
                                partial: true
                            });
                        } else {
                            reject(new Error(`Perplexity response timeout after ${Math.round((Date.now() - startTime)/1000)}s`));
                        }
                        return;
                    }
                    
                    // Continue monitoring
                    setTimeout(checkResponse, this.config.timing.polling_interval);
                    
                } catch (error) {
                    console.error('❌ Error monitoring Perplexity response:', error);
                    reject(error);
                }
            };
            
            // Start monitoring after initial delay
            setTimeout(checkResponse, 2000);
        });
    }

    extractTextContent(element) {
        if (!element) return '';
        
        // Perplexity specific content extraction
        let content = '';
        
        // Try different content extraction methods
        if (element.innerText) {
            content = element.innerText;
        } else if (element.textContent) {
            content = element.textContent;
        } else {
            // Extract text from HTML, preserving structure
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
            .replace(/Sources?\s*:\s*\d+/gi, '')  // Remove "Sources: 1,2,3" text
            .replace(/\[\d+\]/g, '')  // Remove citation numbers like [1]
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
        console.log('🛑 Perplexity Emergency Stop');
        
        try {
            // Try to click stop button if available
            const stopButton = document.querySelector(this.config.selectors.stop_button);
            if (stopButton && this.isElementInteractable(stopButton)) {
                stopButton.click();
                console.log('✅ Clicked Perplexity stop button');
            }
            
            // Stop response monitoring
            this.stopResponseMonitoring();
            
            return { success: true, message: 'Perplexity automation stopped' };
            
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
            onCorrectPage: this.isOnPerplexity(),
            timestamp: new Date().toISOString()
        };
    }
}

// Export for use in background script
if (typeof window !== 'undefined') {
    window.PerplexityAutomator = PerplexityAutomator;
}

console.log('✅ Perplexity Automation Script Ready');