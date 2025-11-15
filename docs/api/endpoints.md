# API Endpoints Documentation

## Authentication Endpoints

### POST /api/v1/auth/login
Login user and receive JWT token

### POST /api/v1/auth/register
Register new user account

### POST /api/v1/auth/refresh
Refresh JWT token

## User Endpoints

### GET /api/v1/users/profile
Get current user profile

### PUT /api/v1/users/profile
Update user profile

### GET /api/v1/users/balance
Get user account balance

## Beneficiary Endpoints

### GET /api/v1/beneficiaries
List all beneficiaries for user

### POST /api/v1/beneficiaries
Add new beneficiary

### PUT /api/v1/beneficiaries/{id}
Update beneficiary details

### DELETE /api/v1/beneficiaries/{id}
Remove beneficiary

## Transaction Endpoints

### GET /api/v1/transactions
Get transaction history

### POST /api/v1/transactions/transfer
Initiate fund transfer

### GET /api/v1/transactions/{id}
Get transaction details

## Admin Endpoints

### POST /api/v1/admin/documents/upload
Upload compliance document

### GET /api/v1/admin/users
List all users (admin only)

### POST /api/v1/admin/users/{id}/credit
Credit user account

### POST /api/v1/admin/users/{id}/debit
Debit user account

## Chatbot Endpoints

### POST /api/v1/chat/message
Send message to chatbot

### GET /api/v1/chat/session
Get or create chat session
