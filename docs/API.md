# API Documentation

Base URL: `/api/v1`

## Authentication

All endpoints (except `/health`) require the `X-API-Key` header.
Example: `X-API-Key: dev-secret-key`

## Errors

All API errors return a standard JSON model:
```json
{
  "error": "ErrorType",
  "detail": "Human readable description"
}
```

## Endpoints

### POST `/surveys`
Upload a new survey (video and GPS track).

**Content-Type**: `multipart/form-data`

| Field | Type | Description |
| --- | --- | --- |
| `video` | File | The video file (`.mp4`, `.avi`, `.mkv`) |
| `gps` | File | The GPS track (`.csv`, `.gpx`) |
| `route_name` | String | Human readable route name |
| `surveyed_on` | String | Date of survey (YYYY-MM-DD) |
| `video_start_offset_s` | Float | Optional. Seconds to add to video time to match GPS time. Default 0.0 |

**Response** (200 OK):
```json
{
  "survey_id": 1,
  "status": "processing"
}
```

### GET `/surveys`
List all surveys.

### GET `/surveys/{id}`
Get survey metadata, including status and counts.

### GET `/surveys/{id}/defects`
List defects for a survey.

### GET `/surveys/{id}/segments`
List segments for a survey.

### GET `/surveys/{id}/queue?budget_inr={amount}`
Get a prioritized list of defects that fit within the given budget.

### POST `/surveys/{id}/verify?against={prev_id}`
Verify a new survey (`id`) against a previous baseline survey (`prev_id`).
Updates defect statuses (New, Open, Repaired, Failed) in the database.

### GET `/defects/{id}/crop`
Download the closest-approach crop image for a defect.
