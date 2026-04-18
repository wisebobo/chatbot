"""
Sample wiki articles for demonstration and testing
"""
from typing import List, Dict, Any


def get_sample_articles() -> List[Dict[str, Any]]:
    """
    Get sample wiki articles for initial setup
    
    Returns:
        List of sample article dictionaries
    """
    return [
        {
            "id": "wiki_0001",
            "title": "Annual Leave Policy",
            "content": """# Annual Leave Policy

## Overview
All full-time employees are entitled to annual leave based on their length of service.

## Leave Entitlement
- **0-2 years**: 15 days per year
- **2-5 years**: 18 days per year
- **5+ years**: 22 days per year

## Application Process
1. Submit leave request through HR portal at least 2 weeks in advance
2. Obtain manager approval
3. HR will confirm and update records

## Carry-over Policy
- Maximum 5 days can be carried over to next year
- Must be used within first quarter of following year
- Excess days will be forfeited

## Public Holidays
Public holidays do not count against annual leave entitlement.

## Contact
For questions about leave policy, contact HR department at hr@company.com""",
            "category": "HR",
            "tags": ["leave", "vacation", "holiday", "time-off"],
            "url": "/wiki/hr/annual-leave-policy",
            "author": "HR Department",
            "version": "2.1",
            "metadata": {
                "department": "Human Resources",
                "effective_date": "2024-01-01",
                "review_date": "2025-01-01"
            }
        },
        {
            "id": "wiki_0002",
            "title": "IT Equipment Request Process",
            "content": """# IT Equipment Request Process

## Overview
This document outlines the process for requesting IT equipment including laptops, monitors, peripherals, and software.

## Standard Equipment
All employees receive:
- Laptop (standard configuration)
- Monitor (upon request)
- Keyboard and mouse
- Headset (for remote workers)

## Request Procedure

### Step 1: Submit Request
Complete the IT Equipment Request Form available on the intranet.

### Step 2: Manager Approval
Your manager must approve the request within 2 business days.

### Step 3: IT Processing
IT department will process approved requests within 5 business days.

### Step 4: Delivery/Collection
- Office employees: Collect from IT desk
- Remote employees: Equipment shipped to home address

## Special Requests
For non-standard equipment or software:
1. Provide business justification
2. Include cost estimate
3. Obtain department head approval

## Equipment Return
When leaving the company or upgrading equipment:
1. Back up all data
2. Return equipment to IT department
3. Complete equipment return form

## Support
For IT equipment issues, contact IT Helpdesk:
- Email: ithelp@company.com
- Phone: ext. 1234
- Portal: https://support.company.com""",
            "category": "IT",
            "tags": ["equipment", "hardware", "request", "it-support"],
            "url": "/wiki/it/equipment-request",
            "author": "IT Department",
            "version": "1.5",
            "metadata": {
                "department": "Information Technology",
                "last_review": "2024-06-15"
            }
        },
        {
            "id": "wiki_0003",
            "title": "Expense Reimbursement Guidelines",
            "content": """# Expense Reimbursement Guidelines

## Overview
This policy covers reimbursement procedures for business-related expenses.

## Eligible Expenses
- Business travel (flights, hotels, ground transportation)
- Client meals and entertainment
- Conference and training fees
- Office supplies (with prior approval)
- Mobile phone bills (partial reimbursement)

## Non-Eligible Expenses
- Personal expenses
- Alcoholic beverages (unless client meeting)
- Traffic fines or parking violations
- Gym memberships
- Commuting costs

## Submission Process

### 1. Collect Receipts
Keep original receipts for all expenses over $25.

### 2. Complete Expense Report
- Use the online expense system
- Categorize each expense
- Attach digital copies of receipts
- Add business purpose for each item

### 3. Manager Approval
Submit to your manager for approval within 30 days of expense.

### 4. Finance Review
Finance team reviews approved reports within 5 business days.

### 5. Payment
Reimbursement processed via direct deposit within 10 business days.

## Spending Limits
- Meals: $50 per person per day
- Hotels: Company negotiated rates preferred
- Flights: Economy class for domestic, premium economy for international

## Receipt Requirements
- Digital photos acceptable
- Must show date, amount, vendor, and items purchased
- Credit card statements alone are not sufficient

## Questions?
Contact Finance team: finance@company.com""",
            "category": "Finance",
            "tags": ["expense", "reimbursement", "receipts", "finance"],
            "url": "/wiki/finance/expense-reimbursement",
            "author": "Finance Department",
            "version": "3.0",
            "metadata": {
                "department": "Finance",
                "policy_number": "FIN-2024-001"
            }
        },
        {
            "id": "wiki_0004",
            "title": "Remote Work Policy",
            "content": """# Remote Work Policy

## Overview
This policy establishes guidelines for employees working remotely.

## Eligibility
- Full-time employees after probation period (3 months)
- Role must be suitable for remote work
- Manager approval required

## Work Arrangements

### Fully Remote
- Work from home 5 days per week
- Monthly office visits for team meetings

### Hybrid
- 2-3 days in office
- 2-3 days remote
- Schedule coordinated with team

## Equipment and Setup
- Company provides laptop and necessary peripherals
- Employee responsible for internet connection
- Ergonomic workspace recommended

## Working Hours
- Core hours: 10 AM - 3 PM (must be available)
- Flexible outside core hours
- Total 8 hours per day expected

## Communication
- Respond to messages within 2 hours during work hours
- Attend all scheduled video meetings
- Keep calendar up to date

## Security Requirements
- Use VPN for all company systems
- Secure home network (WPA2/WPA3)
- Lock computer when away
- No public WiFi for work

## Performance Expectations
- Same performance standards as office work
- Regular check-ins with manager
- Deliverables tracked through project management tools

## Support
- IT support available remotely
- HR available for policy questions
- Manager for work-related concerns""",
            "category": "HR",
            "tags": ["remote-work", "work-from-home", "flexible", "policy"],
            "url": "/wiki/hr/remote-work-policy",
            "author": "HR Department",
            "version": "2.0",
            "metadata": {
                "department": "Human Resources",
                "effective_date": "2024-03-01"
            }
        },
        {
            "id": "wiki_0005",
            "title": "Code Review Best Practices",
            "content": """# Code Review Best Practices

## Overview
Guidelines for conducting effective code reviews in our engineering teams.

## Before Submitting for Review

### Author Responsibilities
- Ensure code compiles and passes all tests
- Write clear commit messages
- Add comments for complex logic
- Update documentation if needed
- Keep pull requests small (< 400 lines ideal)

## Review Process

### Timeline
- Reviews should be completed within 24 hours
- Mark as urgent if blocking deployment
- Use @mentions for specific reviewers

### What to Check

#### Functionality
- Does the code solve the intended problem?
- Are edge cases handled?
- Is error handling appropriate?

#### Code Quality
- Follows coding standards
- No code duplication
- Proper naming conventions
- Appropriate abstraction level

#### Performance
- No obvious performance issues
- Database queries optimized
- Memory usage reasonable

#### Security
- No hardcoded secrets
- Input validation present
- SQL injection prevention
- Authentication/authorization checks

#### Testing
- Unit tests included
- Test coverage adequate
- Integration tests if needed

## Giving Feedback

### Do's
✓ Be constructive and specific
✓ Explain why something should change
✓ Suggest alternatives
✓ Acknowledge good practices

### Don'ts
✗ Don't be critical without explanation
✗ Don't nitpick trivial issues
✗ Don't use harsh language
✗ Don't delay reviews unnecessarily

## Common Issues to Flag

### Critical (Must Fix)
- Security vulnerabilities
- Breaking changes without migration
- Missing error handling
- Performance bottlenecks

### Important (Should Fix)
- Code style violations
- Missing tests
- Poor naming
- Duplicated logic

### Suggestions (Nice to Have)
- Refactoring opportunities
- Documentation improvements
- Minor optimizations

## Approval Process
- Minimum 1 approval required
- Senior dev approval for major changes
- All comments must be resolved
- CI/CD pipeline must pass

## Tools
- GitHub/GitLab for code review
- SonarQube for static analysis
- CodeClimate for quality metrics

## Learning Resources
- Internal coding standards doc
- Language-specific style guides
- Security best practices guide""",
            "category": "Engineering",
            "tags": ["code-review", "best-practices", "development", "quality"],
            "url": "/wiki/engineering/code-review",
            "author": "Engineering Team",
            "version": "1.8",
            "metadata": {
                "department": "Engineering",
                "applicable_languages": ["Python", "Java", "JavaScript", "Go"]
            }
        },
        {
            "id": "wiki_0006",
            "title": "Meeting Room Booking System",
            "content": """# Meeting Room Booking System

## Overview
Guide to booking conference rooms and meeting spaces.

## Available Rooms

### Small Rooms (2-4 people)
- Room A101, A102, A103
- Equipped with whiteboard
- TV screen for presentations

### Medium Rooms (5-10 people)
- Room B201, B202
- Video conferencing capability
- Whiteboard and flipchart

### Large Rooms (10-20 people)
- Room C301 (Board Room)
- Full AV setup
- Catering available

### Training Room (20-30 people)
- Room D401
- Projector and sound system
- Movable furniture

## Booking Process

### Method 1: Online Portal
1. Visit: https://rooms.company.com
2. Select date and time
3. Choose room based on capacity
4. Add meeting details
5. Submit booking

### Method 2: Outlook Calendar
1. Open Outlook calendar
2. Create new meeting
3. Add room as resource
4. Send invitation

### Method 3: Reception
- Call reception: ext. 1000
- Provide meeting details
- Receptionist will book for you

## Booking Rules
- Maximum 4 hours per booking
- Book no more than 2 weeks in advance
- Cancel if not needed (free up for others)
- No-show after 15 minutes = automatic cancellation

## Equipment Requests
Request additional equipment when booking:
- Video conferencing setup
- Additional monitors
- Microphones/speakers
- Catering services

## During Meeting
- Start on time
- Keep noise levels reasonable
- Clean up after use
- Report any issues to facilities

## Recurring Meetings
- Can book recurring slots (weekly/monthly)
- Review quarterly to release unused slots
- Priority given to client-facing meetings

## Support
Facilities team: facilities@company.com""",
            "category": "Operations",
            "tags": ["meeting", "booking", "rooms", "facilities"],
            "url": "/wiki/operations/meeting-rooms",
            "author": "Facilities Team",
            "version": "1.2",
            "metadata": {
                "department": "Facilities & Operations"
            }
        }
    ]
