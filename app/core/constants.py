"""Application-wide constants.

Every string or number that would otherwise be repeated ("magic values") lives here,
so it is defined once, easy to find, and safe to change.
"""

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
AUTH_PREFIX = "/auth"
TODOS_PREFIX = "/todos"
ADMIN_PREFIX = "/admin"
USERS_PREFIX = "/user"
HEALTH_PATH = "/health"

AUTH_TAG = "auth"
TODOS_TAG = "todos"
ADMIN_TAG = "admin"
USERS_TAG = "user"
HEALTH_TAG = "health"

# Relative URL the OAuth2 "Authorize" button in Swagger UI posts to.
TOKEN_URL = "auth/token"

# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
ROLE_ADMIN = "admin"
ROLE_USER = "user"

# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
JWT_ALGORITHM = "HS256"
TOKEN_TYPE_BEARER = "bearer"

CLAIM_SUBJECT = "sub"
CLAIM_USER_ID = "user_id"
CLAIM_ROLE = "role"
CLAIM_EXPIRES = "exp"

# ---------------------------------------------------------------------------
# Validation limits
# ---------------------------------------------------------------------------
TODO_TITLE_MIN_LENGTH = 3
TODO_TITLE_MAX_LENGTH = 100
TODO_DESCRIPTION_MIN_LENGTH = 3
TODO_DESCRIPTION_MAX_LENGTH = 200
TODO_PRIORITY_MIN = 1
TODO_PRIORITY_MAX = 3

PASSWORD_MIN_LENGTH = 6
PHONE_NUMBER_MIN_LENGTH = 10
PHONE_NUMBER_MAX_LENGTH = 20

# ---------------------------------------------------------------------------
# Response messages
# ---------------------------------------------------------------------------
HEALTHY_STATUS = "healthy"

COULD_NOT_VALIDATE_CREDENTIALS = "Could not validate credentials"
INVALID_CREDENTIALS = "Invalid credentials"
INSUFFICIENT_PERMISSIONS = "Insufficient permissions"
USER_ALREADY_EXISTS = "Username or email already exists"
USER_NOT_FOUND = "User not found"
TODO_NOT_FOUND = "Todo with id {todo_id} not found"
INCORRECT_CURRENT_PASSWORD = "Incorrect current password"
PASSWORD_MUST_DIFFER = "New password must differ from current password"

USER_CREATED = "User created successfully"
PASSWORD_CHANGED = "Password changed successfully"
PHONE_NUMBER_UPDATED = "Phone number updated successfully"
