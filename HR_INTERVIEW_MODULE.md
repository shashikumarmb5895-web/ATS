# HR Interview Scheduling Module

## Overview
The HR Interview Scheduling module is a **completely separate and independent** component of the CareerQuest AI ATS system. It provides dedicated functionality for scheduling, managing, and tracking HR interviews throughout the recruitment process.

## Architecture

### Module Structure
```
ATS/
├── hr_interviews.py          # Core HR interview scheduling logic
├── hr_api.py                 # REST API endpoints for HR interviews
├── templates/
│   └── hr_interviews.html    # Dedicated HR interview management UI
└── static/
    └── js/
        └── main.js           # Updated with HR integration functions
```

### Separation of Concerns

**Before:** HR interview scheduling was mixed with general interview scheduling in `app.py`

**After:** HR interviews are now completely separated into their own module with:
- Dedicated data storage (`hr_interviews` list separate from `interviews`)
- Independent API endpoints (`/api/hr/*`)
- Separate management interface (`/hr-interviews`)
- Specialized HR interview types and workflows

## Features

### 1. **HR Interview Scheduling**
- Schedule HR-specific interviews (HR Discussion, Cultural Fit, Behavioral Assessment, etc.)
- Set date, time, interview type, and notes
- Automatic status tracking (Scheduled, Completed, Cancelled)

### 2. **Interview Type Support**
- HR Discussion
- Cultural Fit Interview
- Behavioral Assessment
- Compensation Discussion
- Final HR Round

### 3. **Feedback Management**
- Add structured feedback after HR interviews
- Rate candidates (1-5 scale)
- Track interviewer information
- Mark interviews as completed

### 4. **Dashboard & Analytics**
- Real-time statistics (Total, Scheduled, Completed, Completion Rate)
- Upcoming interviews view
- Complete interview history
- Search and filter capabilities

### 5. **Integration with Main ATS**
- Accessible from main navigation ("HR Interviews" tab)
- Can schedule HR interviews from candidate ranking view
- Maintains compatibility with existing interview workflow

## API Endpoints

All HR interview endpoints are prefixed with `/api/hr`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/hr/schedule` | Schedule a new HR interview |
| GET | `/api/hr/interviews` | Get all HR interviews (with optional filters) |
| GET | `/api/hr/interviews/<id>` | Get specific HR interview |
| PUT | `/api/hr/interviews/<id>` | Update HR interview details |
| POST | `/api/hr/interviews/<id>/cancel` | Cancel an HR interview |
| POST | `/api/hr/interviews/<id>/feedback` | Add feedback for completed interview |
| GET | `/api/hr/upcoming` | Get all upcoming HR interviews |
| GET | `/api/hr/stats` | Get HR interview statistics |
| GET | `/api/hr/types` | Get available interview types |

### Example: Schedule HR Interview

```javascript
POST /api/hr/schedule
{
  "candidate_id": "abc-123-def",
  "job_id": 1,
  "date": "2026-05-15",
  "time": "14:00",
  "type": "HR Discussion",
  "notes": "Focus on cultural fit and salary expectations"
}
```

### Example: Add HR Feedback

```javascript
POST /api/hr/interviews/{interview_id}/feedback
{
  "interviewer_name": "Jane Smith",
  "rating": 4,
  "feedback": "Strong communication skills, good cultural alignment. Salary expectations within budget."
}
```

## Usage

### Accessing the HR Interview Module

1. **From Main Application:**
   - Click on "HR Interviews" tab in the navigation bar
   - Direct URL: `http://localhost:3000/hr-interviews`

2. **From Recruiter View:**
   - When viewing candidates, click "Schedule" button
   - This now uses the HR interview API endpoint

### Scheduling an HR Interview

1. Navigate to `/hr-interviews`
2. Click "Schedule New Interview"
3. Fill in the form:
   - Candidate ID
   - Job ID
   - Date and Time
   - Interview Type
   - Notes (optional)
4. Click "Schedule Interview"

### Adding Feedback

1. Find the interview in "Upcoming Interviews" or "All Interviews"
2. Click "Feedback" button
3. Enter:
   - Interviewer Name
   - Rating (1-5)
   - Detailed Feedback
4. Click "Submit Feedback"

### Managing Interviews

- **View Upcoming:** See all scheduled future interviews
- **Search:** Filter interviews by candidate ID, job ID, or type
- **Cancel:** Cancel scheduled interviews with confirmation
- **Track Status:** Monitor Scheduled, Completed, and Cancelled interviews

## Data Model

### HR Interview Object
```python
{
    "id": "uuid-string",
    "candidate_id": "candidate-uuid",
    "job_id": 1,
    "date": "2026-05-15",
    "time": "14:00",
    "type": "HR Discussion",
    "notes": "Additional notes",
    "status": "Scheduled",  # Scheduled, Completed, Cancelled
    "created_at": "2026-04-28T10:30:00",
    "interviewer": "Jane Smith",
    "feedback": "Feedback text",
    "rating": 4
}
```

## Key Differences from General Interviews

| Feature | General Interviews (`/api/schedule`) | HR Interviews (`/api/hr/schedule`) |
|---------|--------------------------------------|-------------------------------------|
| **Storage** | `interviews` list | `hr_interviews` list (separate) |
| **Types** | Technical, System Design, HR Discussion | HR-specific types only |
| **Feedback** | No built-in feedback | Structured feedback with ratings |
| **Management** | Basic scheduling | Full lifecycle management |
| **UI** | Modal in main app | Dedicated dashboard |
| **Analytics** | None | Statistics and completion tracking |

## Technical Implementation

### Flask Blueprint
The HR module uses Flask Blueprint for clean separation:

```python
# hr_api.py
hr_bp = Blueprint('hr_interviews', __name__, url_prefix='/api/hr')

# app.py
from hr_api import hr_bp
app.register_blueprint(hr_bp)
```

### Core Class
```python
# hr_interviews.py
class HRInterviewScheduler:
    def __init__(self):
        self.hr_interviews = []
        self.interview_types = [...]
    
    def schedule_hr_interview(self, ...):
        # Implementation
    
    def get_hr_interviews(self, ...):
        # Implementation
    
    # ... other methods
```

## Testing

### Manual Testing Steps

1. **Start the Application:**
   ```bash
   cd c:\Users\bharg\OneDrive\Desktop\ATS\ATS
   python app.py
   ```

2. **Test HR Interview Page:**
   - Navigate to `http://localhost:3000/hr-interviews`
   - Verify dashboard loads with statistics

3. **Schedule an Interview:**
   - Click "Schedule New Interview"
   - Fill in form and submit
   - Verify it appears in "Upcoming Interviews"

4. **Add Feedback:**
   - Click "Feedback" on a scheduled interview
   - Submit feedback form
   - Verify status changes to "Completed"

5. **Test Integration:**
   - Go to main app (`http://localhost:3000`)
   - Navigate to Recruiter view
   - View applicants and click "Schedule"
   - Verify it uses HR API endpoint

6. **Test API Endpoints:**
   ```bash
   # Get stats
   curl http://localhost:3000/api/hr/stats
   
   # Get all interviews
   curl http://localhost:3000/api/hr/interviews
   
   # Get interview types
   curl http://localhost:3000/api/hr/types
   ```

## Benefits of Separation

1. **Modularity:** HR interviews are completely independent
2. **Scalability:** Can be extended without affecting main ATS
3. **Maintainability:** Clear separation of concerns
4. **Specialization:** HR-specific features and workflows
5. **Analytics:** Dedicated statistics and reporting
6. **User Experience:** Purpose-built UI for HR managers

## Future Enhancements

- [ ] Email notifications for scheduled interviews
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Video interview link generation
- [ ] Automated reminder system
- [ ] HR interview templates
- [ ] Bulk scheduling capabilities
- [ ] Advanced reporting and export
- [ ] Integration with video conferencing APIs

## Troubleshooting

### Common Issues

1. **Module Not Found Error:**
   - Ensure `hr_interviews.py` and `hr_api.py` are in the ATS directory
   - Check that blueprint is registered in `app.py`

2. **API Endpoints Not Working:**
   - Verify Flask app is running
   - Check blueprint registration: `app.register_blueprint(hr_bp)`
   - Ensure URL prefix `/api/hr` is correct

3. **HR Page Not Loading:**
   - Verify route exists in `app.py`: `@app.route('/hr-interviews')`
   - Check template file exists: `templates/hr_interviews.html`

## Support

For issues or questions about the HR Interview Scheduling module:
1. Check this documentation
2. Review API endpoint responses for error messages
3. Check browser console for JavaScript errors
4. Verify Flask server logs for backend errors

---

**Module Version:** 1.0.0  
**Last Updated:** April 28, 2026  
**Compatible with:** CareerQuest AI ATS v1.0+
