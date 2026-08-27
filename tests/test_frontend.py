def test_frontend_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Steam Cases" in response.text
    assert "/assets/app.js" in response.text


def test_frontend_assets(client):
    response = client.get("/assets/app.js")
    assert response.status_code == 200
    assert "loadCases" in response.text
