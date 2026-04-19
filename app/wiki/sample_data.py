"""
Enhanced sample wiki articles demonstrating advanced knowledge graph features
Shows versioning, relationships, feedback loop, and source traceability
"""
from typing import List, Dict, Any


def get_sample_articles() -> List[Dict[str, Any]]:
    """
    Get enhanced sample wiki articles with knowledge graph capabilities
    
    Returns:
        List of sample article dictionaries following the enhanced schema
    """
    return [
        {
            "entry_id": "policy_annual_leave",
            "title": "Annual Leave Policy",
            "aliases": ["vacation policy", "time off policy", "leave entitlement"],
            "type": "rule",
            "content": """# Annual Leave Policy

## Overview
All full-time employees are entitled to annual leave based on their length of service.

## Leave Entitlement (2024)
- **Tier 1 (0-2 years)**: 10 days per year
- **Tier 2 (>2-5 years)**: 15 days per year  
- **Tier 3 (>5 years)**: 20 days per year

## Application Process
1. Submit leave request through HR portal at least **2 weeks (10 business days)** in advance
2. Obtain manager approval via workflow system
3. HR will confirm and update records within 3 business days

## Carry-over Policy
- Maximum **5 days** can be carried over to next year
- Must be used within **first quarter (Q1)** of following year
- Excess days will be **forfeited** without compensation

## Public Holidays
Public holidays do not count against annual leave entitlement.

## Emergency Leave
For emergency situations, contact HR directly with manager notification.

## Related Policies
- See also: [Sick Leave Policy](policy_sick_leave)
- See also: [Remote Work Policy](policy_remote_work)

## Contact
For questions about leave policy:
- Email: hr@company.com
- Portal: https://hr.company.com/leave
- Phone: ext. 5678""",
            "summary": "Company annual leave policy detailing entitlements based on tenure, application process, and carry-over rules.",
            "parent_ids": [],
            "related_ids": [
                {"entry_id": "policy_sick_leave", "relation": "related_to"},
                {"entry_id": "policy_remote_work", "relation": "related_to"},
                {"entry_id": "process_leave_request", "relation": "depends_on"}
            ],
            "tags": ["hr", "leave", "vacation", "policy", "benefits"],
            "sources": [
                {
                    "source_id": "doc_hr_2024_001",
                    "file_name": "Employee_Handbook_2024.pdf",
                    "page": 15,
                    "content_snippet": "Section 3.2: Annual Leave - Employees are entitled to...",
                    "url": "https://intranet.company.com/docs/handbook2024.pdf"
                }
            ],
            "confidence": 0.98,
            "status": "active",
            "version": 2,
            "create_time": "2024-01-01T00:00:00",
            "update_time": "2024-12-15T10:30:00",
            "feedback": {
                "positive": 45,
                "negative": 2,
                "comments": [
                    "Very clear and helpful!",
                    "Would be good to add examples for part-time employees"
                ]
            },
            "metadata": {
                "department": "Human Resources",
                "effective_date": "2024-01-01",
                "review_date": "2025-01-01",
                "owner": "HR Policy Team"
            }
        },
        {
            "entry_id": "process_it_equipment_request",
            "title": "IT Equipment Request Process",
            "aliases": ["hardware request", "laptop request", "equipment procurement"],
            "type": "process",
            "content": """# IT Equipment Request Process

## Overview
Standardized procedure for requesting IT equipment including laptops, monitors, peripherals, and software licenses.

## Standard Equipment Allocation
All full-time employees receive:
- Laptop (standard business configuration)
- Monitor (24" or 27" upon request)
- Keyboard and mouse (ergonomic options available)
- Headset (for remote/hybrid workers)
- Laptop bag/case

## Request Procedure

### Step 1: Submit Request
Complete the **IT Equipment Request Form** on the intranet portal.
- URL: https://intranet.company.com/it/equipment-request
- Required fields: Employee ID, justification, equipment type

### Step 2: Manager Approval
Your direct manager must approve the request within **2 business days**.
- Approval via email or workflow system
- Budget code verification required

### Step 3: IT Processing
IT department processes approved requests within **5 business days**.
- Inventory check
- Configuration and setup
- Asset tagging

### Step 4: Delivery/Collection
**Office-based employees:**
- Collect from IT Service Desk (Building A, Floor 2)
- Bring employee ID for verification

**Remote employees:**
- Equipment shipped via courier (2-3 business days)
- Signature required upon delivery
- Return shipping label included for future returns

## Special/Non-Standard Requests
For equipment beyond standard allocation:
1. Provide detailed **business justification**
2. Include **cost estimate** from vendor
3. Obtain **department head approval** (not just direct manager)
4. IT will evaluate technical feasibility

Examples: High-performance workstation, specialized software, multiple monitors

## Software Licenses
Software requests follow separate process:
- Standard software: Auto-approved (Office 365, Adobe Reader, etc.)
- Specialized software: Requires IT security review
- Development tools: Requires CTO approval

## Equipment Return
When leaving company or upgrading:
1. **Back up all data** to company cloud storage
2. Sign out of all accounts and services
3. Return equipment to IT Service Desk
4. Complete **Equipment Return Form**
5. Receive confirmation email

## Warranty and Support
- Standard warranty: 3 years manufacturer warranty
- Extended warranty: Available for critical roles
- Support: IT Helpdesk (ext. 1234, ithelp@company.com)

## Related Resources
- [IT Security Policy](policy_it_security)
- [Remote Work Setup Guide](guide_remote_work_setup)
- [Software License Management](process_software_license)

## Contact
**IT Service Desk:**
- Email: ithelp@company.com
- Phone: ext. 1234
- Portal: https://support.company.com
- Hours: Mon-Fri 8:00 AM - 6:00 PM""",
            "summary": "Complete process for requesting IT equipment including standard allocation, approval workflow, and delivery procedures.",
            "parent_ids": [],
            "related_ids": [
                {"entry_id": "policy_it_security", "relation": "related_to"},
                {"entry_id": "guide_remote_work_setup", "relation": "example_of"},
                {"entry_id": "process_software_license", "relation": "related_to"}
            ],
            "tags": ["it", "equipment", "hardware", "procurement", "process"],
            "sources": [
                {
                    "source_id": "doc_it_2024_005",
                    "file_name": "IT_Procedures_Manual_v3.2.docx",
                    "page": 8,
                    "content_snippet": "Section 2.1: Equipment Procurement - All hardware requests must...",
                    "url": "https://intranet.company.com/it/procedures"
                }
            ],
            "confidence": 0.95,
            "status": "active",
            "version": 3,
            "create_time": "2023-06-15T09:00:00",
            "update_time": "2024-11-20T14:15:00",
            "feedback": {
                "positive": 38,
                "negative": 5,
                "comments": [
                    "Process is clear but could be faster",
                    "Would like self-service option for standard items"
                ]
            },
            "metadata": {
                "department": "Information Technology",
                "process_owner": "IT Operations",
                "sla_days": 5,
                "automation_level": "semi-automated"
            }
        },
        {
            "entry_id": "concept_expense_reimbursement",
            "title": "Expense Reimbursement Concept",
            "aliases": ["expense claim", "reimbursement policy", "business expenses"],
            "type": "concept",
            "content": """# Expense Reimbursement Concept

## Definition
Expense reimbursement is the process by which employees are repaid for legitimate business-related expenses incurred on behalf of the company.

## Key Principles
1. **Business Purpose**: Expenses must have clear business justification
2. **Reasonable Cost**: Expenses should be reasonable and necessary
3. **Documentation**: Receipts and supporting documents required
4. **Timeliness**: Submit within 30 days of expense occurrence
5. **Compliance**: Must adhere to company policy and local regulations

## Eligible Expenses
- Business travel (flights, hotels, ground transportation)
- Client meals and entertainment (with prior approval)
- Conference registration fees
- Professional development courses
- Office supplies (when working remotely)

## Non-Eligible Expenses
- Personal expenses
- Alcohol (unless pre-approved for client entertainment)
- Upgrades beyond standard (e.g., first-class flights)
- Family member expenses
- Fines or penalties

## Reimbursement Limits
- Daily meal allowance: $75 (domestic), $100 (international)
- Hotel maximum: $200/night (tier 1 cities), $150/night (other locations)
- Ground transportation: Actual cost with receipts

## Approval Workflow
1. Employee submits expense report with receipts
2. Direct manager reviews and approves
3. Finance department verifies compliance
4. Payment processed within 10 business days

## Documentation Requirements
- Original receipts (digital copies acceptable)
- Business purpose description
- Attendee list (for meals/entertainment)
- Pre-approval documentation (if required)

## Related Concepts
- [Travel Policy](policy_travel)
- [Corporate Credit Card Usage](policy_corporate_card)
- [Per Diem Rates](reference_per_diem)

## Tax Implications
Reimbursed business expenses are generally non-taxable. Consult tax advisor for specific situations.""",
            "summary": "Core concept of expense reimbursement including principles, eligible expenses, limits, and approval workflow.",
            "parent_ids": [],
            "related_ids": [
                {"entry_id": "policy_travel", "relation": "related_to"},
                {"entry_id": "policy_corporate_card", "relation": "related_to"},
                {"entry_id": "process_submit_expense", "relation": "depends_on"}
            ],
            "tags": ["finance", "expenses", "reimbursement", "policy", "concept"],
            "sources": [
                {
                    "source_id": "doc_finance_2024_003",
                    "file_name": "Finance_Policy_Manual_2024.pdf",
                    "page": 22,
                    "content_snippet": "Chapter 4: Expense Management - The company reimburses...",
                    "url": "https://intranet.company.com/finance/policies"
                }
            ],
            "confidence": 0.97,
            "status": "active",
            "version": 1,
            "create_time": "2024-03-10T11:00:00",
            "update_time": "2024-03-10T11:00:00",
            "feedback": {
                "positive": 12,
                "negative": 0,
                "comments": []
            },
            "metadata": {
                "department": "Finance",
                "category": "Financial Policies",
                "regulatory_compliance": True
            }
        },
        {
            "entry_id": "qa_vpn_setup",
            "title": "How to Set Up VPN for Remote Access?",
            "aliases": ["vpn configuration", "remote access setup", "connect to company network"],
            "type": "qa",
            "content": """# How to Set Up VPN for Remote Access?

## Question
How do I configure VPN to securely access company resources when working remotely?

## Answer

### Prerequisites
- Company-issued laptop or approved personal device
- VPN client software (provided by IT)
- Multi-factor authentication (MFA) enabled
- Stable internet connection

### Step-by-Step Setup

#### Windows
1. Download VPN client from IT portal: https://intranet.company.com/vpn/download
2. Run installer and follow prompts
3. Launch VPN client
4. Enter company credentials (username@company.com)
5. Complete MFA verification (push notification to authenticator app)
6. Click "Connect"
7. Verify connection status shows "Connected"

#### macOS
1. Open System Preferences > Network
2. Click "+" to add new interface
3. Select "VPN" as interface type
4. Choose "IKEv2" as VPN type
5. Enter server address: vpn.company.com
6. Enter account credentials
7. Enable "Send all traffic over VPN connection"
8. Click "Apply" and "Connect"

#### Mobile (iOS/Android)
1. Install "Company VPN" app from App Store/Play Store
2. Open app and enter company email
3. Follow MFA verification steps
4. Toggle VPN connection ON
5. Verify lock icon appears in status bar

### Troubleshooting

**Issue: Cannot connect**
- Check internet connection
- Verify credentials are correct
- Ensure MFA device is accessible
- Try restarting VPN client

**Issue: Slow connection**
- Switch to wired connection if possible
- Close bandwidth-intensive applications
- Try different VPN server location

**Issue: Connection drops frequently**
- Update VPN client to latest version
- Check firewall settings
- Contact IT if problem persists

### Security Best Practices
- Always use VPN on public Wi-Fi
- Never share VPN credentials
- Log out when not in use
- Keep VPN client updated
- Report suspicious activity to IT Security

### Related Resources
- [VPN Security Policy](policy_vpn_security)
- [Remote Work Best Practices](guide_remote_work)
- [IT Security Guidelines](policy_it_security)

### Support
For VPN issues:
- IT Helpdesk: ext. 1234
- Email: ithelp@company.com
- Emergency: IT Security Hotline ext. 9999""",
            "summary": "Complete guide for setting up VPN on Windows, macOS, and mobile devices with troubleshooting tips.",
            "parent_ids": [],
            "related_ids": [
                {"entry_id": "policy_vpn_security", "relation": "depends_on"},
                {"entry_id": "guide_remote_work", "relation": "related_to"},
                {"entry_id": "policy_it_security", "relation": "related_to"}
            ],
            "tags": ["it", "vpn", "remote-access", "security", "troubleshooting", "faq"],
            "sources": [
                {
                    "source_id": "doc_it_2024_012",
                    "file_name": "VPN_User_Guide_v2.1.pdf",
                    "page": 3,
                    "content_snippet": "Section 1: Getting Started - To establish a secure connection...",
                    "url": "https://intranet.company.com/it/vpn-guide"
                }
            ],
            "confidence": 0.93,
            "status": "active",
            "version": 2,
            "create_time": "2024-02-20T13:30:00",
            "update_time": "2024-10-05T09:45:00",
            "feedback": {
                "positive": 67,
                "negative": 3,
                "comments": [
                    "Very helpful! Saved me hours of troubleshooting",
                    "Screenshots would make it even better"
                ]
            },
            "metadata": {
                "department": "IT",
                "difficulty_level": "beginner",
                "estimated_time_minutes": 10,
                "last_tested": "2024-10-01"
            }
        },
        {
            "entry_id": "formula_roi_calculation",
            "title": "ROI Calculation Formula",
            "aliases": ["return on investment", "investment analysis", "profit calculation"],
            "type": "formula",
            "content": """# ROI Calculation Formula

## Definition
Return on Investment (ROI) measures the profitability of an investment relative to its cost.

## Basic Formula

```
ROI = [(Net Profit / Cost of Investment) × 100]%

Where:
- Net Profit = Total Revenue - Total Cost
- Cost of Investment = Initial investment + Ongoing costs
```

## Example Calculation

**Scenario:** Marketing campaign investment

- Initial investment: $10,000
- Additional costs: $2,000
- Total revenue generated: $25,000

**Calculation:**
```
Net Profit = $25,000 - ($10,000 + $2,000) = $13,000
Total Cost = $12,000

ROI = ($13,000 / $12,000) × 100 = 108.33%
```

**Interpretation:** For every dollar invested, you gained $1.08 in profit.

## Advanced Considerations

### Time-Adjusted ROI
For investments over multiple periods:

```
Annualized ROI = [(1 + ROI)^(1/n) - 1] × 100

Where n = number of years
```

### Risk-Adjusted ROI
Consider risk factors:
- Market volatility
- Opportunity cost
- Inflation impact

## Industry Benchmarks

| Industry | Average ROI | Good ROI | Excellent ROI |
|----------|-------------|----------|---------------|
| Technology | 15-25% | 25-40% | >40% |
| Manufacturing | 10-20% | 20-30% | >30% |
| Retail | 8-15% | 15-25% | >25% |
| Services | 12-22% | 22-35% | >35% |

## Common Mistakes
1. Ignoring hidden costs (maintenance, training, downtime)
2. Not accounting for time value of money
3. Comparing incomparable investments
4. Using unrealistic revenue projections

## Tools and Templates
- Excel ROI Calculator: [Download Template](https://intranet.company.com/templates/roi-calculator.xlsx)
- Online ROI Calculator: https://tools.company.com/roi
- Financial Analysis Software: SAP, Oracle Financials

## Related Concepts
- [Net Present Value (NPV)](concept_npv)
- [Internal Rate of Return (IRR)](concept_irr)
- [Payback Period](concept_payback_period)
- [Cost-Benefit Analysis](process_cost_benefit)

## References
- Corporate Finance Institute. "Return on Investment (ROI)."
- Investopedia. "Understanding ROI."
- Company Financial Planning Guidelines v3.0""",
            "summary": "Comprehensive guide to ROI calculation including basic formula, examples, industry benchmarks, and common pitfalls.",
            "parent_ids": [],
            "related_ids": [
                {"entry_id": "concept_npv", "relation": "related_to"},
                {"entry_id": "concept_irr", "relation": "related_to"},
                {"entry_id": "process_cost_benefit", "relation": "example_of"}
            ],
            "tags": ["finance", "formula", "roi", "investment", "analysis", "calculation"],
            "sources": [
                {
                    "source_id": "doc_finance_2024_008",
                    "file_name": "Financial_Analysis_Methods.pdf",
                    "page": 45,
                    "content_snippet": "Chapter 7: Investment Metrics - ROI is calculated as...",
                    "url": "https://intranet.company.com/finance/methods"
                }
            ],
            "confidence": 0.99,
            "status": "active",
            "version": 1,
            "create_time": "2024-05-12T10:00:00",
            "update_time": "2024-05-12T10:00:00",
            "feedback": {
                "positive": 28,
                "negative": 1,
                "comments": [
                    "Excellent breakdown with practical examples!"
                ]
            },
            "metadata": {
                "department": "Finance",
                "complexity": "intermediate",
                "use_cases": ["project evaluation", "budget planning", "investment decisions"]
            }
        }
    ]
