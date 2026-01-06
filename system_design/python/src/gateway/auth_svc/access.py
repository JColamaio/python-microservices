import os

import requests


def login(request):
    """Forward login request to auth service with basic auth credentials."""
    auth = request.authorization
    if not auth:
        return None, ("missing credentials", 401)

    basic_auth = (auth.username, auth.password)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login",
        auth=basic_auth,
        timeout=10,
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)


def validate_token(request):
    """Validate JWT token via auth service."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None, ("missing token", 401)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/validate",
        headers={"Authorization": auth_header},
        timeout=10,
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
