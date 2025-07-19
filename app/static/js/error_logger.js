/**
 * Frontend Error Logging System
 * 
 * This module captures JavaScript errors, AJAX failures, and user interaction errors
 * and sends them to the backend for centralized logging.
 */

class ErrorLogger {
    constructor() {
        this.apiEndpoint = '/api/logging';
        this.maxRetries = 3;
        this.retryDelay = 1000; // 1 second
        this.errorQueue = [];
        this.isOnline = navigator.onLine;
        
        this.init();
    }
    
    init() {
        // Capture uncaught JavaScript exceptions
        window.addEventListener('error', (event) => {
            this.logError({
                message: event.message,
                source: event.filename,
                line: event.lineno,
                column: event.colno,
                error: event.error ? event.error.toString() : 'Unknown Error',
                stack: event.error ? event.error.stack : '',
                context: {
                    type: 'uncaught_exception',
                    event_type: 'error'
                }
            });
        });
        
        // Capture unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.logError({
                message: `Unhandled Promise Rejection: ${event.reason}`,
                source: 'promise',
                line: 0,
                column: 0,
                error: event.reason ? event.reason.toString() : 'Promise Rejection',
                stack: event.reason && event.reason.stack ? event.reason.stack : '',
                context: {
                    type: 'unhandled_promise_rejection',
                    reason: event.reason
                }
            });
        });
        
        // Monitor network status
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.flushErrorQueue();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
        });
        
        // Capture AJAX/fetch errors by wrapping fetch
        this.wrapFetch();
        
        // Capture form submission errors
        this.monitorFormSubmissions();
        
        console.log('Error Logger initialized');
    }
    
    /**
     * Log an error to the backend
     */
    async logError(errorData) {
        const payload = {
            ...errorData,
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString(),
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            screen: {
                width: screen.width,
                height: screen.height
            }
        };
        
        if (this.isOnline) {
            try {
                await this.sendToBackend(`${this.apiEndpoint}/frontend-error`, payload);
            } catch (error) {
                console.warn('Failed to send error to backend:', error);
                this.queueError(payload);
            }
        } else {
            this.queueError(payload);
        }
    }
    
    /**
     * Log a warning to the backend
     */
    async logWarning(message, context = {}) {
        const payload = {
            message,
            context,
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        };
        
        if (this.isOnline) {
            try {
                await this.sendToBackend(`${this.apiEndpoint}/frontend-warning`, payload);
            } catch (error) {
                console.warn('Failed to send warning to backend:', error);
            }
        }
    }
    
    /**
     * Log info message to the backend
     */
    async logInfo(message, context = {}) {
        const payload = {
            message,
            context,
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        };
        
        if (this.isOnline) {
            try {
                await this.sendToBackend(`${this.apiEndpoint}/frontend-info`, payload);
            } catch (error) {
                console.warn('Failed to send info to backend:', error);
            }
        }
    }
    
    /**
     * Send data to backend with retry logic
     */
    async sendToBackend(url, data, retryCount = 0) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            if (retryCount < this.maxRetries) {
                await this.delay(this.retryDelay * (retryCount + 1));
                return this.sendToBackend(url, data, retryCount + 1);
            }
            throw error;
        }
    }
    
    /**
     * Queue error for later sending when online
     */
    queueError(errorData) {
        this.errorQueue.push(errorData);
        
        // Limit queue size to prevent memory issues
        if (this.errorQueue.length > 50) {
            this.errorQueue.shift(); // Remove oldest error
        }
        
        // Store in localStorage for persistence
        try {
            localStorage.setItem('errorQueue', JSON.stringify(this.errorQueue));
        } catch (e) {
            console.warn('Failed to store error queue in localStorage:', e);
        }
    }
    
    /**
     * Flush queued errors when back online
     */
    async flushErrorQueue() {
        // Load from localStorage
        try {
            const stored = localStorage.getItem('errorQueue');
            if (stored) {
                const storedErrors = JSON.parse(stored);
                this.errorQueue = [...this.errorQueue, ...storedErrors];
                localStorage.removeItem('errorQueue');
            }
        } catch (e) {
            console.warn('Failed to load error queue from localStorage:', e);
        }
        
        // Send queued errors
        const errors = [...this.errorQueue];
        this.errorQueue = [];
        
        for (const error of errors) {
            try {
                await this.sendToBackend(`${this.apiEndpoint}/frontend-error`, error);
                await this.delay(100); // Small delay between requests
            } catch (e) {
                console.warn('Failed to send queued error:', e);
                this.queueError(error); // Re-queue if failed
            }
        }
    }
    
    /**
     * Wrap fetch to capture AJAX errors
     */
    wrapFetch() {
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                // Log failed HTTP requests
                if (!response.ok) {
                    this.logWarning(`HTTP Request Failed: ${response.status} ${response.statusText}`, {
                        type: 'http_error',
                        url: args[0],
                        status: response.status,
                        statusText: response.statusText,
                        method: args[1]?.method || 'GET'
                    });
                }
                
                return response;
            } catch (error) {
                // Log network errors
                this.logError({
                    message: `Network Error: ${error.message}`,
                    source: 'fetch',
                    line: 0,
                    column: 0,
                    error: error.toString(),
                    stack: error.stack || '',
                    context: {
                        type: 'network_error',
                        url: args[0],
                        method: args[1]?.method || 'GET'
                    }
                });
                
                throw error;
            }
        };
    }
    
    /**
     * Monitor form submissions for errors
     */
    monitorFormSubmissions() {
        document.addEventListener('submit', (event) => {
            const form = event.target;
            if (form.tagName === 'FORM') {
                // Log form submission attempt
                this.logInfo('Form submission started', {
                    type: 'form_submission',
                    form_id: form.id,
                    form_action: form.action,
                    form_method: form.method
                });
                
                // Monitor for form validation errors
                setTimeout(() => {
                    const errors = form.querySelectorAll('.error, .invalid, [aria-invalid="true"]');
                    if (errors.length > 0) {
                        this.logWarning('Form validation errors detected', {
                            type: 'form_validation_error',
                            form_id: form.id,
                            error_count: errors.length,
                            errors: Array.from(errors).map(el => ({
                                element: el.tagName,
                                name: el.name,
                                message: el.textContent || el.title || 'Unknown error'
                            }))
                        });
                    }
                }, 100);
            }
        });
    }
    
    /**
     * Utility function for delays
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Manual error logging for specific components
     */
    logComponentError(component, action, error, context = {}) {
        this.logError({
            message: `Component Error in ${component}: ${error.message || error}`,
            source: component,
            line: 0,
            column: 0,
            error: error.toString(),
            stack: error.stack || '',
            context: {
                type: 'component_error',
                component,
                action,
                ...context
            }
        });
    }
    
    /**
     * Log user interaction errors
     */
    logUserInteractionError(interaction, error, context = {}) {
        this.logError({
            message: `User Interaction Error: ${interaction} - ${error.message || error}`,
            source: 'user_interaction',
            line: 0,
            column: 0,
            error: error.toString(),
            stack: error.stack || '',
            context: {
                type: 'user_interaction_error',
                interaction,
                ...context
            }
        });
    }
}

// Initialize error logger when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.errorLogger = new ErrorLogger();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorLogger;
}
