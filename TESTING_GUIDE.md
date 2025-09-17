# 🧪 API Testing Guide

This guide shows you how to test each API individually and understand what each test does.

## 🎯 Quick Overview

| Test Command | What It Tests | When to Use |
|-------------|---------------|-------------|
| `python tools/test_bag_api.py "1082GB 43-2"` | Address lookup & building data | ✅ Start here - verify your address works |
| `python tools/test_dso_search.py "1082GB 43-2" "dakkapel"` | Find renovation rules | ✅ Test after BAG works |
| `python tools/test_dso_interactive.py "1082GB 43-2" "dakkapel"` | Permit requirements | ✅ Test permit checking |
| `python tools/test_all_apis.py "1082GB 43-2" "dakkapel"` | All APIs in sequence | ✅ Complete individual testing |
| `python run_tests.py` | Full integration (all houses) | 🚀 Production testing |

## 📋 Step-by-Step Testing

### 1. Start with BAG API (Address Validation)
```bash
python tools/test_bag_api.py "1082GB 43-2"
```

**What this tests:**
- ✅ Can we find your address in the Dutch registry?
- ✅ Do we get building details (year, size, usage)?
- ✅ Can we extract coordinates for DSO APIs?

**Expected output:**
```
✅ Address validated successfully
✅ Building data retrieved
✅ Coordinates extracted: [119879.0, 482161.0]
✅ Ready for DSO integration
```

### 2. Test DSO Search API (Find Rules)
```bash
python tools/test_dso_search.py "1082GB 43-2" "dakkapel"
```

**What this tests:**
- ✅ Can we find renovation rules for "dakkapel"?
- ✅ Do we get functional structure references?
- ✅ Are search results relevant and useful?

**Expected output:**
```
✅ Found 20 functional structure references
✅ Quality Score: 70/100
✅ DSO Search API working perfectly!
```

### 3. Test DSO Interactive API (Permit Checking)
```bash
python tools/test_dso_interactive.py "1082GB 43-2" "dakkapel"
```

**What this tests:**
- ✅ Can we determine if permits are required?
- ✅ What documents need to be submitted?
- ✅ What compliance measures are needed?

**Expected output:**
```
✅ PERMIT REQUIRED for dakkapel
📄 Documents needed: 3
⚖️ Found 5 compliance measures
```

### 4. Test All APIs Together
```bash
python tools/test_all_apis.py "1082GB 43-2" "dakkapel"
```

**What this tests:**
- ✅ Complete workflow from address to permits
- ✅ Integration between all APIs
- ✅ Overall system readiness

**Expected output:**
```
📊 Overall Results: 3/3 tests passed (100.0%)
✅ PASS BAG API - Address lookup and building data
✅ PASS DSO Search API - Find applicable rules and activities
✅ PASS DSO Interactive API - Permit checks and requirements
🚀 Excellent! APIs are ready for integration
```

## 🔧 Testing Different Scenarios

### Test Different Addresses
```bash
# Your current working address
python tools/test_bag_api.py "1082GB 43-2"

# Try other addresses from your config
python tools/test_bag_api.py "1012JS 1"
python tools/test_bag_api.py "2631CR 15"
```

### Test Different Renovation Types
```bash
# Dakkapel (dormer window) - Simple
python tools/test_dso_search.py "1082GB 43-2" "dakkapel"

# Uitbouw (extension) - Complex
python tools/test_dso_search.py "1082GB 43-2" "uitbouw"

# Badkamer verbouwen (bathroom renovation) - Medium
python tools/test_dso_search.py "1082GB 43-2" "badkamer_verbouwen"
```

### Test Full Combinations
```bash
# Test complete flow for different renovations
python tools/test_all_apis.py "1082GB 43-2" "dakkapel"
python tools/test_all_apis.py "1082GB 43-2" "uitbouw"
python tools/test_all_apis.py "1082GB 43-2" "badkamer_verbouwen"
```

## 🎯 Understanding Test Results

### ✅ Success Indicators
- **HTTP 200**: API responds correctly
- **Data found**: Address/rules/permits found
- **Coordinates extracted**: Ready for DSO integration
- **References found**: Can proceed to next API

### ❌ Common Issues & Solutions

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| "Address not found" | Wrong format or non-existent | Check postcode format (1234AB) |
| "No coordinates" | Address exists but no geometry | Try different address |
| "No activities found" | Search term not in Dutch system | Try "dakkapel" or "uitbouw" |
| "HTTP 400" | Payload format issue | API payload needs adjustment |
| "HTTP 404" | Wrong API endpoint | Check API documentation |

## 📊 What Each Test Tells You

### BAG API Test Results
- **Address Quality**: Is your address properly registered?
- **Building Data**: Year, size, usage type available?
- **Coordinates**: Can we locate it for DSO APIs?

### DSO Search Test Results
- **Rule Coverage**: Are there renovation rules for your project?
- **Search Quality**: How relevant are the results?
- **Reference Count**: How many rules apply?

### DSO Interactive Test Results
- **Permit Requirements**: Is a permit needed?
- **Document List**: What paperwork is required?
- **Compliance**: What rules must be followed?

## 🚀 Next Steps Based on Results

### If All Tests Pass (✅✅✅)
```bash
# Ready for full integration testing
python run_tests.py
```

### If Some Tests Fail (✅❌✅)
1. **Identify the failing API**
2. **Check the error messages**
3. **Try different parameters**
4. **Review API documentation**

### If Most Tests Fail (❌❌❌)
1. **Check API keys in .env file**
2. **Verify internet connection**
3. **Try known working address: "1082GB 43-2"**
4. **Check if APIs are temporarily down**

## 💡 Pro Tips

### Fastest Testing Workflow
```bash
# Quick validation
python tools/test_bag_api.py "1082GB 43-2"

# If BAG works, test search
python tools/test_dso_search.py "1082GB 43-2" "dakkapel"

# If search works, test all
python tools/test_all_apis.py "1082GB 43-2" "dakkapel"
```

### Debugging Individual Issues
```bash
# Focus on one API at a time
python tools/test_bag_api.py "YOUR_ADDRESS" 2>&1 | tee bag_debug.log

# Check logs
cat bag_debug.log
```

### Testing Your Actual Houses
```bash
# Use addresses from your config.yaml
python tools/test_all_apis.py "1012JS 1" "dakkapel"
python tools/test_all_apis.py "2631CR 15" "uitbouw"
```

---

**Start testing with: `python tools/test_bag_api.py "1082GB 43-2"`**