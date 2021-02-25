class MockResponse:
    def __init__(self, content, status_code, headers={}):
        self.content = content
        self.status_code = status_code
        self.headers = headers
