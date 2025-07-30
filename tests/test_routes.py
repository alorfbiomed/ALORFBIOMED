"""
Test cases for application routes.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from io import BytesIO

from app import create_app


class TestRoutes:
    """Test cases for application routes."""

    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = create_app()
        app.config['TESTING'] = True
        app.config['LOGIN_DISABLED'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()

    def test_index_route(self, client):
        """Test the index route."""
        response = client.get('/')
        
        assert response.status_code == 200
        assert b'ALORF BIOMED SYSTEM' in response.data

    def test_ppm_list_route(self, client):
        """Test the PPM list route."""
        with patch('app.services.data_service.DataService.get_all_entries') as mock_get:
            mock_get.return_value = [
                {
                    'SERIAL': 'TEST001',
                    'DEPARTMENT': 'X-RAY',
                    'NAME': 'Test Equipment',
                    'has_history': False
                }
            ]
            
            response = client.get('/equipment/ppm')
            
            assert response.status_code == 200
            assert b'PPM Equipment List' in response.data
            assert b'TEST001' in response.data

    def test_ocm_list_route(self, client):
        """Test the OCM list route."""
        with patch('app.services.data_service.DataService.get_all_entries') as mock_get:
            mock_get.return_value = [
                {
                    'SERIAL': 'OCM001',
                    'DEPARTMENT': 'SURGERY',
                    'NAME': 'Surgical Equipment',
                    'has_history': False
                }
            ]
            
            response = client.get('/equipment/ocm')
            
            assert response.status_code == 200
            assert b'OCM Equipment List' in response.data
            assert b'OCM001' in response.data

    def test_history_log_route(self, client):
        """Test the history log route."""
        with patch('app.services.history_service.HistoryService.get_all_history_notes') as mock_get:
            mock_get.return_value = []
            
            response = client.get('/equipment/history-log')
            
            assert response.status_code == 200
            assert b'History Log' in response.data

    def test_equipment_history_route(self, client):
        """Test individual equipment history route."""
        with patch('app.services.data_service.DataService.get_entry') as mock_get_equipment:
            with patch('app.services.history_service.HistoryService.get_history_notes_by_equipment') as mock_get_history:
                mock_get_equipment.return_value = {
                    'SERIAL': 'TEST001',
                    'NAME': 'Test Equipment',
                    'DEPARTMENT': 'X-RAY'
                }
                mock_get_history.return_value = []
                
                response = client.get('/equipment/ppm/TEST001/history')
                
                assert response.status_code == 200
                assert b'Equipment History' in response.data
                assert b'TEST001' in response.data

    def test_equipment_history_route_not_found(self, client):
        """Test equipment history route for non-existent equipment."""
        with patch('app.services.data_service.DataService.get_entry') as mock_get:
            mock_get.return_value = None
            
            response = client.get('/equipment/ppm/NONEXISTENT/history')
            
            assert response.status_code == 404

    def test_add_history_note_get(self, client):
        """Test GET request to add history note page."""
        with patch('app.services.data_service.DataService.get_entry') as mock_get:
            mock_get.return_value = {
                'SERIAL': 'TEST001',
                'NAME': 'Test Equipment',
                'DEPARTMENT': 'X-RAY'
            }
            
            response = client.get('/equipment/ppm/TEST001/history/add')
            
            assert response.status_code == 200
            assert b'Add History Note' in response.data

    def test_add_history_note_post(self, client):
        """Test POST request to add history note."""
        with patch('app.services.data_service.DataService.get_entry') as mock_get_equipment:
            with patch('app.services.history_service.HistoryService.create_history_note') as mock_create:
                mock_get_equipment.return_value = {
                    'SERIAL': 'TEST001',
                    'NAME': 'Test Equipment'
                }
                mock_create.return_value = MagicMock(id='new-note-id')
                
                response = client.post('/equipment/ppm/TEST001/history', data={
                    'note_text': 'Test history note'
                })
                
                # Should redirect after successful creation
                assert response.status_code == 302
                mock_create.assert_called_once()

    def test_machine_assignment_route(self, client):
        """Test machine assignment route."""
        response = client.get('/equipment/machine-assignment')
        
        assert response.status_code == 200
        assert b'Machine Assignment' in response.data

    def test_settings_route(self, client):
        """Test settings route."""
        response = client.get('/settings')
        
        assert response.status_code == 200
        assert b'Settings' in response.data

    def test_api_departments_get(self, client):
        """Test GET API for departments."""
        with patch('app.services.data_service.DataService.get_departments') as mock_get:
            mock_get.return_value = ['X-RAY', 'LABORATORY', 'SURGERY']
            
            response = client.get('/api/departments')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'departments' in data
            assert len(data['departments']) == 3

    def test_api_departments_post(self, client):
        """Test POST API for creating department."""
        with patch('app.services.department_service.DepartmentService.create_department') as mock_create:
            mock_create.return_value = MagicMock(id='dept-123', name='NEW-DEPT')
            
            response = client.post('/api/departments', 
                                 json={'name': 'NEW-DEPT', 'description': 'New Department'})
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['name'] == 'NEW-DEPT'

    def test_api_equipment_search(self, client):
        """Test API for equipment search."""
        with patch('app.services.data_service.DataService.search_entries') as mock_search:
            mock_search.return_value = [
                {
                    'SERIAL': 'TEST001',
                    'NAME': 'Test Equipment',
                    'DEPARTMENT': 'X-RAY'
                }
            ]
            
            response = client.get('/api/equipment/ppm/search?department=X-RAY')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 1
            assert data[0]['SERIAL'] == 'TEST001'

    def test_api_history_search(self, client):
        """Test API for history search."""
        with patch('app.services.history_service.HistoryService.search_history_notes') as mock_search:
            mock_search.return_value = []
            
            response = client.get('/api/history/search?search_text=maintenance')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)

    def test_api_invalid_endpoint(self, client):
        """Test API call to invalid endpoint."""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404

    def test_api_departments_machines_get(self, client):
        """Test GET API for department machines."""
        with patch('app.services.department_service.DepartmentService.get_machines_by_department') as mock_get:
            mock_get.return_value = ['MACHINE1', 'MACHINE2']
            
            response = client.get('/api/departments-machines/X-RAY/machines')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'machines' in data
            assert len(data['machines']) == 2

    def test_api_departments_machines_post(self, client):
        """Test POST API for adding machine to department."""
        with patch('app.services.department_service.DepartmentService.add_machine_to_department') as mock_add:
            mock_add.return_value = True
            
            response = client.post('/api/departments-machines/X-RAY/machines',
                                 json={'machine_name': 'NEW-MACHINE'})
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['message'] == 'Machine added successfully'

    def test_error_handling_500(self, client):
        """Test 500 error handling."""
        with patch('app.services.data_service.DataService.get_all_entries') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            response = client.get('/equipment/ppm')
            
            # Should handle the error gracefully
            assert response.status_code in [200, 500]  # Depending on error handling implementation

    def test_file_upload_route(self, client):
        """Test file upload route."""
        with patch('app.services.history_service.HistoryService.get_history_note_by_id') as mock_get_note:
            with patch('app.services.history_service.HistoryService.add_attachment_to_note') as mock_add_attachment:
                mock_get_note.return_value = MagicMock(id='note-123')
                mock_add_attachment.return_value = MagicMock(id='attachment-123')
                
                # Create a test file
                data = {
                    'file': (BytesIO(b'test file content'), 'test.txt')
                }
                
                response = client.post('/equipment/history/note-123/upload',
                                     data=data,
                                     content_type='multipart/form-data')
                
                # Should redirect after successful upload
                assert response.status_code in [200, 302]
