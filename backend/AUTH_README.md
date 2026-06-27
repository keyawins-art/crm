# JWT Authentication

## Environment variables
Set these in backend/.env:

SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

## Endpoints
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- POST /auth/logout
- GET /auth/me

## Usage
1. Register a user with POST /auth/register.
2. Copy the returned access_token and refresh_token.
3. Call /auth/me with:
   Authorization: Bearer <access_token>
