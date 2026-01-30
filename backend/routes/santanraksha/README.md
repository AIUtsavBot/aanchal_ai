# 👶 SantanRaksha Routes

**Backend API Routes for Child Health**

## Routes in this Category

| Route | File Location | Purpose |
|-------|---------------|---------|
| **SantanRaksha** | `../santanraksha.py` | Child health APIs (42KB!) |
| **Postnatal** | `../postnatal.py` | Postnatal care APIs |
| **Postnatal Routes** | `../postnatal_routes.py` | Additional postnatal endpoints |

## Key Endpoints

- `POST /api/santanraksha/child` - Register child
- `GET /api/santanraksha/vaccines/{child_id}` - Get vaccination schedule
- `POST /api/santanraksha/growth` - Record growth measurement
- `GET /api/postnatal/assessments/{mother_id}` - Postnatal assessments
