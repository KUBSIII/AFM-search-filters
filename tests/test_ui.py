from fastapi.testclient import TestClient


def test_ui_page_returns_html(client: TestClient) -> None:
    response = client.get('/ui')

    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert 'AFM Search Console' in response.text
    assert 'id="filters-form"' in response.text


def test_root_redirects_to_ui(client: TestClient) -> None:
    response = client.get('/', follow_redirects=False)

    assert response.status_code == 307
    assert response.headers['location'] == '/ui'
