# Jack & Jill Conjoint Experiment System

A **conjoint-style job preference experiment** displayed in a conversational chatbot UI. This system presents randomized schematic job ads (A vs B) and records user choices for experimental analysis.

## 🎯 Purpose

This application is designed for **experimental research** - specifically conjoint analysis of job preferences. It is NOT a job matching or recommendation system.

## 🏗️ Architecture

### Design Patterns Used

1. **Factory Pattern** ([app/patterns/factory.py](app/patterns/factory.py))
   - `JobCardFactory` - Creates job card pairs for A/B comparisons
   - `JobCardBuilder` - Step-by-step construction of job cards
   - `AbstractJobCardFactory` - Allows different card configurations

2. **Strategy Pattern** ([app/patterns/strategy.py](app/patterns/strategy.py))
   - `RandomizationStrategy` - Abstract strategy for different randomization approaches
   - `SeededRandomStrategy` - Basic deterministic randomization
   - `BalancedRandomStrategy` - Ensures minimum differences between cards
   - `FullFactorialStrategy` - Complete coverage of attribute combinations
   - `DOptimalStrategy` - Maximizes statistical efficiency

3. **Adapter Pattern** ([app/patterns/adapter.py](app/patterns/adapter.py))
   - `ExportAdapter` - Abstract adapter for data export
   - `CSVExportAdapter` - Export to CSV format
   - `JSONExportAdapter` - Export to JSON format
   - `RExportAdapter` - Export to R-compatible format
   - `PythonExportAdapter` - Export to Python/Pandas format

4. **Template Method Pattern** ([app/models/base.py](app/models/base.py))
   - `BaseModel` - Common CRUD operations for all models

5. **Facade Pattern** ([app/services/](app/services/))
   - Services provide simplified interfaces to complex subsystems

## 📁 Project Structure

```
JACK_AND_JILL/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py             # Configuration classes
│   ├── models/               # MongoDB models
│   │   ├── base.py           # Base model with Template Method
│   │   ├── user.py           # User model (PII separated)
│   │   ├── chat_session.py   # Session tracking
│   │   ├── user_response.py  # Chat responses
│   │   ├── job_attribute.py  # Conjoint attributes
│   │   ├── generated_job_card.py  # Job cards
│   │   └── conjoint_choice.py     # A/B choices (immutable)
│   ├── patterns/             # Design pattern implementations
│   │   ├── factory.py        # Job card factory
│   │   ├── strategy.py       # Randomization strategies
│   │   └── adapter.py        # Export adapters
│   ├── services/             # Business logic layer
│   │   ├── session_service.py
│   │   ├── conjoint_service.py
│   │   ├── response_service.py
│   │   ├── attribute_service.py
│   │   └── export_service.py
│   └── routes/               # Flask blueprints
│       ├── api.py            # REST API endpoints
│       └── views.py          # HTML views
├── static/
│   ├── css/styles.css        # Chat UI styles
│   └── js/chat.js            # Chat application logic
├── templates/
│   ├── index.html            # Main chat interface
│   └── admin.html            # Admin dashboard
├── requirements.txt
├── run.py                    # Application entry point
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- MongoDB (running locally or remote)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /Users/enockmecheo/Desktop/JACK_AND_JILL
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB URI and secret key
   ```

5. **Start MongoDB** (if running locally):
   ```bash
   mongod --dbpath /path/to/data/db
   ```

6. **Run the application:**
   ```bash
   python run.py
   ```

7. **Access the application:**
   - Main Survey: http://localhost:5000
   - Admin Dashboard: http://localhost:5000/admin

## 📊 API Endpoints

### Session Management
- `POST /api/session/start` - Start new chat session
- `GET /api/session/<id>/state` - Get session state
- `POST /api/session/<id>/respond` - Submit response

### Conjoint Experiment
- `GET /api/conjoint/<session_id>/round/<n>` - Get job cards for round
- `POST /api/conjoint/<session_id>/choice` - Submit A/B choice
- `GET /api/conjoint/<session_id>/results` - Get session results

### Data Export
- `GET /api/export/all?format=csv` - Export all data
- `GET /api/export/session/<id>?format=json` - Export session
- `GET /api/export/statistics` - Get summary statistics

### Attributes
- `GET /api/attributes` - Get attribute definitions
- `GET /api/attributes/statistics` - Get attribute stats

## 🔬 Conjoint Attributes

Default job attributes for the experiment:

| Attribute | Levels |
|-----------|--------|
| Salary Range | $40-60k, $60-90k, $90-120k, $120k+ |
| Work Arrangement | Fully on-site, Hybrid, Fully remote |
| Company Size | Startup, Mid-size, Large |
| Commute Time | Under 15 min, 15-30 min, 30-60 min |
| Benefits | Basic, Standard, Comprehensive |
| Career Growth | Limited, Moderate, Rapid |

## 📈 Data Export for Analysis

Export data in multiple formats for statistical analysis:

```python
# Python/Pandas
import pandas as pd
df = pd.read_csv('conjoint_experiment_data.csv')

# R
source('conjoint_experiment_data.R')
```

The exported data is structured for:
- Discrete choice models
- Mixed-effects logit models
- Conjoint analysis in R/Python

## 🔒 Data Integrity

- **PII Separation**: User data stored separately from experimental choices
- **Immutable Choices**: No updates allowed on conjoint choices
- **Deterministic Randomization**: Reproducible with session seeds
- **Write-optimized**: High-volume choice recording

## 🧪 Experiment Design

This system supports:
- Full factorial designs
- D-optimal designs
- Balanced random assignment
- Custom constraint strategies

## License

MIT License
