console.log('equipment_list.js loaded');

// Add selected class style only if not already added
if (!document.getElementById('equipment-table-styles')) {
    const style = document.createElement('style');
    style.id = 'equipment-table-styles';
    style.textContent = `
        .equipment-table tr.selected {
            background-color: #e2e6ea !important;
        }
        .item-checkbox:checked {
            background-color: #0d6efd;
            border-color: #0d6efd;
        }
    `;
    document.head.appendChild(style);
}

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page with equipment table
    const tableBody = document.querySelector('.equipment-table tbody');

    if (!tableBody) {
        console.log('No equipment table found on this page, skipping equipment_list.js initialization');
        return;
    }

    // UI Elements - Updated for new advanced filtering system
    const selectAllCheckbox = document.getElementById('selectAll');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const selectedCountSpan = document.getElementById('selectedCount');

    // Advanced filter elements
    const columnFilters = document.querySelectorAll('.column-filter');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const clearAllFiltersBtn = document.getElementById('clearAllFilters');

    let sortDirection = 1;
    let lastSortColumn = '';

    console.log('Equipment list initialized with advanced filtering system');
    console.log('Found column filters:', columnFilters.length);

    // Event listeners for advanced filters
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', updateTable);
    }

    if (clearAllFiltersBtn) {
        clearAllFiltersBtn.addEventListener('click', clearAllFilters);
    }

    // Add event listeners to all column filters for real-time filtering
    columnFilters.forEach(filter => {
        filter.addEventListener('input', debounce(updateTable, 300));
        filter.addEventListener('change', updateTable);
    });

    // Initialize table display and attach event listeners
    attachCheckboxEventListeners();
    updateBulkDeleteButton();
    updateRecordCounter();

    console.log('Equipment list initialization complete');



    // Updated table filtering function for advanced filters
    function updateTable() {
        try {
            console.log('Updating table with advanced filters');

            const rows = Array.from(tableBody.getElementsByTagName('tr'));

            // Get all active filters
            const activeFilters = {};
            columnFilters.forEach(filter => {
                const column = filter.getAttribute('data-column');
                const value = filter.value.trim();
                if (value) {
                    activeFilters[column] = value.toLowerCase();
                }
            });

            console.log('Active filters:', activeFilters);

            // Reset select all checkbox
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = false;
            }

            // Apply filters to each row
            rows.forEach(row => {
                let showRow = true;

                // Check each active filter
                for (const [column, filterValue] of Object.entries(activeFilters)) {
                    const cellValue = getCellValueByColumn(row, column);
                    if (!cellValue.toLowerCase().includes(filterValue)) {
                        showRow = false;
                        break;
                    }
                }

                row.style.display = showRow ? '' : 'none';
            });

            // Count visible rows and update display
            const visibleRows = rows.filter(row => row.style.display !== 'none');
            console.log(`Filtered results: ${visibleRows.length} visible rows`);

            // Update record counter
            updateRecordCounter();

            // Show no results message if needed
            if (visibleRows.length === 0) {
                const colspan = tableBody.querySelector('tr')?.cells.length || 16;
                const noResultsRow = document.createElement('tr');
                noResultsRow.innerHTML = `<td colspan="${colspan}" class="text-center text-muted py-4">
                    <i class="fas fa-search me-2"></i>No equipment found matching the current filters.
                    <br><small>Try adjusting your filter criteria.</small>
                </td>`;
                tableBody.appendChild(noResultsRow);
            }

            // Reattach checkbox event listeners
            attachCheckboxEventListeners();
            updateBulkDeleteButton();

            // Log successful table update
            if (window.errorLogger) {
                window.errorLogger.logInfo('Table filtering completed successfully', {
                    component: 'equipment_list',
                    action: 'updateTable',
                    active_filters: Object.keys(activeFilters).length,
                    visible_rows: visibleRows.length,
                    total_rows: rows.length
                });
            }

        } catch (error) {
            console.error('Error in updateTable:', error);

            // Log error to backend
            if (window.errorLogger) {
                window.errorLogger.logComponentError('equipment_list', 'updateTable', error, {
                    total_rows: tableBody ? tableBody.getElementsByTagName('tr').length : 0,
                    filters_count: columnFilters ? columnFilters.length : 0
                });
            }
        }
    }

    // Helper function to get cell value by column name
    function getCellValueByColumn(row, columnName) {
        // Determine data type from URL
        const dataType = window.location.pathname.includes('ppm') ? 'ppm' : 'ocm';

        // Column mapping for different data types
        const columnMap = dataType === 'ppm' ? {
            'Department': 2,
            'Name': 3,
            'Model': 4,
            'Serial': 5,
            'Manufacturer': 6,
            'Log_Number': 7,
            'Installation_Date': 8,
            'Warranty_End': 9
        } : {
            'Department': 2,
            'Name': 3,
            'Model': 4,
            'Serial': 5,
            'Manufacturer': 6,
            'Log_Number': 7,
            'Installation_Date': 8,
            'Warranty_End': 9,
            'Service_Date': 10,
            'Next_Maintenance': 11,
            'Engineer': 12,
            'Status': 13
        };

        const columnIndex = columnMap[columnName];
        if (columnIndex !== undefined && row.cells[columnIndex]) {
            return row.cells[columnIndex].textContent.trim();
        }
        return '';
    }

    // Clear all filters function
    function clearAllFilters() {
        columnFilters.forEach(filter => {
            filter.value = '';
        });
        updateTable();
        console.log('All filters cleared');
    }

    // Debounce function for performance
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Checkbox functionality
    function attachCheckboxEventListeners() {
        const itemCheckboxes = document.querySelectorAll('.item-checkbox');

        selectAllCheckbox?.addEventListener('change', function() {
            const visibleRows = Array.from(tableBody.querySelectorAll('tr'))
                .filter(row => row.style.display !== 'none');
            
            visibleRows.forEach(row => {
                const checkbox = row.querySelector('.item-checkbox');
                if (checkbox) {
                    checkbox.checked = selectAllCheckbox.checked;
                    toggleRowSelection(checkbox);
                }
            });
        });

        itemCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                if (!checkbox.checked && selectAllCheckbox) {
                    selectAllCheckbox.checked = false;
                }
                toggleRowSelection(checkbox);
            });
        });
    }

    function toggleRowSelection(checkbox) {
        const row = checkbox.closest('tr');
        if (row) {
            if (checkbox.checked) {
                row.classList.add('selected');
            } else {
                row.classList.remove('selected');
            }
        }
        updateBulkDeleteButton();
    }

    function updateBulkDeleteButton() {
        const checkedCount = document.querySelectorAll('.item-checkbox:checked').length;
        console.log('updateBulkDeleteButton called, checkedCount:', checkedCount);

        if (bulkDeleteBtn) {
            bulkDeleteBtn.style.display = checkedCount > 0 ? 'inline-block' : 'none';
            bulkDeleteBtn.textContent = `Delete Selected (${checkedCount})`;
        }
        if (selectedCountSpan) {
            selectedCountSpan.textContent = checkedCount;
        }
    }

    function updateRecordCounter() {
        // Use more specific selector for equipment table only
        const equipmentTable = document.querySelector('.equipment-table tbody');
        const visibleRows = equipmentTable ? equipmentTable.querySelectorAll('tr:not([style*="display: none"])') : [];
        const totalRecordsCount = document.getElementById('totalRecordsCount');

        console.log(`updateRecordCounter: Found ${visibleRows.length} visible rows`);

        if (totalRecordsCount) {
            if (visibleRows.length > 0) {
                // Update the displayed count based on visible rows
                const currentCount = visibleRows.length;
                totalRecordsCount.textContent = `${currentCount} records (page may need refresh for accurate count)`;
                console.log(`Updated record counter to: ${currentCount}`);
            } else {
                // Don't hide the counter, just update it to show 0
                totalRecordsCount.textContent = `0 records (page may need refresh for accurate count)`;
                console.log('Updated record counter to: 0');
            }
        }
    }

    // Initial setup
    attachCheckboxEventListeners();
    
    // Bulk delete functionality
    bulkDeleteBtn?.addEventListener('click', async function() {
        const checkedBoxes = document.querySelectorAll('.item-checkbox:checked');
        const selectedSerials = Array.from(checkedBoxes).map(checkbox => {
            return checkbox.dataset.serial;
        });
        
        if (!selectedSerials.length) {
            alert('Please select at least one item to delete.');
            return;
        }

        // Enhanced confirmation dialog
        const confirmMessage = selectedSerials.length === 1
            ? `Are you sure you want to delete the selected record?\n\nSerial: ${selectedSerials[0]}\n\nThis action cannot be undone.`
            : `Are you sure you want to delete ${selectedSerials.length} selected records?\n\nThis action cannot be undone.`;

        if (!confirm(confirmMessage)) {
            return;
        }

        // Show enhanced progress indicator
        const originalText = bulkDeleteBtn.textContent;
        bulkDeleteBtn.disabled = true;
        bulkDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

        // Add progress message for large operations
        let progressMessage = null;
        if (selectedSerials.length > 50) {
            progressMessage = document.createElement('div');
            progressMessage.className = 'alert alert-info mt-2';
            progressMessage.innerHTML = `<i class="fas fa-info-circle"></i> Deleting ${selectedSerials.length} records, please wait...`;
            bulkDeleteBtn.parentNode.insertBefore(progressMessage, bulkDeleteBtn.nextSibling);
        }

        const startTime = Date.now();
        console.log(`Starting bulk delete of ${selectedSerials.length} records`);

        // Log bulk delete start
        if (window.errorLogger) {
            window.errorLogger.logInfo('Bulk delete operation started', {
                component: 'equipment_list',
                action: 'bulk_delete',
                data_type: dataType,
                record_count: selectedSerials.length,
                serials: selectedSerials.slice(0, 10) // Log first 10 serials for debugging
            });
        }

        try {
            const response = await fetch(`/api/bulk_delete/${dataType}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ serials: selectedSerials })
            });

            const result = await response.json();
            const endTime = Date.now();
            const duration = ((endTime - startTime) / 1000).toFixed(2);
            console.log(`Bulk delete completed in ${duration} seconds`);

            if (result.success) {
                // Remove deleted rows from the table
                checkedBoxes.forEach(checkbox => {
                    const row = checkbox.closest('tr');
                    if (row) {
                        row.remove();
                    }
                });

                // Log successful bulk delete
                if (window.errorLogger) {
                    window.errorLogger.logInfo('Bulk delete operation completed successfully', {
                        component: 'equipment_list',
                        action: 'bulk_delete',
                        data_type: dataType,
                        record_count: selectedSerials.length,
                        duration_seconds: parseFloat(duration),
                        deleted_count: result.deleted_count || selectedSerials.length
                    });
                }

                // Update counters and record display
                updateBulkDeleteButton();
                updateRecordCounter();

                // Show enhanced success message with performance info
                const message = `✅ Successfully deleted ${result.deleted_count} record(s) in ${duration}s.` +
                    (result.not_found > 0 ? ` ${result.not_found} record(s) were not found.` : '');
                alert(message);

                // Check if all records on current page were deleted
                const equipmentTable = document.querySelector('.equipment-table tbody');
                const remainingRows = equipmentTable ? equipmentTable.querySelectorAll('tr:not([style*="display: none"])') : [];

                console.log(`Remaining rows after bulk delete: ${remainingRows.length}`);

                // Update record counters after successful bulk delete
                updateRecordCounter();
            } else {
                alert(`Failed to delete records: ${result.message || 'Unknown error'}`);

                // Log bulk delete failure
                if (window.errorLogger) {
                    window.errorLogger.logWarning('Bulk delete operation failed', {
                        component: 'equipment_list',
                        action: 'bulk_delete',
                        data_type: dataType,
                        record_count: selectedSerials.length,
                        error_message: result.message || 'Unknown error',
                        response_status: response?.status
                    });
                }
            }
        } catch (error) {
            console.error('Error during bulk delete:', error);
            alert('Error occurred while deleting records. Please try again.');

            // Log bulk delete error
            if (window.errorLogger) {
                window.errorLogger.logUserInteractionError('bulk_delete', error, {
                    component: 'equipment_list',
                    data_type: dataType,
                    record_count: selectedSerials.length,
                    duration_before_error: ((Date.now() - startTime) / 1000).toFixed(2)
                });
            }
        } finally {
            // Clean up progress indicators
            if (progressMessage) {
                progressMessage.remove();
            }

            // Re-enable the button with original text
            bulkDeleteBtn.disabled = false;
            bulkDeleteBtn.innerHTML = originalText;

            // Update button text with current selection count
            const currentSelection = document.querySelectorAll('.item-checkbox:checked').length;
            if (currentSelection > 0) {
                bulkDeleteBtn.textContent = `Delete Selected (${currentSelection})`;
            }
        }
    });

    // Single delete functionality with progress indicators
    document.addEventListener('click', async function(event) {
        if (event.target.classList.contains('single-delete-btn')) {
            const button = event.target;
            const serial = button.dataset.serial;
            const dataType = button.dataset.dataType;

            if (!confirm(`Are you sure you want to delete this record?\n\nSerial: ${serial}\n\nThis action cannot be undone.`)) {
                return;
            }

            // Show progress indicator
            const originalText = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

            const startTime = Date.now();
            console.log(`Starting single delete of ${dataType} record: ${serial}`);

            try {
                const response = await fetch(`/api/equipment/${dataType}/${encodeURIComponent(serial)}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                const result = await response.json();
                const endTime = Date.now();
                const duration = ((endTime - startTime) / 1000).toFixed(2);
                console.log(`Single delete completed in ${duration} seconds`);

                if (response.ok) {
                    // Remove the row from the table
                    const row = button.closest('tr');
                    if (row) {
                        row.remove();
                    }

                    // Update record counter
                    updateRecordCounter();

                    // Show success message
                    alert(`✅ Successfully deleted record ${serial} in ${duration}s.`);

                } else {
                    alert(`Failed to delete record: ${result.error || 'Unknown error'}`);
                    // Reset button state
                    button.disabled = false;
                    button.innerHTML = originalText;
                }

            } catch (error) {
                console.error('Error during single delete:', error);
                alert('Error occurred while deleting record. Please try again.');

                // Reset button state
                button.disabled = false;
                button.innerHTML = originalText;
            }
        }
    });
});