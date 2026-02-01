# MatruRaksha API Specification

## Base URL
`/api`

## Authentication (`/api/auth`)
Routes for user registration, login, and session management.

| Method | Endpoint | Purpose | Roles |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/signup` | Register a new user | ADMIN, DOCTOR, ASHA_WORKER |
| `POST` | `/auth/signin` | Login with email/password | All |
| `POST` | `/auth/signin/google` | Initiate Google OAuth | All |
| `POST` | `/auth/signout` | Sign out current user | Authenticated |
| `POST` | `/auth/refresh` | Refresh access token | All |
| `GET` | `/auth/me` | Get current user profile | Authenticated |
| `POST` | `/auth/update-profile` | Update user profile | Authenticated |
| `POST` | `/auth/upload-cert` | Upload doctor certification | DOCTOR |
| `POST` | `/auth/register-request` | Submit registration for approval | DOCTOR, ASHA_WORKER |
| `GET` | `/auth/register-requests` | List pending requests | ADMIN |
| `POST` | `/auth/register-requests/{id}/decision` | Approve/Reject request | ADMIN |

## Admin Management (`/api/admin`)
Routes for managing users, roles, and system statistics.

| Method | Endpoint | Purpose | Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/admin/stats` | Get dashboard statistics | ADMIN |
| `GET` | `/admin/full` | Get all admin data (mothers, doctors, workers) | ADMIN |
| `GET` | `/admin/users` | List all system users | ADMIN |
| `GET` | `/admin/users/role/{role}` | Filter users by role | ADMIN |
| `PUT` | `/admin/users/{id}/activate` | Activate user account | ADMIN |
| `PUT` | `/admin/users/{id}/deactivate` | Deactivate user account | ADMIN |
| `GET` | `/admin/doctors` | List doctors with stats | ADMIN |
| `PUT` | `/admin/doctors/{id}` | Update doctor details | ADMIN |
| `GET` | `/admin/asha-workers` | List ASHA workers with stats | ADMIN |
| `PUT` | `/admin/asha-workers/{id}` | Update ASHA worker details | ADMIN |
| `GET` | `/admin/mothers` | List all mothers | ADMIN |
| `POST` | `/admin/mothers/{id}/assign-asha` | Assign Mother to ASHA | ADMIN |
| `POST` | `/admin/mothers/{id}/assign-doctor` | Assign Mother to Doctor | ADMIN |

## Enhanced AI Features (`/api/enhanced` & `/api/ai`)
Advanced AI capabilities for context, reporting, and predictive health.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/enhanced/reports/analyze` | Analyze medical reports using Gemini |
| `POST` | `/api/enhanced/timeline/event` | Add health timeline event from interaction |
| `POST` | `/api/enhanced/memory/store` | Store user context/preferences |
| `POST` | `/api/enhanced/conversation/message` | Log AI conversation history |
| `POST` | `/api/enhanced/agent/query` | Query Contextual AI Agent |
| `POST` | `/api/enhanced/agent/create` | Initialize Agent for Mother |
| `POST` | `/api/ai/analyze/{mother_id}` | Trigger Risk Analysis |
| `POST` | `/api/ai/summary/{mother_id}` | Generate Health Summary |

## Postnatal Care (`/api/postnatal`)
Core tracking for mothers and children after delivery.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/postnatal/mothers` | List postnatal mothers (filtered) |
| `GET` | `/postnatal/children` | List children |
| `POST` | `/postnatal/children` | Register new child |
| `POST` | `/postnatal/assessments/mother` | Create mother postnatal assessment |
| `GET` | `/postnatal/assessments/mother/{id}` | Get mother's assessment history |
| `POST` | `/postnatal/assessments/child` | Create child health checkup |
| `GET` | `/postnatal/assessments/child/{id}` | Get child's checkup history |

## SantanRaksha Child Health (`/api/santanraksha`)
Specialized tracking for Growth (WHO Standards) and Vaccination (IAP Schedule).

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/santanraksha/vaccination/{child_id}/initialize` | Initialize IAP Vaccination Schedule |
| `GET` | `/santanraksha/vaccination/{child_id}` | Get vaccination record |
| `POST` | `/santanraksha/vaccination/mark-done` | Mark vaccine as given |
| `GET` | `/santanraksha/vaccination/schedule/standard` | Get standard schedule reference |
| `POST` | `/santanraksha/growth/record` | Add growth measurement (calcs Z-score) |
| `GET` | `/santanraksha/growth/{child_id}` | Get growth history with trends |
| `POST` | `/santanraksha/milestone/toggle` | Toggle developmental milestone |
| `GET` | `/santanraksha/milestone/{child_id}` | Get achieved milestones |


## Delivery Transition (`/api/delivery`)
Handling the critical delivery phase and system transition.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/delivery/complete` | Complete delivery, create child, transition mother |
| `GET` | `/delivery/status/{mother_id}` | Check if mother is Pregnant or Postnatal |
| `POST` | `/delivery/add-child/{mother_id}` | Add twin/triplet/missed child post-delivery |
| `GET` | `/delivery/children/{mother_id}` | Get all children for mother |

## Certificates (`/api/v1/certificates`)
Verification services for medical professionals.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/v1/certificates/verify` | Verify Doctor Certificate |
| `POST` | `/v1/certificates/parse` | Parse generic document |
| `POST` | `/v1/certificates/id-document/validate-asha` | Validate ASHA Identity |

## Other Modules

- **Export Routes** (`/api/export`): Data export functionalities.
- **Offline Queue** (`/api/offline-queue`): Sync support for offline-first PWA actions.
- **VAPI Routes** (`/api/vapi`): Voice AI integration endpoints.
- **Webhook Routes** (`/api/webhook`): Telegram and external webhooks.
