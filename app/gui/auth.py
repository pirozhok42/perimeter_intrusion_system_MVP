ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin"

def check_credentials(login: str, password: str) -> bool:
    return login.strip() == ADMIN_LOGIN and password == ADMIN_PASSWORD
