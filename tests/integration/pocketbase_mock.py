
class PocketBaseMock:
    """
    Mock accessing a collection in PocketBase.
    
    Args:
        name (str): The name of the collection to access.

    Returns:
        UsersCollectionMock: A mock collection object for the "users" collection.

    Raises:
        ValueError: If the collection name is not "users".
    """
    def collection(self, name):
        if name != "users":
            raise ValueError(f"Unknown collection: {name}")
        return UsersCollectionMock()


class UsersCollectionMock:
    """
    Mock authenticating a user with email and password.

    Args:
        email (str): The user's email.
        password (str): The user's password.

    Returns:
        AuthResponseMock: A mock authentication response object.

    Raises:
        Exception: If the password does not match the expected test password.
    """
    def auth_with_password(self, email, password):
        if password != "12345678":
            raise Exception("Invalid credentials")

        return AuthResponseMock(email)

class AuthResponseMock:
    """
    Mock a fake authentication response.

    Args:
        email (str): The email of the authenticated user.
    """
    def __init__(self, email):
        self.token = "fake-token"
        self.record = {
            "id": "user123",
            "email": email,
            "username": email.split("@")[0],
        }
