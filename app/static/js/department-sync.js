/**
 * Global Department Synchronization System
 * 
 * This module provides real-time synchronization of department dropdowns
 * across all forms in the application. When departments are created, updated,
 * or deleted in the Department Management tab, all dropdown lists are
 * automatically updated without requiring page refreshes.
 */

class DepartmentSync {
    constructor() {
        this.departments = [];
        this.registeredDropdowns = new Map();
        this.init();
    }

    init() {
        // Listen for department update events
        document.addEventListener('departmentsUpdated', (event) => {
            this.handleDepartmentUpdate(event.detail);
        });

        // Listen for cross-tab synchronization
        window.addEventListener('storage', (event) => {
            if (event.key === 'departmentsData' && event.newValue) {
                try {
                    const data = JSON.parse(event.newValue);
                    if (data.departments && Array.isArray(data.departments)) {
                        this.departments = data.departments;
                        this.updateAllDropdowns();
                        console.log('DepartmentSync: Synchronized from another tab');
                    }
                } catch (error) {
                    console.error('DepartmentSync: Error parsing localStorage data:', error);
                }
            }
        });

        // Load initial departments from API if not already loaded
        this.loadInitialDepartments();
    }

    /**
     * Load departments from API if not already available
     */
    async loadInitialDepartments() {
        // Check if departments are already available globally
        if (window.getCurrentDepartments && window.getCurrentDepartments().length > 0) {
            this.departments = window.getCurrentDepartments();
            return;
        }

        // Check localStorage first
        try {
            const stored = localStorage.getItem('departmentsData');
            if (stored) {
                const data = JSON.parse(stored);
                if (data.departments && Array.isArray(data.departments)) {
                    this.departments = data.departments;
                    this.updateAllDropdowns();
                    return;
                }
            }
        } catch (error) {
            console.error('DepartmentSync: Error reading from localStorage:', error);
        }

        // Fetch from API as fallback
        try {
            const response = await fetch('/api/departments');
            if (response.ok) {
                this.departments = await response.json();
                this.updateAllDropdowns();
                console.log('DepartmentSync: Loaded departments from API');
            }
        } catch (error) {
            console.error('DepartmentSync: Error loading departments from API:', error);
        }
    }

    /**
     * Register a dropdown for automatic synchronization
     * @param {HTMLSelectElement} selectElement - The select element to register
     * @param {Object} options - Configuration options
     */
    registerDropdown(selectElement, options = {}) {
        if (!selectElement || !selectElement.id) {
            console.warn('DepartmentSync: Cannot register dropdown without ID');
            return;
        }

        const config = {
            defaultOption: options.defaultOption || '<option value="">Select Department</option>',
            useId: options.useId || false, // Whether to use dept.id or dept.department_name as value
            preserveSelection: options.preserveSelection !== false, // Default to true
            customFilter: options.customFilter || null, // Function to filter departments
            ...options
        };

        this.registeredDropdowns.set(selectElement.id, {
            element: selectElement,
            config: config
        });

        // Update immediately if departments are available
        if (this.departments.length > 0) {
            this.updateDropdown(selectElement.id);
        }

        console.log(`DepartmentSync: Registered dropdown #${selectElement.id}`);
    }

    /**
     * Unregister a dropdown
     * @param {string} dropdownId - The ID of the dropdown to unregister
     */
    unregisterDropdown(dropdownId) {
        this.registeredDropdowns.delete(dropdownId);
        console.log(`DepartmentSync: Unregistered dropdown #${dropdownId}`);
    }

    /**
     * Handle department update events
     * @param {Object} detail - Event detail containing departments data
     */
    handleDepartmentUpdate(detail) {
        if (detail.departments && Array.isArray(detail.departments)) {
            this.departments = detail.departments;
            this.updateAllDropdowns();
            console.log('DepartmentSync: Updated from event');
        }
    }

    /**
     * Update all registered dropdowns
     */
    updateAllDropdowns() {
        this.registeredDropdowns.forEach((dropdown, id) => {
            this.updateDropdown(id);
        });
    }

    /**
     * Update a specific dropdown
     * @param {string} dropdownId - The ID of the dropdown to update
     */
    updateDropdown(dropdownId) {
        const dropdown = this.registeredDropdowns.get(dropdownId);
        if (!dropdown || !dropdown.element) {
            return;
        }

        const { element, config } = dropdown;
        const currentValue = config.preserveSelection ? element.value : '';

        // Clear and add default option
        element.innerHTML = config.defaultOption;

        // Filter departments if custom filter is provided
        let departmentsToShow = this.departments;
        if (config.customFilter && typeof config.customFilter === 'function') {
            departmentsToShow = this.departments.filter(config.customFilter);
        }

        // Add department options
        departmentsToShow.forEach(dept => {
            const option = document.createElement('option');
            option.value = config.useId ? dept.id : dept.department_name;
            option.textContent = dept.department_name;
            element.appendChild(option);
        });

        // Restore previous selection if it still exists
        if (currentValue && config.preserveSelection) {
            element.value = currentValue;
        }

        console.log(`DepartmentSync: Updated dropdown #${dropdownId} with ${departmentsToShow.length} departments`);
    }

    /**
     * Get current departments
     * @returns {Array} Current departments array
     */
    getDepartments() {
        return this.departments;
    }

    /**
     * Manually trigger update of all dropdowns
     */
    refresh() {
        this.updateAllDropdowns();
    }
}

// Create global instance
window.DepartmentSync = window.DepartmentSync || new DepartmentSync();

// Convenience functions for backward compatibility
window.registerDepartmentDropdown = function(selectElement, options = {}) {
    return window.DepartmentSync.registerDropdown(selectElement, options);
};

window.unregisterDepartmentDropdown = function(dropdownId) {
    return window.DepartmentSync.unregisterDropdown(dropdownId);
};

window.refreshDepartmentDropdowns = function() {
    return window.DepartmentSync.refresh();
};

console.log('DepartmentSync: Module loaded and ready');
