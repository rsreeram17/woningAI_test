# Integrated Renovation API Testing Framework

A comprehensive testing framework for Dutch renovation permits that combines BAG (address registry) and DSO (environmental law) APIs to test the feasibility of building a renovation assistant MVP.

## 🎯 Purpose

Test the integration between Dutch government APIs to determine:
- Which renovation types have the best API support
- Data quality and completeness for different addresses
- Technical feasibility for MVP development
- Business viability scores for feature prioritization

## 🏗️ What This Framework Does

### Complete API Integration Testing
- **BAG API**: Validates addresses, extracts building details and coordinates
- **DSO APIs**: Searches regulations, checks permits, finds authorities, gets definitions
- **End-to-End Flow**: Address → Building Data → Applicable Rules → Permit Requirements → Authority Contact

### House-Specific Organization
- Each of your 10 houses gets its own folder with all test data
- Easy access to results by house address
- Detailed logging for every API interaction
- Claude-friendly reports for easy analysis

### Business Intelligence
- Viability scores (0-100) for each renovation type
- Success rate analysis across all houses
- Performance metrics and bottleneck identification
- MVP feature prioritization recommendations

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Configure Your Houses
Edit `config.yaml` and replace the sample addresses with your 10 actual houses:

```yaml
test_addresses:
  - postcode: "YOUR_POSTCODE"
    huisnummer: YOUR_NUMBER
    huisletter: "LETTER_IF_ANY"  # optional
    huisnummertoevoeging: "ADDITION_IF_ANY"  # optional, e.g., "2" for 43-2
    house_name: "Descriptive Name"
    description: "Brief description"
    priority: "high"  # high, medium, low
```

### 3. Individual API Testing (NEW!)
```bash
# Test individual APIs one by one
python tools/test_bag_api.py "1082GB 43-2"
python tools/test_dso_search.py "1082GB 43-2" "dakkapel"
python tools/test_dso_interactive.py "1082GB 43-2" "dakkapel"

# Test all APIs at once
python tools/test_all_apis.py "1082GB 43-2" "dakkapel"
```

### 4. Full Integration Testing
```bash
# Full test suite (all houses × all renovation types)
python run_tests.py

# Quick test for debugging
python tools/quick_test.py "1012JS 1" "dakkapel"

# View results for specific house
python tools/house_viewer.py "1012JS 1"
```

## 📁 What Gets Generated

### House-Specific Data (logs/by_house/house_POSTCODE_NUMBER/)
```
house_1012JS_1/
├── raw_api_calls/          # Complete API request/response logs
│   ├── bag_requests.json
│   ├── dso_search_requests.json
│   └── dso_interactive_requests.json
├── formatted_outputs/      # Human-readable test results
│   ├── dakkapel_test_results.md
│   ├── uitbouw_test_results.md
│   └── summary_all_renovations.md
└── analysis/               # Performance and business metrics
    ├── success_rates.json
    └── business_viability.json
```

### AI-Readable Reports (logs/ai_readable/)
- `session_summary_YYYYMMDD.md` - Overall test session results
- `api_interactions_YYYYMMDD.md` - Detailed API call logs
- `house_report_HOUSE_ID.md` - Individual house analysis

### Combined Analysis (outputs/combined/)
- `test_results_TIMESTAMP.json` - Complete raw results
- `test_summary_TIMESTAMP.json` - Business intelligence summary
- Cross-house comparison data

## 🛠️ Tools & Commands

### Individual API Testing (Recommended for Development)
```bash
# Test BAG API only (address lookup and building data)
python tools/test_bag_api.py "1082GB 43-2"

# Test DSO Search API only (find applicable rules)
python tools/test_dso_search.py "1082GB 43-2" "dakkapel"

# Test DSO Interactive API only (permit checks)
python tools/test_dso_interactive.py "1082GB 43-2" "dakkapel"

# Test all APIs in sequence
python tools/test_all_apis.py "1082GB 43-2" "dakkapel"
```

### Interactive House Viewer
```bash
python tools/house_viewer.py
# or
python tools/house_viewer.py "1012JS 1"
```

### Quick Testing
```bash
# Test single scenario (full integration)
python tools/quick_test.py "2631CR 15C" "uitbouw"
```

### Viewing Results
```bash
# View house summary
cat logs/by_house/house_1012JS_1/formatted_outputs/summary_all_renovations.md

# View raw API data
cat logs/by_house/house_1012JS_1/raw_api_calls/bag_requests.json

# Find all logs for a house
find logs/by_house/house_1012JS_1 -type f
```

## 🤖 Using with Claude

### Share AI-Readable Reports
The framework generates Claude-optimized reports that you can directly share:

```bash
# Generate house-specific report
python tools/house_viewer.py "1012JS 1"
# Select option 5: "Generate Claude-friendly report"
```

### Example Questions for Claude
- "Which renovation types have the best success rates?"
- "What are the main API integration issues?"
- "How should I prioritize features for my MVP based on these results?"
- "Which houses have the most complete data?"

## 📊 Understanding the Results

### Success Metrics
- **Integration Success**: Can we complete the full BAG→DSO workflow?
- **Data Completeness**: How much useful information do we get?
- **Business Viability**: 0-100 score for MVP feature prioritization

### Renovation Type Analysis
Each renovation type gets scored on:
- **API Coverage**: Do the APIs have relevant rules?
- **Permit Clarity**: Can we determine permit requirements?
- **Authority Identification**: Can we find who's responsible?
- **User Experience**: How many questions can we answer?

### House-Level Insights
For each house:
- Which renovation types work best
- Data quality and completeness
- Specific API issues or limitations
- Recommendations for MVP features

## 🔧 Configuration Options

### API Settings (config.yaml)
```yaml
apis:
  bag:
    timeout: 30
    rate_limit:
      requests_per_second: 45
  dso:
    timeout: 30
```

### Testing Settings
```yaml
testing:
  delay_between_tests: 1.0  # seconds
  retry_failed_calls: 3
```

### Logging Settings
```yaml
logging:
  house_specific:
    create_individual_folders: true
    save_raw_api_calls: true
  console:
    show_progress: true
    use_colors: true
```

## 🎯 Renovation Types Tested

1. **Dakkapel** (Dormer window) - Simple
2. **Uitbouw** (Extension) - Complex
3. **Badkamer verbouwen** (Bathroom renovation) - Medium
4. **Extra verdieping** (Additional floor) - Complex
5. **Garage bouwen** (Building garage) - Medium
6. **Keuken verbouwen** (Kitchen renovation) - Medium

## 📈 Business Intelligence Output

### Overall Recommendations
- Which renovation types to prioritize in MVP
- Which features have the best API support
- Technical challenges to expect
- Market readiness assessment

### House-Specific Insights
- Best-performing addresses for demos
- Data quality variations by location
- Regional differences in API coverage

## 🔍 Troubleshooting

### Common Issues
1. **API Key Errors**: Check your .env file has correct keys
2. **Address Not Found**: Verify Dutch postcode format (1234AB)
3. **Slow Performance**: Check internet connection and API rate limits
4. **Empty Results**: Some APIs may be temporarily unavailable

### Debug Mode
```bash
# Set debug mode in .env
DEBUG_MODE=true

# Or use quick test for single scenarios
python tools/quick_test.py "ADDRESS" "TYPE"
```

### Getting Help
- Check `logs/ai_readable/` for detailed error analysis
- Use `python tools/house_viewer.py` to explore specific issues
- Review API documentation in the context files

## 🎉 Next Steps After Testing

1. **Analyze Results**: Review the session summary and house reports
2. **Prioritize Features**: Use business viability scores to plan MVP
3. **Address Issues**: Fix any API integration problems identified
4. **Plan MVP**: Focus on high-scoring renovation types and houses
5. **Scale Up**: Expand to more addresses and renovation scenarios

---

**Ready to test your renovation MVP feasibility? Start with `python run_tests.py`**