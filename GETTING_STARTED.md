# Getting Started with API Testing

This is your step-by-step guide to test the Dutch renovation APIs for your MVP.

## 📋 What You Need Before Starting

### 1. API Keys
You need API keys for:
- **BAG API**: Dutch address/building registry
- **DSO API**: Dutch Environmental Act (Omgevingswet)

### 2. Your 10 House Addresses
Prepare your 10 house addresses in Dutch format:
- Postcode: `1234AB` format
- House number: `123`
- Optional house letter: `A`, `B`, etc.

## 🚀 Step-by-Step Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure API Keys
```bash
# Copy the template
cp .env.example .env

# Edit with your API keys
nano .env
```

Add your keys:
```env
BAG_API_KEY=your_bag_api_key_here
DSO_API_KEY=your_dso_api_key_here
```

### Step 3: Configure Your Houses
Edit `config.yaml` and replace the sample addresses:

```yaml
test_addresses:
  - postcode: "1012JS"      # Replace with your address
    huisnummer: 1           # Replace with your house number
    house_name: "My House 1" # Give it a descriptive name
    description: "Description of this property"
    priority: "high"        # high, medium, or low
  # Add your other 9 houses...
```

## 🧪 Testing Options

### Option 1: Quick Test (Recommended First)
Test a single house and renovation type to make sure everything works:

```bash
python tools/quick_test.py "1012JS 1" "dakkapel"
```

This will:
- ✅ Test your API keys
- ✅ Validate address format
- ✅ Check API connectivity
- ✅ Show basic results

### Option 2: Full Test Suite
Once quick test works, run the complete test:

```bash
python run_tests.py
```

This will test all your houses with all renovation types (60 tests total if you have 10 houses).

**Estimated time**: 15-30 minutes depending on API response times.

## 📊 What Happens During Testing

### Real-time Progress
You'll see live progress like this:
```
🚀 Starting: Amsterdam Canal House → dakkapel
📊 Progress: [==========----------] 2/7 steps

🔄 BAG API: GET /adressen (ID: abc123ef)
  ✅ Response: 200 (0.23s)

🔄 DSO_Search API: POST /activiteiten/_zoek (ID: def456gh)
  ✅ Response: 200 (0.45s)
```

### Files Created
For each house, you get:
- **Raw API logs**: Complete request/response data
- **Formatted results**: Human-readable test summaries
- **House summary**: Complete analysis for that address

## 🔍 Viewing Your Results

### Quick House Check
```bash
python tools/house_viewer.py "1012JS 1"
```

### View All Results
```bash
# See what files were created
ls logs/by_house/

# Read a house summary
cat logs/by_house/house_1012JS_1/formatted_outputs/summary_all_renovations.md
```

### AI-Friendly Analysis
Share this file with Claude Desktop for detailed analysis:
```bash
cat logs/ai_readable/session_summary_YYYYMMDD.md
```

## 💡 Understanding Your Results

### Success Indicators
- ✅ **Green checkmarks**: API calls succeeded
- ❌ **Red X marks**: API calls failed
- ⚠️ **Yellow warnings**: Partial success

### Key Metrics
- **Integration Success Rate**: Can we complete the full workflow?
- **Business Viability Score**: 0-100 score for MVP features
- **Data Completeness**: How much useful info do we get?

### What to Look For
1. **Which renovation types work best**: High success rates
2. **Which houses have good data**: Complete building information
3. **API performance issues**: Slow responses or failures
4. **Business opportunities**: High viability scores

## 🎯 Next Steps Based on Results

### If Results Look Good (70%+ success rate)
- ✅ APIs are ready for MVP development
- 🎯 Prioritize high-scoring renovation types
- 🏗️ Focus on houses with complete data for demos

### If Results Are Mixed (40-70% success rate)
- ⚠️ MVP possible but with limitations
- 🔧 Focus on renovation types that work well
- 🛠️ Plan for error handling and fallbacks

### If Results Are Poor (<40% success rate)
- ❌ Current API approach may not work
- 🔄 Consider alternative data sources
- 📞 Contact API providers for support

## 🆘 If Something Goes Wrong

### Common Issues
1. **"BAG API key not found"**
   - Check your `.env` file has `BAG_API_KEY=your_key`

2. **"Address not found"**
   - Verify Dutch postcode format: `1234AB` (no spaces)
   - Check house number is correct

3. **"Connection error"**
   - Check internet connection
   - APIs might be temporarily down

4. **Very slow performance**
   - Normal for first run (no cached data)
   - Check rate limits in `config.yaml`

### Debug Mode
```bash
# Enable detailed logging
echo "DEBUG_MODE=true" >> .env

# Run single test to see detailed errors
python tools/quick_test.py "YOUR_ADDRESS" "dakkapel"
```

### Get Help
- 📋 Check `logs/ai_readable/` for error summaries
- 🔍 Use `python tools/house_viewer.py` to explore issues
- 📚 Review the context documents for API details

## 🤖 Using Results with Claude

### Generate Reports
```bash
python tools/house_viewer.py "1012JS 1"
# Select option 5: "Generate Claude-friendly report"
```

### Questions to Ask Claude
- "Which renovation types should I prioritize for my MVP?"
- "What are the main technical challenges I'll face?"
- "How do the results vary between different houses?"
- "What features have the best API support?"

---

## 🎉 You're Ready!

Start with:
```bash
python tools/quick_test.py "YOUR_FIRST_ADDRESS" "dakkapel"
```

Then move to the full test suite when you're confident everything works.

Good luck testing your renovation MVP APIs! 🏗️