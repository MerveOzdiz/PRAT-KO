def test_app_initialization(app):
    assert app is not None
    assert app.config['TESTING'] is True

def test_categories_endpoint(client):
    response = client.get('/api/categories')
    assert response.status_code == 200
    assert isinstance(response.json, list)
