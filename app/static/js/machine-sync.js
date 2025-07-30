/**
 * Machine Synchronization Module
 * Provides real-time synchronization of machine data between Machine Assignment and Training sections
 */

class MachineSync {
    constructor() {
        this.listeners = [];
        this.machineData = {};
        this.isInitialized = false;
        
        console.log('MachineSync: Initializing machine synchronization module');
    }

    /**
     * Initialize the machine sync system
     */
    async init() {
        try {
            console.log('MachineSync: Fetching initial machine data...');
            await this.refreshMachineData();
            this.isInitialized = true;
            console.log('MachineSync: Initialization complete');
            return this.machineData;
        } catch (error) {
            console.error('MachineSync: Failed to initialize:', error);
            throw error;
        }
    }

    /**
     * Fetch latest machine data from the API
     */
    async refreshMachineData() {
        try {
            console.log('MachineSync: Fetching machine data from API...');
            const response = await fetch('/api/departments-machines');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.machineData = await response.json();
            console.log('MachineSync: Machine data refreshed:', Object.keys(this.machineData).length, 'departments');
            
            // Notify all listeners
            this.notifyListeners();
            
            // Dispatch global event
            window.dispatchEvent(new CustomEvent('machinesUpdated', {
                detail: { 
                    machines: this.machineData,
                    timestamp: new Date().toISOString()
                }
            }));
            
            return this.machineData;
        } catch (error) {
            console.error('MachineSync: Error refreshing machine data:', error);
            throw error;
        }
    }

    /**
     * Add a machine to a department
     */
    async addMachine(department, machineName) {
        try {
            console.log(`MachineSync: Adding machine '${machineName}' to department '${department}'`);
            
            const response = await fetch(`/api/departments-machines/${encodeURIComponent(department)}/machines`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    machine_name: machineName
                })
            });

            const result = await response.json();

            if (response.ok) {
                // Success - refresh data and notify listeners
                await this.refreshMachineData();
                console.log(`MachineSync: Successfully added machine '${machineName}' to department '${department}'`);
                return { success: true, message: result.message };
            } else if (response.status === 409) {
                // Already exists - still refresh data to ensure consistency
                await this.refreshMachineData();
                console.log(`MachineSync: Machine '${machineName}' already exists in department '${department}'`);
                return { success: false, alreadyExists: true, message: result.error };
            } else {
                // Other error
                console.error(`MachineSync: Error adding machine:`, result.error);
                return { success: false, alreadyExists: false, message: result.error };
            }
        } catch (error) {
            console.error('MachineSync: Error adding machine:', error);
            return { success: false, alreadyExists: false, message: 'Network error occurred' };
        }
    }

    /**
     * Remove a machine from a department
     */
    async removeMachine(department, machineName) {
        try {
            console.log(`MachineSync: Removing machine '${machineName}' from department '${department}'`);

            const response = await fetch(`/api/departments-machines/${encodeURIComponent(department)}/machines/${encodeURIComponent(machineName)}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok) {
                // Success - refresh data and notify listeners
                await this.refreshMachineData();
                console.log(`MachineSync: Successfully removed machine '${machineName}' from department '${department}'`);
                return { success: true, message: result.message };
            } else {
                console.error(`MachineSync: Error removing machine:`, result.error);
                return { success: false, message: result.error };
            }
        } catch (error) {
            console.error('MachineSync: Error removing machine:', error);
            return { success: false, message: 'Network error occurred' };
        }
    }

    /**
     * Delete a machine completely from all departments
     */
    async deleteMachine(machineName) {
        try {
            console.log(`MachineSync: Deleting machine '${machineName}' from all departments`);

            const response = await fetch(`/api/machines/${encodeURIComponent(machineName)}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok) {
                // Success - refresh data and notify listeners
                await this.refreshMachineData();
                console.log(`MachineSync: Successfully deleted machine '${machineName}' from all departments`);
                return {
                    success: true,
                    message: result.message,
                    departmentsAffected: result.departments_affected,
                    trainingRecordsUpdated: result.training_records_updated
                };
            } else {
                console.error(`MachineSync: Error deleting machine:`, result.error);
                return { success: false, message: result.error };
            }
        } catch (error) {
            console.error('MachineSync: Error deleting machine:', error);
            return { success: false, message: 'Network error occurred' };
        }
    }

    /**
     * Get machines for a specific department
     */
    getMachinesForDepartment(department) {
        return this.machineData[department] || [];
    }

    /**
     * Get all machine data
     */
    getAllMachines() {
        return this.machineData;
    }

    /**
     * Register a listener for machine data updates
     */
    addListener(callback) {
        if (typeof callback === 'function') {
            this.listeners.push(callback);
            console.log('MachineSync: Listener registered, total listeners:', this.listeners.length);
            
            // If already initialized, call the listener immediately
            if (this.isInitialized) {
                callback(this.machineData);
            }
        }
    }

    /**
     * Remove a listener
     */
    removeListener(callback) {
        const index = this.listeners.indexOf(callback);
        if (index > -1) {
            this.listeners.splice(index, 1);
            console.log('MachineSync: Listener removed, total listeners:', this.listeners.length);
        }
    }

    /**
     * Notify all listeners of data updates
     */
    notifyListeners() {
        console.log('MachineSync: Notifying', this.listeners.length, 'listeners of machine data update');
        this.listeners.forEach(callback => {
            try {
                callback(this.machineData);
            } catch (error) {
                console.error('MachineSync: Error calling listener:', error);
            }
        });
    }

    /**
     * Force refresh machine data (useful for manual sync)
     */
    async forceRefresh() {
        console.log('MachineSync: Force refreshing machine data...');
        return await this.refreshMachineData();
    }
}

// Create global instance
window.machineSync = new MachineSync();

// Global convenience functions
window.addMachineToSync = async (department, machineName) => {
    return await window.machineSync.addMachine(department, machineName);
};

window.removeMachineFromSync = async (department, machineName) => {
    return await window.machineSync.removeMachine(department, machineName);
};

window.deleteMachineFromSync = async (machineName) => {
    return await window.machineSync.deleteMachine(machineName);
};

window.refreshMachineSync = async () => {
    return await window.machineSync.forceRefresh();
};

// Register for machine data updates
window.registerMachineListener = (callback) => {
    window.machineSync.addListener(callback);
};

console.log('MachineSync: Module loaded successfully');
