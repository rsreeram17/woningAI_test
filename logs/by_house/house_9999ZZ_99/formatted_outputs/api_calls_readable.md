
## DSO_Search API Call - 11:18:36

**House:** 9999ZZ 99 | **Session:** DSO_DetailedQuery_Test_20250918_111836
**Endpoint:** `/activiteiten/_zoek`
**Status:** ✅ SUCCESS
**Duration:** 0.116s

### Request Summary:
```json
{
  "request_id": "c5411992",
  "method": "POST",
  "url": "https://service.omgevingswet.overheid.nl/publiek/toepasbare-regels/api/zoekinterface/v2/activiteiten/_zoek",
  "headers": {
    "Content-Type": "application/json",
    "User-Agent": "Dutch-Renovation-Tester/1.0",
    "x-api-key": "***REDACTED***"
  },
  "payload": {
    "zoekterm": "dakkapel",
    "sortering": "besteMatch"
  },
  "params": null,
  "timeout": 30,
  "timestamp": 1758187116.499029
}
```

### Response Summary:
- **Size:** 10.93 KB
- **HTTP Status:** 200

### Key Response Data:
```json
{
  "status_code": 200
}
```

---

## BAG API Call - 11:18:36

**House:** 9999ZZ 99 | **Session:** DSO_DetailedQuery_Test_20250918_111836
**Endpoint:** `/adressenuitgebreid`
**Status:** ✅ SUCCESS
**Duration:** 0.079s

### Request Summary:
```json
{
  "request_id": "c7d69266",
  "method": "GET",
  "url": "https://api.bag.kadaster.nl/lvbag/individuelebevragingen/v2/adressenuitgebreid",
  "headers": {
    "Content-Type": "application/json",
    "User-Agent": "Dutch-Renovation-Tester/1.0",
    "X-Api-Key": "***REDACTED***",
    "Accept-Crs": "EPSG:28992"
  },
  "payload": null,
  "params": {
    "postcode": "9999ZZ",
    "huisnummer": 99
  },
  "timeout": 30,
  "timestamp": 1758187116.616509
}
```

### Response Summary:
- **Size:** 1.14 KB
- **HTTP Status:** 200

### Key Response Data:
```json
{
  "status_code": 200
}
```

---
