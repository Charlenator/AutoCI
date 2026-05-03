import os, json, base64, sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('/Users/MAC/Desktop/VSC/TCN/AutoCI/backend/.env')
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

print(f"SUPABASE_URL: {url}")
print(f"SUPABASE_SERVICE_KEY: {'[set]' if key else '[MISSING]'} (len={len(key) if key else 0})")

if not url or not key:
    print("ERROR: Missing Supabase credentials")
    sys.exit(1)

supa = create_client(url, key)

# Test 1: Table read works
try:
    r = supa.table("industry_benchmarks").select("*").limit(1).execute()
    print(f"Table query OK: {len(r.data)} rows")
except Exception as e:
    print(f"Table query FAILED: {e}")

# Test 2: Storage bucket list
try:
    buckets = supa.storage.list_buckets()
    bucket_names = [b.get("name", b.get("id", "?")) for b in buckets]
    print(f"Buckets found: {bucket_names}")
except Exception as e:
    print(f"Storage list_buckets FAILED: {e}")

# Test 3: Upload a tiny file to cv-attachments
test_content = b"hello world"
try:
    resp = supa.storage.from_("cv-attachments").upload(
        "diagnostic_test.txt",
        test_content,
        {"content-type": "text/plain"},
    )
    print(f"Upload OK: {resp}")
except Exception as e:
    print(f"Upload FAILED: {e}")
    # Try with explicit headers
    try:
        # Some versions of supabase-py need the service key explicitly
        # Let's try getting the raw headers used
        import httpx
        hdrs = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        r2 = httpx.post(
            f"{url}/storage/v1/object/cv-attachments/diagnostic_test_http.txt",
            headers=hdrs,
            content=test_content
        )
        print(f"Direct HTTP upload: status={r2.status_code}, body={r2.text[:200]}")
    except Exception as e2:
        print(f"Direct HTTP upload also FAILED: {e2}")
