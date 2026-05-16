"""
Multi-Database Bulk Postgres Data Generator
Usage:
    python generate_data.py <url1> <url2> <url3> ...
    python generate_data.py --file db_urls.txt

db_urls.txt format (one URL per line):
    postgresql://user:pass@host1:5432/db1
    postgresql://user:pass@host2:5432/db2
"""

db_link = 'postgresql://postgres:Admin1234@rds-migration.cvik8accw2tk.ap-south-1.rds.amazonaws.com:5432/postgres'

import sys
import random
import string
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import psycopg2
    from psycopg2.extras import execute_batch
except ImportError:
    print("Installing psycopg2-binary...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2.extras import execute_batch

# ─── Config ────────────────────────────────────────────────────────────────────

ROWS_USERS       = 500
ROWS_DEPARTMENTS = 30
ROWS_EMPLOYEES   = 500
ROWS_PROJECTS    = 300
ROWS_AUDIT_LOGS  = 2000
ROWS_ORDERS      = 1000
ROWS_PRODUCTS    = 200
ROWS_EVENTS      = 1500
BATCH_SIZE       = 200
MAX_WORKERS      = 4

# ─── Data Pools ────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Akhil","Ravi","Priya","Amit","Neha","Kiran","Raj","Pooja","Vijay","Ananya",
    "Suresh","Deepa","Arjun","Meera","Dev","Ishaan","Nisha","Rohit","Kavya","Tarun",
    "Shreya","Manish","Lata","Aditya","Divya","Sanjay","Ritika","Vikram","Swati","Nikhil",
    "James","Emma","Oliver","Sophia","Liam","Ava","Noah","Isabella","William","Mia",
    "Ethan","Charlotte","Mason","Amelia","Logan","Harper","Lucas","Evelyn","Benjamin","Abigail"
]
LAST_NAMES = [
    "Sharma","Verma","Patel","Kumar","Singh","Reddy","Nair","Iyer","Das","Bose",
    "Mehta","Joshi","Rao","Gupta","Shah","Mishra","Tiwari","Pandey","Chaudhary","Kapoor",
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Taylor",
    "Anderson","Thomas","Jackson","White","Harris","Martin","Thompson","Moore","Young","Lee"
]
DEPARTMENTS = [
    "Engineering","DevOps","Platform","Security","Product","Design","Marketing",
    "Sales","HR","Finance","Data Science","ML/AI","QA","Infrastructure","Support",
    "Cloud Ops","Site Reliability","Backend","Frontend","Mobile","Analytics",
    "Compliance","Legal","Business Development","Customer Success","Research",
    "Architecture","Database","Networking","Operations"
]
ROLES       = ["admin","editor","viewer","moderator","superuser","developer","analyst","manager"]
STATUSES    = ["active","inactive","pending","archived","suspended"]
JOB_TITLES  = [
    "Senior Engineer","Staff Engineer","DevOps Lead","SRE","Platform Engineer",
    "Backend Developer","Cloud Architect","ML Engineer","Security Engineer","Data Engineer",
    "Frontend Developer","Fullstack Engineer","DevSecOps Engineer","Kubernetes Specialist",
    "Solutions Architect","Engineering Manager","Tech Lead","Principal Engineer","CTO","VP Engineering"
]
TAGS        = ["kubernetes","aws","devops","mlops","aiops","terraform","docker",
               "python","linux","cicd","helm","argocd","istio","prometheus","grafana"]
ACTIONS     = ["CREATE","UPDATE","DELETE","LOGIN","LOGOUT","DEPLOY","SCALE",
               "RESTART","ROLLBACK","APPROVE","REJECT","EXPORT","IMPORT","CLONE","ARCHIVE"]
RESOURCES   = ["deployment","pod","service","configmap","secret","namespace",
               "user","project","pipeline","cluster","node","ingress","pvc","job","cronjob"]
PRODUCT_CATEGORIES = ["Software","Training","Consulting","Support","License","Cloud","Hardware","Service"]
EVENT_TYPES = ["user.login","user.logout","deploy.start","deploy.success","deploy.failed",
               "scale.up","scale.down","alert.fired","alert.resolved","backup.done","backup.failed",
               "payment.success","payment.failed","signup","subscription.renewed","subscription.cancelled"]
ORDER_STATUSES = ["pending","processing","completed","cancelled","refunded","shipped","delivered"]
SEVERITIES = ["info","warning","critical","debug","error"]

# ─── Helpers ───────────────────────────────────────────────────────────────────

def rstr(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def email(first, last):
    domains = ["gmail.com","yahoo.com","outlook.com","company.io","dev.net","corp.co","tech.in"]
    return f"{first.lower()}.{last.lower()}{random.randint(1,9999)}@{random.choice(domains)}"

def rdate(start=730, end=0):
    return datetime.now() - timedelta(days=random.randint(end, start))

def rip():
    return ".".join(str(random.randint(1,254)) for _ in range(4))

def rphone():
    return f"+{random.randint(1,99)}-{random.randint(1000000000,9999999999)}"

def rmoney(lo, hi):
    return round(random.uniform(lo, hi), 2)

def rname():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

# ─── Schema ────────────────────────────────────────────────────────────────────

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    phone       VARCHAR(25),
    role        VARCHAR(50),
    status      VARCHAR(20) DEFAULT 'active',
    country     VARCHAR(60),
    timezone    VARCHAR(60),
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,
    head_name   VARCHAR(100),
    budget      NUMERIC(14,2),
    headcount   INT DEFAULT 0,
    location    VARCHAR(100),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employees (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id) ON DELETE CASCADE,
    department_id   INT REFERENCES departments(id),
    job_title       VARCHAR(100),
    salary          NUMERIC(12,2),
    level           VARCHAR(20),
    manager_name    VARCHAR(100),
    joined_at       TIMESTAMP,
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    category    VARCHAR(80),
    sku         VARCHAR(50) UNIQUE,
    price       NUMERIC(10,2),
    cost        NUMERIC(10,2),
    stock       INT DEFAULT 0,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id),
    product_id      INT REFERENCES products(id),
    quantity        INT,
    unit_price      NUMERIC(10,2),
    total_amount    NUMERIC(12,2),
    status          VARCHAR(30) DEFAULT 'pending',
    payment_method  VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projects (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    description TEXT,
    status      VARCHAR(30) DEFAULT 'active',
    priority    VARCHAR(20),
    start_date  DATE,
    end_date    DATE,
    budget      NUMERIC(14,2),
    spent       NUMERIC(14,2),
    team_size   INT,
    tags        TEXT,
    created_by  INT REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id          SERIAL PRIMARY KEY,
    user_id     INT REFERENCES users(id),
    action      VARCHAR(100),
    resource    VARCHAR(100),
    resource_id INT,
    ip_address  VARCHAR(45),
    user_agent  TEXT,
    status_code INT,
    duration_ms INT,
    timestamp   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id          SERIAL PRIMARY KEY,
    event_type  VARCHAR(100),
    user_id     INT REFERENCES users(id),
    payload     JSONB,
    severity    VARCHAR(20),
    source      VARCHAR(100),
    region      VARCHAR(50),
    timestamp   TIMESTAMP DEFAULT NOW()
);
"""

# ─── Seed Functions ────────────────────────────────────────────────────────────

def seed_users(cur, n):
    rows = []
    seen = set()
    countries  = ["India","USA","UK","Germany","Canada","Australia","Singapore","Brazil","UAE","Japan"]
    timezones  = ["Asia/Kolkata","America/New_York","Europe/London","Asia/Singapore","America/Los_Angeles"]
    attempts   = 0
    while len(rows) < n and attempts < n * 3:
        attempts += 1
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        em = email(fn, ln)
        if em in seen:
            continue
        seen.add(em)
        rows.append((
            f"{fn} {ln}", em, rphone(),
            random.choice(ROLES), random.choice(STATUSES),
            random.choice(countries), random.choice(timezones),
            rdate(730), rdate(30)
        ))
    execute_batch(cur,
        """INSERT INTO users (name,email,phone,role,status,country,timezone,created_at,updated_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (email) DO NOTHING""",
        rows, page_size=BATCH_SIZE)
    cur.execute("SELECT id FROM users")
    return [r[0] for r in cur.fetchall()]

def seed_departments(cur):
    rows = [(
        d, rname(), rmoney(50000, 10000000),
        random.randint(5, 200),
        random.choice(["Bangalore","Mumbai","Delhi","Hyderabad","Remote","New York","London"])
    ) for d in DEPARTMENTS]
    execute_batch(cur,
        """INSERT INTO departments (name,head_name,budget,headcount,location)
           VALUES (%s,%s,%s,%s,%s) ON CONFLICT (name) DO NOTHING""",
        rows, page_size=BATCH_SIZE)
    cur.execute("SELECT id FROM departments")
    return [r[0] for r in cur.fetchall()]

def seed_employees(cur, user_ids, dept_ids, n):
    levels = ["Junior","Mid","Senior","Staff","Principal","Lead","Manager","Director"]
    sample = random.sample(user_ids, min(n, len(user_ids)))
    rows = [(
        uid, random.choice(dept_ids), random.choice(JOB_TITLES),
        rmoney(300000, 5000000), random.choice(levels), rname(),
        rdate(2000, 30), random.choice([True]*4 + [False])
    ) for uid in sample]
    execute_batch(cur,
        """INSERT INTO employees (user_id,department_id,job_title,salary,level,manager_name,joined_at,is_active)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        rows, page_size=BATCH_SIZE)

def seed_products(cur, n):
    rows = []
    seen_skus = set()
    for _ in range(n):
        name = f"{random.choice(TAGS).capitalize()} {random.choice(['Pro','Suite','Kit','Plan','Bundle','License'])} {random.randint(1,99)}"
        sku  = f"SKU-{rstr(4).upper()}-{random.randint(1000,9999)}"
        if sku in seen_skus:
            continue
        seen_skus.add(sku)
        cost  = rmoney(100, 50000)
        price = round(cost * random.uniform(1.2, 3.0), 2)
        rows.append((name, random.choice(PRODUCT_CATEGORIES), sku, price, cost, random.randint(0, 1000), True, rdate(365)))
    execute_batch(cur,
        """INSERT INTO products (name,category,sku,price,cost,stock,is_active,created_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (sku) DO NOTHING""",
        rows, page_size=BATCH_SIZE)
    cur.execute("SELECT id, price FROM products")
    return cur.fetchall()

def seed_orders(cur, user_ids, products, n):
    payment_methods = ["credit_card","debit_card","upi","netbanking","razorpay","stripe","paypal","wallet"]
    rows = []
    for _ in range(n):
        uid = random.choice(user_ids)
        prod_id, price = random.choice(products)
        qty = random.randint(1, 10)
        rows.append((uid, prod_id, qty, price, round(price * qty, 2),
                     random.choice(ORDER_STATUSES), random.choice(payment_methods), rdate(365), rdate(30)))
    execute_batch(cur,
        """INSERT INTO orders (user_id,product_id,quantity,unit_price,total_amount,status,payment_method,created_at,updated_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        rows, page_size=BATCH_SIZE)

def seed_projects(cur, user_ids, n):
    adjectives = ["Advanced","Cloud-Native","Production","Automated","Distributed","Resilient","Scalable","Hybrid"]
    nouns      = ["Pipeline","Platform","Cluster","Gateway","Mesh","Dashboard","Engine","Framework"]
    priorities = ["low","medium","high","critical"]
    rows = []
    for _ in range(n):
        name       = f"{random.choice(adjectives)} {random.choice(TAGS).capitalize()} {random.choice(nouns)}"
        start_date = rdate(365, 30).date()
        end_date   = start_date + timedelta(days=random.randint(30, 365))
        budget     = rmoney(10000, 2000000)
        rows.append((name, f"Initiative to build and operate {name.lower()}.",
                     random.choice(STATUSES), random.choice(priorities),
                     start_date, end_date, budget,
                     round(budget * random.uniform(0, 1.1), 2),
                     random.randint(2, 20),
                     ",".join(random.sample(TAGS, 3)),
                     random.choice(user_ids)))
    execute_batch(cur,
        """INSERT INTO projects (name,description,status,priority,start_date,end_date,budget,spent,team_size,tags,created_by)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        rows, page_size=BATCH_SIZE)

def seed_audit_logs(cur, user_ids, n):
    uas = [
        "Mozilla/5.0 (Linux; kubectl/1.28)","curl/7.88","Terraform/1.5","ArgoCD/2.8",
        "Mozilla/5.0 (Macintosh; Safari/537)","Python-requests/2.31","Go-http-client/1.1"
    ]
    rows = [(
        random.choice(user_ids), random.choice(ACTIONS), random.choice(RESOURCES),
        random.randint(1, 9999), rip(), random.choice(uas),
        random.choice([200,200,200,201,204,400,401,403,404,500]),
        random.randint(5, 5000), rdate(180)
    ) for _ in range(n)]
    execute_batch(cur,
        """INSERT INTO audit_logs (user_id,action,resource,resource_id,ip_address,user_agent,status_code,duration_ms,timestamp)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        rows, page_size=BATCH_SIZE)

def seed_events(cur, user_ids, n):
    regions = ["ap-south-1","us-east-1","eu-west-1","us-west-2","ap-southeast-1","ap-northeast-1"]
    sources = ["api-gateway","k8s-controller","auth-service","payment-service","deploy-bot","monitoring"]
    rows = []
    for _ in range(n):
        uid   = random.choice(user_ids)
        etype = random.choice(EVENT_TYPES)
        payload = '{' + f'"user_id":{uid},"event":"{etype}","ref":"{rstr(8)}","duration_ms":{random.randint(10,3000)}' + '}'
        rows.append((etype, uid, payload, random.choice(SEVERITIES),
                     random.choice(sources), random.choice(regions), rdate(90)))
    execute_batch(cur,
        """INSERT INTO events (event_type,user_id,payload,severity,source,region,timestamp)
           VALUES (%s,%s,%s::jsonb,%s,%s,%s,%s)""",
        rows, page_size=BATCH_SIZE)

# ─── Per-DB Runner ─────────────────────────────────────────────────────────────

def run_for_db(db_url, db_index, total_dbs):
    label = f"[DB {db_index}/{total_dbs}] {db_url.split('@')[-1]}"
    results = {"url": db_url, "label": label, "success": False, "counts": {}, "error": None, "elapsed": 0}
    t0 = time.time()
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor()
        print(f"\n{label} — connected ✅")

        cur.execute(CREATE_TABLES)
        conn.commit()

        print(f"{label} — seeding users ({ROWS_USERS})...")
        user_ids = seed_users(cur, ROWS_USERS)

        print(f"{label} — seeding departments ({ROWS_DEPARTMENTS})...")
        dept_ids = seed_departments(cur)
        conn.commit()

        print(f"{label} — seeding employees ({ROWS_EMPLOYEES})...")
        seed_employees(cur, user_ids, dept_ids, ROWS_EMPLOYEES)

        print(f"{label} — seeding products ({ROWS_PRODUCTS})...")
        products = seed_products(cur, ROWS_PRODUCTS)
        conn.commit()

        print(f"{label} — seeding orders ({ROWS_ORDERS})...")
        if products:
            seed_orders(cur, user_ids, products, ROWS_ORDERS)

        print(f"{label} — seeding projects ({ROWS_PROJECTS})...")
        seed_projects(cur, user_ids, ROWS_PROJECTS)
        conn.commit()

        print(f"{label} — seeding audit_logs ({ROWS_AUDIT_LOGS})...")
        seed_audit_logs(cur, user_ids, ROWS_AUDIT_LOGS)

        print(f"{label} — seeding events ({ROWS_EVENTS})...")
        seed_events(cur, user_ids, ROWS_EVENTS)
        conn.commit()

        for table in ["users","departments","employees","products","orders","projects","audit_logs","events"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            results["counts"][table] = cur.fetchone()[0]

        results["success"] = True
        results["elapsed"] = round(time.time() - t0, 2)
        print(f"{label} — ✅ done in {results['elapsed']}s")

    except Exception as e:
        results["error"] = str(e)
        print(f"{label} — ❌ failed: {e}")
        try:
            conn.rollback()
        except:
            pass
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass
    return results

# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    db_urls = []
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("Provide path to file: --file db_urls.txt")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            db_urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        db_urls = [u for u in sys.argv[1:] if u.strip()]

    if not db_urls:
        print("No DB URLs provided.")
        sys.exit(1)

    total = len(db_urls)
    print(f"\n🚀 Multi-DB Bulk Data Generator")
    print(f"   Databases  : {total}")
    print(f"   Users/db   : {ROWS_USERS}")
    print(f"   Employees  : {ROWS_EMPLOYEES}")
    print(f"   Products   : {ROWS_PRODUCTS}")
    print(f"   Orders     : {ROWS_ORDERS}")
    print(f"   Projects   : {ROWS_PROJECTS}")
    print(f"   Audit logs : {ROWS_AUDIT_LOGS}")
    print(f"   Events     : {ROWS_EVENTS}")
    print(f"   Workers    : {min(MAX_WORKERS, total)}")

    all_results = []
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, total)) as pool:
        futures = {pool.submit(run_for_db, url, i+1, total): url for i, url in enumerate(db_urls)}
        for future in as_completed(futures):
            all_results.append(future.result())

    print("\n" + "═"*70)
    print("  SUMMARY")
    print("═"*70)
    for r in all_results:
        status = "✅" if r["success"] else "❌"
        print(f"\n{status}  {r['label']}")
        if r["success"]:
            print(f"   Elapsed : {r['elapsed']}s")
            for table, count in r["counts"].items():
                print(f"   {table:<15} → {count:>6} rows")
        else:
            print(f"   Error   : {r['error']}")

    success = sum(1 for r in all_results if r["success"])
    print(f"\n{'═'*70}")
    print(f"  {success}/{total} databases seeded successfully.")
    print("═"*70)

if __name__ == "__main__":
    main()

# usage: python create-dumy-data.py postgresql://postgres:Admin1234@rds-migration.cvik8accw2tk.ap-south-1.rds.amazonaws.com:5432/postgres