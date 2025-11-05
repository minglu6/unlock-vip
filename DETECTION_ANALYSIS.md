# CSDN Detection Analysis: How unlock-vip Makes Requests

## Executive Summary
The unlock-vip application uses Python's `requests` library to communicate with CSDN. It sends requests with specific HTTP headers, manages cookies, and calls CSDN APIs directly. Multiple patterns could be detected as automated/shared usage.

---

## 1. HTTP HEADERS AND USER-AGENT STRINGS

### User-Agent String (article_service.py, line 49)
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
```

### Full Request Headers Set (article_service.py, lines 48-64)
```python
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
'Accept-Encoding': 'gzip, deflate, br',
'Connection': 'keep-alive',
'DNT': '1',
'Upgrade-Insecure-Requests': '1',
'Sec-Fetch-Dest': 'document',
'Sec-Fetch-Mode': 'navigate',
'Sec-Fetch-Site': 'none',
'Sec-Fetch-User': '?1',
'Cache-Control': 'max-age=0',
'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
'sec-ch-ua-mobile': '?0',
'sec-ch-ua-platform': '"Windows"'
```

### VIP Unlock Request Headers (article_service.py, lines 122-128)
When calling the unlock API, additional headers are set:
```python
'Accept': '*/*',
'Content-Type': 'application/json; charset=UTF-8',
'Origin': 'https://blog.csdn.net',
'Referer': f'https://blog.csdn.net/article/details/{article_id}',
'X-Requested-With': 'XMLHttpRequest',  # MAJOR DETECTION VECTOR
```

### File Download Service Headers (file_service.py, lines 85-100)
Uses Chrome 141.0.0.0 (different from article service):
```python
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
'Accept': 'application/json, text/plain, */*',
'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
'Accept-Encoding': 'gzip, deflate, br, zstd',
'Content-Type': 'application/json',
'Origin': 'https://download.csdn.net',
'Referer': 'https://download.csdn.net/',
'DNT': '1',
'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
'sec-ch-ua-mobile': '?0',
'sec-ch-ua-platform': '"Windows"',
'Sec-Fetch-Site': 'same-origin',
'Sec-Fetch-Mode': 'cors',
'Sec-Fetch-Dest': 'empty',
```

---

## 2. CRITICAL DETECTION VECTORS

### A. X-Requested-With Header
**Location:** article_service.py, line 127
**Risk Level:** CRITICAL

The header `X-Requested-With: XMLHttpRequest` is a fingerprint of automated tools. CSDN can easily detect this as it's typically only sent by AJAX requests from browsers, not real users.

### B. Inconsistent User-Agent Versions
- Article Service: Chrome 131.0.0.0
- File Download Service: Chrome 141.0.0.0

Real users would have consistent versions. Multiple requests with different Chrome versions suggest parallel request handling or tool switching.

### C. Missing Dynamic Client Hints
The `sec-ch-ua` headers use hardcoded fixed values:
```
"Google Chrome";v="131"
```
Real Chrome browsers send randomized/dynamic values. The static values are easily fingerprinted.

### D. Perfect Header Order
Headers are set in a fixed, static order. Real browsers vary header order. Static order is detectable.

### E. Session Reuse Pattern
**Location:** Multiple service classes (article_service.py, wenku_service.py, file_service.py)

```python
def _load_session(self):
    """从cookies文件加载session"""
    if self.session:
        return  # Reuses existing session
```

Each service maintains a persistent session with loaded cookies. This creates:
- Consistent connection patterns
- Identical request sequences
- Predictable timing patterns

### F. Verify=False (SSL Verification Disabled)
**Location:** article_service.py:135, 234; wenku_service.py:154, 219, 269; file_service.py:167

```python
response = self.session.post(unlock_url, json=payload, timeout=30, verify=False)
```

Disabling SSL verification is a red flag for automated tools. Real browsers always verify SSL.

---

## 3. REQUEST PATTERNS AND SIGNATURES

### A. VIP Article Unlock Flow
1. Request page at `/article/details/{ID}`
2. Immediately POST to `/phoenix/web/v1/vip-article-read` API
3. Payload: `{"articleId": int(article_id)}`
4. Headers include `X-Requested-With: XMLHttpRequest` and Referer

**Signature:** Sequential requests with specific API endpoint calls signal automated extraction.

### B. Document Download Flow
1. GET request to wenku.csdn.net page
2. POST to unlock endpoints:
   - `https://wenku.csdn.net/phoenix/web/v1/vip-article-read`
   - `https://wenku.csdn.net/phoenix/web/v1/vip-wenku-read`
   - `https://blog.csdn.net/phoenix/web/v1/vip-article-read` (fallback)
3. Re-fetch page if unlock succeeds

**Signature:** Multiple POST attempts to unlock endpoints are suspicious.

### C. Download API Calls
**Location:** file_service.py:68

```python
DOWNLOAD_API = "https://download.csdn.net/api/source/detail/v1/download"
```

Direct API calls (not through browser UI) with specific sourceId extraction:
```python
payload = {"sourceId": int(source_id)}
response = self.session.post(self.DOWNLOAD_API, json=payload, ...)
```

**Signature:** Direct API calls bypass normal UI interaction patterns.

---

## 4. COOKIE MANAGEMENT

### Cookie Source (cookies.json)
**Location:** cookie_parser.py:51-95

Supports two formats:
1. JSON: `{"UserToken": "value", "UserInfo": "value", ...}`
2. Cookie String: `name1=value1; name2=value2`

### Cookies Set on Session
```python
for name, value in cookies_dict.items():
    self.session.cookies.set(name, str(value), domain='.csdn.net')
```

### Detectability Issues
- All requests use the SAME cookies across multiple services
- No cookie rotation
- No cookie expiration handling
- Cookies persist across service instances
- No user-specific variation

**Signature:** Identical cookies across multiple requests, services, and time periods.

---

## 5. REQUEST TIMING AND RATE PATTERNS

### Synchronous Design
**Location:** app/api/article.py (download endpoint, lines 14-92)

```python
@router.post("/download", response_model=ArticleResponse)
async def download_article(request: ArticleRequest):
    article_service = ArticleService()
    article_data = article_service.download_article(url)  # Blocking call
    clean_html = article_service.extract_clean_content(...)
    return ArticleResponse(...)
```

Multiple requests to the same article trigger sequential unlock API calls:
1. Request 1: GET article page (30s timeout)
2. Request 2: POST unlock API (30s timeout)  
3. Request 3: GET article again if needed (30s timeout)

**Signature:** Sequential, perfectly timed requests from same IP/session.

### ThreadPoolExecutor for Background Tasks
**Location:** file_service.py:24-56

```python
self._executor = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="FileDownload"
)
```

Parallel requests from thread pool are easily detected by:
- Identical headers from multiple threads
- Burst request patterns
- Fixed 4-thread pool signature

---

## 6. REQUEST BODY PATTERNS

### VIP Article Unlock Payload
```python
payload = {"articleId": int(article_id)}
```

### Wenku Unlock Payload (Multiple attempts)
```python
payload = {"articleId": wenku_id, "wenkuId": wenku_id}
```

### File Download Payload
```python
payload = {"sourceId": int(source_id)}
```

**Signature:** Minimal JSON payloads with specific field names. Real browser requests have much larger/nested payloads.

---

## 7. POTENTIAL CSDN DETECTION MECHANISMS

### Server-Side Detection (High Confidence)
1. **X-Requested-With Header**: Automated tool fingerprint
2. **verify=False in SSL**: Only tools disable this
3. **Missing Dynamic Characteristics**: 
   - Fixed sec-ch-ua values
   - Consistent header order
   - Identical session reuse
4. **Direct API Calls**: Calls to `/phoenix/web/v1/` endpoints that aren't called by regular UI
5. **Request Sequencing**: Unlock API calls always followed by page re-fetch
6. **Rate Limiting**: Multiple rapid requests to same endpoints

### Detection by Request Patterns
1. **User-Agent Version Mismatch**: 131 vs 141 in same session
2. **Perfect Request Timing**: Automated delays instead of human-like variance
3. **Cookie Consistency**: Same cookies used across days/weeks without refresh
4. **ThreadPool Fingerprinting**: Exactly 4 parallel requests is suspicious
5. **API Endpoint Discovery**: Calling internal `/phoenix/` endpoints indicates code analysis

### DNS/Network Level Detection
1. **Reverse DNS**: IP belongs to datacenter/cloud provider (not home ISP)
2. **TLS Fingerprinting**: requests library has identifiable TLS signature
3. **JA3 Fingerprinting**: Can identify requests library by SSL handshake patterns
4. **Connection Patterns**: Persistent keep-alive connections from same IP

---

## 8. COOKIE NAMES AND DETECTION

### Expected CSDN Cookies (from cookies.json.example)
```
UserToken              - Session token
UserInfo              - User identification
dc_sid                - CSDN session ID
uuid_tt_dd            - Device fingerprint
fid                   - Browser fingerprint
Hm_lvt_6bcd52f51...  - Analytics tracking
c_segment             - Segment tracking
c_first_ref           - First referrer tracking
c_first_page          - First page tracking
```

**Risk:** If multiple users/IPs use identical cookies, this is easily detected as shared account abuse.

---

## 9. SUMMARY OF DETECTABLE PATTERNS

### Tier 1: Obvious (Would Catch Most Bots)
- X-Requested-With: XMLHttpRequest header
- verify=False in requests
- Direct /phoenix/web/v1/ API calls
- Missing browser fingerprinting

### Tier 2: Advanced (Would Catch Sophisticated Bots)
- Fixed sec-ch-ua values
- Consistent header ordering
- User-Agent version mismatches
- Perfect request timing patterns

### Tier 3: Very Advanced (Would Catch Even Better Bots)
- TLS fingerprinting
- JA3 signature analysis
- ThreadPool signature (exactly 4 threads)
- Request body structure analysis
- Cookie reuse tracking

### Tier 4: Distributed Pattern Detection
- Shared cookies across IPs
- Similar unlock request sequences
- Same User-Agent from multiple IPs
- Synchronized request patterns

---

## 10. RECOMMENDATIONS FOR AVOIDING DETECTION

(Not providing recommendations as per user instructions)

