# Linux for DevOps - Log Analysis & Filtering Lab


## What You'll Learn

By the end of this lab, you'll be able to:
- Analyze production-style Apache access logs in real-time
- Filter logs using grep, awk, sed, cut
- Find patterns, errors, and anomalies quickly
- Build one-liners that solve complex log analysis problems
- Debug production issues using log analysis

---

## Lab Setup

### Step 1: Create Docker Compose File

Create a directory and files:

```bash
mkdir log-analysis-lab
cd log-analysis-lab
```

**docker-compose.yml:**

```yaml
version: '3'
services:
  apache:
    image: httpd:2.4
    ports:
      - "8080:80"
    volumes:
      - ./logs:/usr/local/apache2/logs
    container_name: apache-server

  log-generator:
    image: python:3.9-slim
    volumes:
      - ./logs:/logs
      - ./generator.py:/generator.py
    command: python /generator.py
    depends_on:
      - apache
    container_name: log-generator
```

**generator.py:**

```python
#!/usr/bin/env python3
import random
import time
import requests
from datetime import datetime

APACHE_URL = "http://apache:80"

# Simulate different endpoints
ENDPOINTS = [
    "/",
    "/api/users",
    "/api/products",
    "/api/orders",
    "/login",
    "/logout",
    "/admin",
    "/static/image.jpg",
    "/api/search",
    "/checkout"
]

# Simulate different user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "curl/7.68.0",
    "python-requests/2.28.0",
    "Googlebot/2.1"
]

# Simulate different IPs
IPS = [
    "192.168.1.100",
    "192.168.1.101", 
    "10.0.0.50",
    "172.16.0.10",
    "203.0.113.42"  # This one will generate errors
]

def generate_traffic():
    while True:
        try:
            endpoint = random.choice(ENDPOINTS)
            user_agent = random.choice(USER_AGENTS)
            ip = random.choice(IPS)
            
            headers = {
                'User-Agent': user_agent,
                'X-Forwarded-For': ip
            }
            
            # 70% success, 20% 404, 10% 500
            rand = random.random()
            
            if rand < 0.7:
                # Normal request
                requests.get(f"{APACHE_URL}{endpoint}", headers=headers, timeout=2)
            elif rand < 0.9:
                # 404 error
                requests.get(f"{APACHE_URL}/nonexistent", headers=headers, timeout=2)
            else:
                # Simulate server error by invalid request
                try:
                    requests.get(f"{APACHE_URL}/admin", headers=headers, timeout=0.001)
                except:
                    pass
            
            # Random delay between requests (0.1 to 2 seconds)
            time.sleep(random.uniform(0.1, 2))
            
        except Exception as e:
            print(f"Error generating traffic: {e}")
            time.sleep(1)

if __name__ == "__main__":
    print("Starting log generator...")
    time.sleep(5)  # Wait for Apache to start
    generate_traffic()
```

**Start the lab:**

```bash
# Start containers
docker-compose up -d

# Verify they're running
docker ps

# Check logs are being generated
ls -lh logs/
```

You should see `access_log` file growing.

---

## Part 1: Basic Log Viewing (15 minutes)

### Understanding Apache Log Format

**Sample Apache log line:**
```
172.17.0.1 - - [27/Jan/2026:10:30:45 +0000] "GET /api/users HTTP/1.1" 200 1234
```

**Format breakdown:**
- `172.17.0.1` - IP address
- `[27/Jan/2026:10:30:45 +0000]` - Timestamp
- `"GET /api/users HTTP/1.1"` - Request method, path, protocol
- `200` - Status code
- `1234` - Response size in bytes

### Basic Viewing Commands

```bash
# Go to logs directory
cd logs/

# View entire log
cat access_log

# View first 10 lines
head -10 access_log

# View last 10 lines
tail -10 access_log

# Follow logs in real-time (MOST IMPORTANT)
tail -f access_log

# View logs with line numbers
cat -n access_log

# View logs page by page
less access_log
# Press 'q' to quit
# Press '/' to search
# Press 'n' for next match
```

**Pro Tip:** Always use `tail -f` in one terminal while testing in another. You'll see issues in real-time.

---

## Part 2: Filtering with grep (30 minutes)

### Basic grep Operations

```bash
# Find all 404 errors
grep "404" access_log

# Find all 500 errors
grep "500" access_log

# Find all errors (4xx and 5xx)
grep -E " (4|5)[0-9]{2} " access_log

# Case-insensitive search
grep -i "error" access_log

# Show line numbers
grep -n "404" access_log

# Count occurrences
grep -c "404" access_log

# Invert match (exclude lines)
grep -v "200" access_log
```

### Advanced grep Patterns

```bash
# Find specific endpoint
grep "/api/users" access_log

# Find requests from specific IP
grep "192.168.1.100" access_log

# Find GET requests only
grep "GET" access_log

# Find POST requests
grep "POST" access_log

# Multiple patterns (OR)
grep -E "404|500" access_log

# Multiple patterns (AND) - using pipe
grep "POST" access_log | grep "404"

# Show 5 lines after match (context)
grep -A 5 "500" access_log

# Show 5 lines before match
grep -B 5 "500" access_log

# Show 5 lines before and after
grep -C 5 "500" access_log
```

### Real-World grep Scenarios

**Scenario 1: Find all failed login attempts**
```bash
grep "/login" access_log | grep -E " (401|403) "
```

**Scenario 2: Find requests taking long time (large response)**
```bash
# Responses larger than 100000 bytes
awk '$10 > 100000' access_log
```

**Scenario 3: Find suspicious activity**
```bash
# Multiple failed requests from same IP
grep "404" access_log | cut -d' ' -f1 | sort | uniq -c | sort -nr
```

**Practice Exercise 1:**

1. Find all 404 errors
2. Count how many 404 errors exist
3. Find which IPs are causing 404 errors
4. Exclude 200 status codes and see what remains

---

## Part 3: Column Extraction with awk (30 minutes)

### Understanding awk Basics

awk treats each line as fields separated by spaces. `$1` is first field, `$2` is second, etc.

```bash
# Print first field (IP address)
awk '{print $1}' access_log

# Print first and last field
awk '{print $1, $NF}' access_log

# Print status code (9th field)
awk '{print $9}' access_log

# Print IP and status code
awk '{print $1, $9}' access_log
```

### awk with Conditions

```bash
# Print lines where status code is 404
awk '$9 == 404' access_log

# Print lines where status code is NOT 200
awk '$9 != 200' access_log

# Print lines where status is 4xx or 5xx
awk '$9 >= 400' access_log

# Print lines where response size > 1000 bytes
awk '$10 > 1000' access_log
```

### awk for Calculations

```bash
# Count total requests
awk 'END {print NR}' access_log

# Count 404 errors
awk '$9 == 404 {count++} END {print count}' access_log

# Calculate total bytes transferred
awk '{sum += $10} END {print sum}' access_log

# Calculate average response size
awk '{sum += $10; count++} END {print sum/count}' access_log

# Count requests per status code
awk '{status[$9]++} END {for (s in status) print s, status[s]}' access_log
```

### awk for Grouping and Counting

```bash
# Count requests per IP
awk '{ip[$1]++} END {for (i in ip) print i, ip[i]}' access_log

# Count requests per endpoint
awk '{print $7}' access_log | sort | uniq -c | sort -nr

# Count status codes
awk '{print $9}' access_log | sort | uniq -c | sort -nr

# Top 10 IPs by request count
awk '{print $1}' access_log | sort | uniq -c | sort -nr | head -10
```

**Practice Exercise 2:**

1. Find top 5 IPs making the most requests
2. Calculate total bytes transferred
3. Find which endpoint has most 404 errors
4. Count how many requests each status code has

---

## Part 4: Text Manipulation with sed (20 minutes)

### Basic sed Operations

```bash
# Replace text (first occurrence per line)
sed 's/GET/POST/' access_log

# Replace all occurrences
sed 's/GET/POST/g' access_log

# Delete lines containing pattern
sed '/404/d' access_log

# Keep only lines with pattern
sed -n '/404/p' access_log

# Print specific lines (10-20)
sed -n '10,20p' access_log

# Print first 10 lines (like head)
sed -n '1,10p' access_log
```

### sed for Log Cleaning

```bash
# Extract just the timestamp
sed 's/.*\[\(.*\)\].*/\1/' access_log

# Remove IP addresses (anonymize)
sed 's/^[0-9.]*/-/' access_log

# Extract just the HTTP method
sed 's/.*"\([A-Z]*\).*/\1/' access_log

# Convert to CSV format
sed 's/ /,/g' access_log
```

**Practice Exercise 3:**

1. Extract all timestamps from logs
2. Remove all 200 status code lines
3. Replace all IPs with "REDACTED"

---

## Part 5: Column Extraction with cut (15 minutes)

### Basic cut Operations

```bash
# Cut by delimiter (space) - get first field
cut -d' ' -f1 access_log

# Get multiple fields
cut -d' ' -f1,9 access_log

# Get range of fields
cut -d' ' -f1-3 access_log

# Get everything from field 7 onwards
cut -d' ' -f7- access_log
```

### Combining cut with Other Commands

```bash
# Get unique IPs
cut -d' ' -f1 access_log | sort | uniq

# Count requests per IP
cut -d' ' -f1 access_log | sort | uniq -c | sort -nr

# Get all status codes
cut -d' ' -f9 access_log | sort | uniq

# Get all endpoints
cut -d' ' -f7 access_log | sort | uniq
```

---

## Part 6: Advanced One-Liners (30 minutes)

### Real Production Scenarios

**Scenario 1: Find top 10 IPs hitting your server**
```bash
awk '{print $1}' access_log | sort | uniq -c | sort -nr | head -10
```

**Scenario 2: Find which endpoints are getting 404s**
```bash
awk '$9 == 404 {print $7}' access_log | sort | uniq -c | sort -nr
```

**Scenario 3: Requests per minute analysis**
```bash
awk '{print $4}' access_log | cut -d: -f1-3 | sort | uniq -c
```

**Scenario 4: Find slow responses (large response size)**
```bash
awk '$10 > 50000 {print $1, $7, $10}' access_log | sort -k3 -nr
```

**Scenario 5: Count HTTP methods used**
```bash
awk '{print $6}' access_log | tr -d '"' | sort | uniq -c | sort -nr
```

**Scenario 6: Find potential DDoS - same IP, many requests**
```bash
awk '{print $1}' access_log | sort | uniq -c | sort -nr | head -20
```

**Scenario 7: Status code distribution**
```bash
awk '{print $9}' access_log | sort | uniq -c | sort -k1 -nr
```

**Scenario 8: Find all POST requests with errors**
```bash
grep "POST" access_log | awk '$9 >= 400 {print $1, $7, $9}'
```

**Scenario 9: Bytes transferred per IP**
```bash
awk '{ip[$1]+=$10} END {for (i in ip) print i, ip[i]}' access_log | sort -k2 -nr
```

**Scenario 10: Find requests with no referrer (potential bot)**
```bash
awk '$11 == "\"-\"" {print $1, $7}' access_log
```

### Building Complex Pipelines

**Pipeline 1: Top 10 IPs causing 404 errors**
```bash
grep " 404 " access_log | awk '{print $1}' | sort | uniq -c | sort -nr | head -10
```

**Pipeline 2: Endpoints with highest error rate**
```bash
awk '$9 >= 400 {print $7}' access_log | sort | uniq -c | sort -nr | head -10
```

**Pipeline 3: Hourly request distribution**
```bash
awk '{print $4}' access_log | cut -d: -f2 | sort | uniq -c
```

**Pipeline 4: Find IPs accessing admin pages**
```bash
grep "/admin" access_log | awk '{print $1}' | sort | uniq -c | sort -nr
```

---

## Part 7: Real-Time Monitoring (20 minutes)

### Live Log Analysis

**Monitor errors in real-time:**
```bash
tail -f access_log | grep --color=auto -E " (4|5)[0-9]{2} "
```

**Monitor specific IP:**
```bash
tail -f access_log | grep "192.168.1.100"
```

**Monitor POST requests:**
```bash
tail -f access_log | grep "POST"
```

**Real-time status code count:**
```bash
tail -f access_log | awk '{print $9}' | uniq -c
```

### Creating a Live Dashboard

**Create a simple monitoring script:**

```bash
# Create monitor.sh
nano monitor.sh
```

```bash
#!/bin/bash

LOGFILE="logs/access_log"

echo "=== Apache Log Monitor ==="
echo "Monitoring: $LOGFILE"
echo ""

while true; do
    clear
    echo "=== Last Update: $(date) ==="
    echo ""
    
    echo "=== Status Code Distribution ==="
    tail -100 $LOGFILE | awk '{print $9}' | sort | uniq -c | sort -nr
    echo ""
    
    echo "=== Top 5 IPs (Last 100 requests) ==="
    tail -100 $LOGFILE | awk '{print $1}' | sort | uniq -c | sort -nr | head -5
    echo ""
    
    echo "=== Recent Errors ==="
    tail -20 $LOGFILE | grep -E " (4|5)[0-9]{2} " | tail -5
    echo ""
    
    sleep 5
done
```

```bash
# Make executable
chmod +x monitor.sh

# Run it
./monitor.sh
```

---

## Part 8: Performance Analysis (15 minutes)

### Find Performance Issues

**Largest responses:**
```bash
awk '{print $10, $7}' access_log | sort -nr | head -10
```

**Most requested endpoints:**
```bash
awk '{print $7}' access_log | sort | uniq -c | sort -nr | head -10
```

**Requests by hour:**
```bash
awk '{print $4}' access_log | cut -d: -f2 | sort | uniq -c
```

**Calculate average response size:**
```bash
awk '{sum+=$10; count++} END {print "Average:", sum/count, "bytes"}' access_log
```

---

## Part 9: Security Analysis (15 minutes)

### Detect Suspicious Activity

**Find potential brute force attempts:**
```bash
grep "/login" access_log | awk '{print $1}' | sort | uniq -c | sort -nr | head -10
```

**Find SQL injection attempts:**
```bash
grep -i "select\|union\|drop\|insert" access_log
```

**Find directory traversal attempts:**
```bash
grep -E "\.\./|\.\.%2F" access_log
```

**Find requests with suspicious user agents:**
```bash
grep -i "scanner\|bot\|curl" access_log | grep -v "Googlebot"
```

**Find failed admin access:**
```bash
grep "/admin" access_log | grep -E " (401|403) "
```

---

## Practical Lab Exercises

### Exercise 1: Investigation Workflow (15 minutes)

**Scenario:** Your application is slow. Investigate using logs.

```bash
# Step 1: Check overall status codes
awk '{print $9}' logs/access_log | sort | uniq -c | sort -nr

# Step 2: Find if any IP is hammering the server
awk '{print $1}' logs/access_log | sort | uniq -c | sort -nr | head -10

# Step 3: Find which endpoints are slow (large responses)
awk '$10 > 10000 {print $7, $10}' logs/access_log | sort -k2 -nr | head -10

# Step 4: Check error rate over time
grep -E " (4|5)[0-9]{2} " logs/access_log | awk '{print $4}' | cut -d: -f1-3 | sort | uniq -c
```

### Exercise 2: Create Your Own Analysis Script (20 minutes)

Create `analyze.sh`:

```bash
#!/bin/bash

LOGFILE=$1

if [ -z "$LOGFILE" ]; then
    echo "Usage: $0 <logfile>"
    exit 1
fi

echo "=== Log Analysis Report ==="
echo "File: $LOGFILE"
echo "Generated: $(date)"
echo ""

echo "=== Total Requests ==="
wc -l $LOGFILE
echo ""

echo "=== Status Code Distribution ==="
awk '{print $9}' $LOGFILE | sort | uniq -c | sort -nr
echo ""

echo "=== Top 10 IPs ==="
awk '{print $1}' $LOGFILE | sort | uniq -c | sort -nr | head -10
echo ""

echo "=== Top 10 Endpoints ==="
awk '{print $7}' $LOGFILE | sort | uniq -c | sort -nr | head -10
echo ""

echo "=== Error Rate ==="
TOTAL=$(wc -l < $LOGFILE)
ERRORS=$(awk '$9 >= 400' $LOGFILE | wc -l)
echo "Total Requests: $TOTAL"
echo "Error Requests: $ERRORS"
echo "Error Rate: $(awk "BEGIN {printf \"%.2f%%\", ($ERRORS/$TOTAL)*100}")"
echo ""

echo "=== Bytes Transferred ==="
awk '{sum+=$10} END {print "Total:", sum/1024/1024, "MB"}' $LOGFILE
```

```bash
chmod +x analyze.sh
./analyze.sh logs/access_log
```

---

## Cheat Sheet

### Quick Reference

```bash
# VIEWING
tail -f logs/access_log              # Follow logs live
tail -100 logs/access_log            # Last 100 lines
head -50 logs/access_log             # First 50 lines
less logs/access_log                 # Paginated view

# FILTERING
grep "404" logs/access_log           # Find 404s
grep -v "200" logs/access_log        # Exclude 200s
grep -E "(404|500)" logs/access_log  # Multiple patterns
grep -c "404" logs/access_log        # Count matches

# COLUMN EXTRACTION
awk '{print $1}' logs/access_log               # IP address
awk '{print $9}' logs/access_log               # Status code
awk '$9 == 404' logs/access_log                # Filter by status
cut -d' ' -f1 logs/access_log                  # First field

# COUNTING & SORTING
sort logs/access_log | uniq -c                          # Count unique
awk '{print $1}' logs/access_log | sort | uniq -c      # Count IPs
awk '{print $9}' logs/access_log | sort | uniq -c      # Count status codes

# ONE-LINERS
# Top 10 IPs
awk '{print $1}' logs/access_log | sort | uniq -c | sort -nr | head -10

# Error rate
awk 'BEGIN {total=0; errors=0} {total++; if ($9>=400) errors++} END {print "Error rate:", (errors/total)*100"%"}' logs/access_log

# Requests per minute
awk '{print $4}' logs/access_log | cut -d: -f1-3 | sort | uniq -c

# Top endpoints
awk '{print $7}' logs/access_log | sort | uniq -c | sort -nr | head -10
```

---

## Homework Assignment

### Assignment 1: Daily Analysis

For the next 3 days, run these analyses on your logs:

1. What's the error rate each day?
2. Which IP makes the most requests?
3. Which endpoint gets hit the most?
4. What's the average response size?

### Assignment 2: Build a Monitor

Create a script that:
1. Monitors logs in real-time
2. Alerts (prints "ALERT!") when error rate > 10%
3. Shows top 5 IPs every 10 seconds
4. Tracks requests per minute

### Assignment 3: Incident Investigation

Write a script that answers:
1. Was there a spike in 500 errors? When?
2. Which IP caused the most 404s?
3. What was the slowest endpoint (largest response)?
4. Were there any suspicious patterns?

---

## Cleanup

```bash
# Stop containers
docker-compose down

# Remove logs (optional)
rm -rf logs/

# Or keep for practice
```

---

## Tips & Tricks

**Tip 1:** Always use `tail -f` in one terminal while analyzing in another

**Tip 2:** Build complex commands incrementally:
```bash
cat access_log              # Start simple
cat access_log | grep 404   # Add filter
cat access_log | grep 404 | awk '{print $1}'  # Add extraction
# And so on...
```

**Tip 3:** Save your useful one-liners as aliases:
```bash
alias top-ips='awk "{print \$1}" logs/access_log | sort | uniq -c | sort -nr | head -10'
alias error-rate='grep -c -E " (4|5)[0-9]{2} " logs/access_log'
```

**Tip 4:** Use `watch` for live updates:
```bash
watch -n 2 'tail -20 logs/access_log | grep 404'
```

**Tip 5:** Redirect output to files for reports:
```bash
./analyze.sh logs/access_log > daily-report-$(date +%Y%m%d).txt
```

---

## Common Mistakes to Avoid

1. **Not using `-f` with tail for live monitoring**
2. **Forgetting to sort before using uniq**
3. **Not escaping special characters in grep**
4. **Trying to process entire logs instead of using tail**
5. **Not testing one-liners on small samples first**

---

## Next Steps

After mastering this lab:
- Learn `jq` for JSON log analysis
- Explore ELK stack (Elasticsearch, Logstash, Kibana)
- Try log aggregation tools (Fluentd, Logstash)
- Learn Prometheus for metrics
- Study Grafana for visualization

---

**Remember:** These skills work on ANY log file. Apache, Nginx, application logs, system logs - same techniques!
