"""Skill database. To add skills, just add names to a group (or a new group)."""
import difflib

def _g(text):
    return [s.strip() for s in text.split(",") if s.strip()]

SKILL_GROUPS = {
    "Data Science & AI": _g("Data Science, Machine Learning, Deep Learning, Artificial Intelligence, NLP, Computer Vision, Python, R, Pandas, NumPy, SciPy, Scikit-learn, TensorFlow, PyTorch, Keras, XGBoost, LightGBM, Feature Engineering, Model Deployment, MLOps, Neural Networks, Reinforcement Learning, Time Series, Generative AI, LLM, Prompt Engineering, Transformers, Hugging Face, OpenCV, Statistics, Hypothesis Testing, A/B Testing, Regression, Classification, Clustering, Jupyter, Data Mining, Predictive Modeling, Recommendation Systems"),
    "Data Analytics": _g("Data Analysis, Data Analyst, SQL, MySQL, PostgreSQL, Excel, Advanced Excel, Pivot Tables, VLOOKUP, Power BI, Tableau, Looker Studio, Google Sheets, Data Visualization, Data Cleaning, ETL, Dashboards, KPI Reporting, Matplotlib, Seaborn, Plotly, Statistical Analysis, Business Analysis, Business Intelligence, Data Modeling, DAX, Power Query, Google Analytics, Web Analytics, SAS, SPSS, Data Storytelling, Reporting, Forecasting"),
    "Data Engineering & Big Data": _g("Data Engineering, Apache Spark, PySpark, Hadoop, Kafka, Airflow, dbt, Snowflake, BigQuery, Redshift, Databricks, Data Warehouse, Data Lake, Data Pipeline, Hive, NoSQL, MongoDB, Cassandra, Redis, Elasticsearch, Oracle, SQL Server, Data Governance, Talend, Informatica"),
    "Web Development": _g("HTML, CSS, JavaScript, TypeScript, React, Angular, Vue.js, Next.js, Node.js, Express.js, Django, Flask, FastAPI, PHP, Laravel, WordPress, Bootstrap, Tailwind CSS, jQuery, REST API, GraphQL, Responsive Design, SASS, Webpack, Redux, Full Stack, Frontend Development, Backend Development, Web Development, Ruby on Rails, Spring Boot, ASP.NET, SEO Optimization, Progressive Web Apps, WebSockets, Svelte"),
    "Mobile Development": _g("Android Development, iOS Development, Flutter, React Native, Kotlin, Swift, Dart, Java, Xamarin, Firebase, SwiftUI, Jetpack Compose, Mobile App Development, App Store Deployment"),
    "Software Engineering": _g("Java, C, C++, C#, Go, Rust, Scala, Ruby, Data Structures, Algorithms, Object Oriented Programming, Design Patterns, System Design, Microservices, Unit Testing, Git, GitHub, Agile, Scrum, Code Review, Debugging, Linux, Shell Scripting, Bash, API Development, .NET, Software Architecture, Version Control, Test Driven Development, Maven, Gradle"),
    "DevOps & Cloud": _g("AWS, Azure, Google Cloud, Docker, Kubernetes, Terraform, Ansible, Jenkins, CI/CD, GitHub Actions, GitLab CI, Linux Administration, Nginx, Prometheus, Grafana, Cloud Computing, Serverless, Infrastructure as Code, Monitoring, Site Reliability, Helm, EC2, S3, Lambda, VPC, Networking"),
    "Cybersecurity": _g("Cybersecurity, Network Security, Ethical Hacking, Penetration Testing, Vulnerability Assessment, SIEM, Firewall, Cryptography, OWASP, Incident Response, Kali Linux, Wireshark, Nmap, Burp Suite, ISO 27001, SOC, Malware Analysis, Identity Access Management, Risk Assessment, Digital Forensics, Security Auditing"),
    "QA & Testing": _g("Manual Testing, Automation Testing, Selenium, Cypress, Playwright, JUnit, TestNG, Postman, JMeter, Test Cases, Bug Tracking, Jira, Regression Testing, API Testing, Performance Testing, Appium, Test Planning, Quality Assurance"),
    "UI/UX & Graphic Design": _g("Graphic Designer, Graphic Design, Adobe Photoshop, Adobe Illustrator, Adobe InDesign, CorelDRAW, Canva, Figma, Adobe XD, Sketch, UI Design, UX Design, User Research, Wireframing, Prototyping, Typography, Logo Design, Branding, Brand Identity, Color Theory, Layout Design, Print Design, Packaging Design, Poster Design, Infographics, Illustration, Digital Art, Procreate, Design Systems, Usability Testing, Visual Design, Motion Graphics, Photo Editing, Social Media Design, Banner Design"),
    "Video & Audio Production": _g("Video Editor, Video Editing, Adobe Premiere Pro, After Effects, Final Cut Pro, DaVinci Resolve, Filmora, CapCut, Color Grading, Sound Design, Audio Editing, Adobe Audition, Audacity, Cinematography, Videography, Storyboarding, Scriptwriting, Motion Design, VFX, Visual Effects, Animation, 2D Animation, 3D Animation, Blender, Maya, Cinema 4D, YouTube Editing, Podcast Production, Subtitling, Photography, Lightroom, Live Streaming, Thumbnail Design, Reels Editing"),
    "Digital Marketing": _g("Digital Marketing, SEO, SEM, Google Ads, Facebook Ads, Meta Ads, Social Media Marketing, Content Marketing, Email Marketing, Marketing Automation, Mailchimp, HubSpot, Copywriting, Content Writing, Blogging, Affiliate Marketing, Influencer Marketing, Brand Management, Market Research, Lead Generation, Conversion Optimization, Marketing Strategy, Campaign Management, Performance Marketing, LinkedIn Marketing, Instagram Marketing, YouTube Marketing, Community Management, Public Relations, Keyword Research, Link Building, E-commerce Marketing"),
    "Sales & Customer Success": _g("Sales, B2B Sales, B2C Sales, Business Development, Cold Calling, Negotiation, CRM, Salesforce, Zoho CRM, Account Management, Customer Service, Customer Support, Customer Success, Client Relationship, Pipeline Management, Sales Strategy, Retail Sales, Key Account Management, Telecalling, Upselling, Product Demo, Territory Management, Complaint Handling"),
    "Commerce & Accounting": _g("Accounting, Financial Accounting, Cost Accounting, Management Accounting, Bookkeeping, Tally, Tally Prime, QuickBooks, SAP FICO, GST, Income Tax, TDS, Taxation, Auditing, Internal Audit, Statutory Compliance, Accounts Payable, Accounts Receivable, Bank Reconciliation, Payroll Processing, Balance Sheet, Trial Balance, Journal Entries, Budgeting, MIS Reporting, Zoho Books, Busy Software, Ledger Management, Invoicing, Fixed Assets, IFRS, Cash Flow Management, Company Law"),
    "Finance & Banking": _g("Financial Analysis, Financial Modeling, Investment Banking, Equity Research, Valuation, Portfolio Management, Risk Management, Credit Analysis, Corporate Finance, Treasury, Mutual Funds, Stock Market, Derivatives, Wealth Management, Insurance, Loan Processing, KYC, Anti Money Laundering, Banking Operations, Financial Planning, Bloomberg Terminal, Capital Markets, Mergers and Acquisitions, Due Diligence, Fintech"),
    "Human Resources": _g("Human Resources, Recruitment, Talent Acquisition, Onboarding, Payroll, Employee Engagement, Performance Management, HRIS, Labour Law, Training and Development, Compensation and Benefits, Employee Relations, Campus Hiring, Headhunting, Interviewing, HR Policies, Workforce Planning, Exit Interviews, Attendance Management, Organizational Development"),
    "Management & Operations": _g("Project Management, Product Management, Program Management, Operations Management, Supply Chain Management, Logistics, Inventory Management, Procurement, Vendor Management, Process Improvement, Lean Six Sigma, Six Sigma, Kaizen, PMP, Stakeholder Management, Risk Mitigation, Strategic Planning, Team Leadership, Change Management, Time Management, Budget Management, Warehouse Management, ERP, SAP, Business Strategy, OKRs, Roadmapping, Trello, Asana, Notion"),
    "Mechanical Engineering": _g("Mechanical Engineering, AutoCAD, SolidWorks, CATIA, Creo, Ansys, NX, Fusion 360, Inventor, CAD, CAM, CNC Programming, CNC Machining, GD&T, Thermodynamics, Fluid Mechanics, Heat Transfer, Machine Design, FEA, CFD, HVAC, Welding, Manufacturing Processes, 3D Printing, Product Design, Tool Design, Quality Control, Mechanical Drawing, Hydraulics, Pneumatics, Material Science, Maintenance Engineering, Automotive Engineering, Casting, Sheet Metal Design, Lean Manufacturing, Reverse Engineering"),
    "Electrical & Electronics": _g("Electrical Engineering, Electronics Engineering, Embedded Systems, Arduino, Raspberry Pi, PLC, SCADA, Circuit Design, PCB Design, Altium, MATLAB, Simulink, VLSI, Verilog, VHDL, Microcontrollers, ARM, IoT, Power Systems, Control Systems, Signal Processing, Analog Electronics, Digital Electronics, Robotics, ROS, Electrical Wiring, Motor Control, Renewable Energy, Solar PV, Soldering, Industrial Automation, Instrumentation, Telecommunications, 5G"),
    "Civil & Architecture": _g("Civil Engineering, Structural Analysis, Revit, STAAD Pro, ETABS, SketchUp, Lumion, Primavera, MS Project, Quantity Surveying, Estimation and Costing, Site Supervision, Surveying, Total Station, Construction Management, Building Codes, Interior Design, Architectural Design, 3ds Max, BIM, Geotechnical Engineering, Highway Engineering, Water Resources, Town Planning, Concrete Design, Landscape Design"),
    "Healthcare & Life Sciences": _g("Nursing, Patient Care, Clinical Research, Pharmacy, Medical Coding, Medical Billing, Phlebotomy, Radiology, Physiotherapy, First Aid, CPR, Electronic Health Records, Pharmacovigilance, Clinical Trials, GCP, Biotechnology, Microbiology, Laboratory Techniques, PCR, Bioinformatics, Public Health, Epidemiology, Healthcare Administration, Medical Terminology, Diagnostics, Dental Care, Nutrition, Mental Health Counseling"),
    "Education & Content": _g("Teaching, Curriculum Development, Lesson Planning, Classroom Management, Tutoring, E-learning, Instructional Design, Academic Writing, Research, Technical Writing, Editing, Proofreading, Translation, Public Speaking, Content Creation, Storytelling, Journalism, Creative Writing, Ghostwriting, Moodle, Mentoring, Student Counseling, Assessment Design"),
    "Legal & Compliance": _g("Legal Research, Contract Drafting, Contract Management, Corporate Law, Intellectual Property, Litigation, Legal Compliance, Regulatory Compliance, GDPR, Legal Writing, Arbitration, Paralegal, Data Privacy, Company Secretary, Policy Drafting"),
    "Hospitality & Travel": _g("Hotel Management, Front Office, Housekeeping, Food and Beverage, Event Management, Travel Planning, Ticketing, Guest Relations, Restaurant Management, Culinary Arts, Bartending, Tour Guiding, Catering, Reservation Systems, Menu Planning, Food Safety"),
    "Soft Skills": _g("Communication, Teamwork, Leadership, Problem Solving, Critical Thinking, Adaptability, Creativity, Presentation Skills, Decision Making, Conflict Resolution, Emotional Intelligence, Analytical Thinking, Collaboration, Attention to Detail, Multitasking, Self Motivation, Interpersonal Skills, Active Listening, Work Ethic, English Proficiency, Customer Focus"),
    "Office & Productivity Tools": _g("Microsoft Office, MS Word, MS PowerPoint, MS Excel, MS Outlook, Google Workspace, Google Docs, Typing, Data Entry, Email Management, Slack, Zoom, Microsoft Teams, Documentation, Scheduling, Office Administration, Report Writing, Minutes of Meeting"),
}

ALIASES = {
    "javascript": ["js"], "typescript": ["ts"], "machine learning": ["ml"],
    "artificial intelligence": ["ai"], "nlp": ["natural language processing"],
    "power bi": ["powerbi"], "node.js": ["nodejs", "node js"], "vue.js": ["vuejs", "vue"],
    "react": ["reactjs", "react.js"], "express.js": ["expressjs", "express"],
    "next.js": ["nextjs"], "postgresql": ["postgres"], "mongodb": ["mongo"],
    "google cloud": ["gcp"], "aws": ["amazon web services"], "ms excel": ["excel"],
    "adobe photoshop": ["photoshop"], "adobe illustrator": ["illustrator"],
    "adobe premiere pro": ["premiere pro", "premiere"], "after effects": ["adobe after effects"],
    "ci/cd": ["cicd", "ci cd"], "seo": ["search engine optimization"],
    "data analyst": ["data analytics"], "data science": ["data scientist"],
    "graphic designer": ["graphic design"], "video editor": ["video editing"],
    "microsoft office": ["ms office"], "object oriented programming": ["oop", "oops"],
}

ALL_SKILLS = []          # [(skill, group)]
_seen = set()
for _grp, _items in SKILL_GROUPS.items():
    for _s in _items:
        if _s.lower() not in _seen:
            _seen.add(_s.lower())
            ALL_SKILLS.append((_s, _grp))


def suggest(query, limit=12):
    """Return (skills, groups) matching the query. Typos are tolerated."""
    q = query.strip().lower()
    if not q:
        return [], []
    ranked = []
    for skill, grp in ALL_SKILLS:
        s = skill.lower()
        if s == q: r = 0
        elif s.startswith(q): r = 1
        elif any(w.startswith(q) for w in s.split()): r = 2
        elif q in s: r = 3
        elif len(q) >= 4 and difflib.SequenceMatcher(None, q, s).ratio() >= 0.75: r = 5
        else: continue
        ranked.append((r, len(s), skill, grp))
    ranked.sort()
    groups = [{"name": g, "count": len(v)} for g, v in SKILL_GROUPS.items()
              if q in g.lower() or any(w.startswith(q) for w in g.lower().replace("&", " ").split())]
    return [{"skill": s, "group": g} for _, _, s, g in ranked[:limit]], groups
