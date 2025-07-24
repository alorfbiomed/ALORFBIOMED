/**
 * Trainer Synchronization Module
 * 
 * This module provides centralized trainer data management and real-time synchronization
 * between the Machine Assignment and Training sections of the ALORF BIOMED application.
 * 
 * Features:
 * - Centralized trainer data fetching from the TrainerService API
 * - Real-time synchronization across multiple sections
 * - Event-driven updates when trainer data changes
 * - Backward compatibility with existing trainer dropdown implementations
 */

class TrainerSync {
    constructor() {
        this.trainers = [];
        this.trainerData = [];
        this.listeners = new Set();
        this.isInitialized = false;
        
        // Bind methods to preserve context
        this.refreshTrainers = this.refreshTrainers.bind(this);
        this.handleTrainerDataChanged = this.handleTrainerDataChanged.bind(this);
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    /**
     * Initialize the trainer synchronization system
     */
    async init() {
        if (this.isInitialized) {
            return this.trainers;
        }
        
        console.log('TrainerSync: Initializing trainer synchronization...');
        await this.refreshTrainers();
        this.isInitialized = true;
        
        return this.trainers;
    }
    
    /**
     * Fetch latest trainer data from the API
     */
    async refreshTrainers() {
        try {
            console.log('TrainerSync: Fetching trainer data from API...');
            const response = await fetch('/api/trainers/dropdown');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.trainerData = await response.json();
            
            // Extract trainer names for backward compatibility
            this.trainers = this.trainerData.map(trainer => trainer.value || trainer.name);
            
            console.log('TrainerSync: Trainers refreshed:', this.trainers);
            
            // Notify all listeners
            this.notifyListeners();
            
            // Dispatch global event
            window.dispatchEvent(new CustomEvent('trainersUpdated', {
                detail: { 
                    trainers: this.trainers, 
                    trainerData: this.trainerData 
                }
            }));
            
            return this.trainers;
            
        } catch (error) {
            console.error('TrainerSync: Error refreshing trainers:', error);
            return this.trainers; // Return existing trainers on error
        }
    }
    
    /**
     * Get current trainer names (for backward compatibility)
     */
    getTrainers() {
        return this.trainers;
    }
    
    /**
     * Get current trainer data objects
     */
    getTrainerData() {
        return this.trainerData;
    }
    
    /**
     * Add a listener for trainer updates
     */
    addListener(callback) {
        this.listeners.add(callback);
    }
    
    /**
     * Remove a listener
     */
    removeListener(callback) {
        this.listeners.delete(callback);
    }
    
    /**
     * Notify all registered listeners
     */
    notifyListeners() {
        this.listeners.forEach(callback => {
            try {
                callback(this.trainers, this.trainerData);
            } catch (error) {
                console.error('TrainerSync: Error in listener callback:', error);
            }
        });
    }
    
    /**
     * Set up event listeners for trainer data changes
     */
    setupEventListeners() {
        // Listen for trainer data changes from Machine Assignment section
        window.addEventListener('trainerDataChanged', this.handleTrainerDataChanged);
    }
    
    /**
     * Handle trainer data change events
     */
    handleTrainerDataChanged(event) {
        console.log('TrainerSync: Received trainerDataChanged event:', event.detail);
        
        // Refresh trainer data when changes are detected
        this.refreshTrainers();
    }
    
    /**
     * Clean up event listeners
     */
    destroy() {
        window.removeEventListener('trainerDataChanged', this.handleTrainerDataChanged);
        this.listeners.clear();
        this.isInitialized = false;
    }
}

// Create global instance
window.trainerSync = new TrainerSync();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.trainerSync.init();
    });
} else {
    // DOM is already ready
    window.trainerSync.init();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TrainerSync;
}
