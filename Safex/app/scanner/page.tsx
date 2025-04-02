"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs-radix"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Loader2, AlertCircle, CheckCircle, Download, RefreshCw, FileText, FileJson, FileCode } from "lucide-react"
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { VulnerabilityChart, VulnerabilityStats } from "@/components/ui/vulnerability-chart"
import { toast } from "@/components/ui/use-toast"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

// For development/demo mode - set to false to use real backend
const DEMO_MODE = false;

// Define scanner types to match backend enum
const scannerTypes = {
  BASIC: "basic",
  XSS: "xss",
  SQL_INJECTION: "sql_injection",
  FILE_UPLOAD: "file_upload",
  HTTP_METHODS: "http_methods",
  ALL: "all"
};

// Define scanner groups to match backend enum
const scannerGroups = {
  ESSENTIAL: "essential",
  COMMON: "common",
  ADVANCED: "advanced"
};

// Add this type definition near the top of the file, after the imports
interface Vulnerability {
  id?: string;
  name: string;
  severity: string;
  location: string;
  description: string;
  evidence?: string;
  remediation: string;
}

// Interface for vulnerability data in charts
interface VulnerabilityData {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  [key: string]: number;
}

interface ScanResultsType {
  url?: string;
  scan_id?: string;
  timestamp?: string;
  scan_duration?: number;
  scanDuration?: string;
  scanners_used?: string[];
  vulnerabilities?: VulnerabilityData;
  summary?: VulnerabilityData;
  findings?: Vulnerability[];
  report_id?: string;
  status?: string;
  scanners_running?: string[];
}

// Define a default empty vulnerability data for safe rendering when data is missing
const emptyVulnerabilityData: VulnerabilityData = {
  critical: 0,
  high: 0,
  medium: 0,
  low: 0,
  info: 0
};

// Add a debugging component to show which scanners are being used
const DebugScannerInfo = ({ scannersSelected, scannersUsed }: { scannersSelected?: string[], scannersUsed?: string[] }) => {
  if (!scannersSelected && !scannersUsed) return null;
  
  return (
    <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-800 rounded-md text-xs">
      <h4 className="font-bold mb-1">Scanner Debug Info</h4>
      {scannersSelected && (
        <div className="mb-1">
          <span className="font-medium">Selected Scanners: </span>
          {scannersSelected.join(', ')}
        </div>
      )}
      {scannersUsed && (
        <div>
          <span className="font-medium">Actual Scanners Used: </span>
          {scannersUsed.join(', ')}
        </div>
      )}
    </div>
  );
};

export default function ScannerPage() {
  const router = useRouter()
  const [url, setUrl] = useState("")
  const [isScanning, setIsScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState(0)
  const [scanCompleted, setScanCompleted] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)
  const [scanResults, setScanResults] = useState<ScanResultsType | null>(null)
  const [scanId, setScanId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("overview")
  const [reportId, setReportId] = useState<string | null>(null)
  const [scannerGroup, setScannerGroup] = useState<string>(scannerGroups.COMMON)
  const [selectedScanners, setSelectedScanners] = useState<string[]>([
    scannerTypes.XSS, 
    scannerTypes.SQL_INJECTION, 
    scannerTypes.HTTP_METHODS
  ])

  // Function to validate URL
  const isValidUrl = (urlString: string) => {
    try {
      new URL(urlString);
      return true;
    } catch (e) {
      return false;
    }
  };

  // Poll for scan status if we have a scanId
  useEffect(() => {
    if (!DEMO_MODE && scanId && isScanning) {
      const interval = setInterval(async () => {
        try {
          console.log(`[POLL] Polling scan status for ID: ${scanId}`);
          const response = await fetch(`${API_URL}/scanner/${scanId}`);
          
          console.log(`[POLL] Response status: ${response.status}`);
          
          if (!response.ok) {
            console.error(`[POLL] Error response: ${response.status}`);
            throw new Error(`Server responded with status: ${response.status}`);
          }
          
          const data = await response.json();
          console.log(`[POLL] Response data:`, data);
          
          // Update progress based on backend-reported progress
          const newProgress = data.progress || Math.min(scanProgress + 2, 95);
          setScanProgress(newProgress);
          
          // Log scanners being used
          if (data.scanners_used) {
            console.log(`[POLL] Active scanners: ${data.scanners_used.join(', ')}`);
          }
          
          // Check if scan is fully or partially completed
          if (data.status === 'completed') {
            console.log("[POLL] Scan fully completed");
            clearInterval(interval);
            setIsScanning(false);
            setScanCompleted(true);
            fetchAndProcessResults(scanId);
          } 
          else if (data.status === 'partially_completed') {
            console.log("[POLL] Scan partially completed - some scanners still running");
            
            // Check how long we've been scanning
            const scanStartTime = localStorage.getItem(`scan_start_${scanId}`);
            const currentTime = new Date().getTime();
            const maxWaitTimeMs = 3 * 60 * 1000; // 3 minutes max wait
            
            // If we've waited too long, show partial results
            if (scanStartTime && (currentTime - parseInt(scanStartTime)) > maxWaitTimeMs) {
              console.log(`[POLL] Maximum wait time of ${maxWaitTimeMs/1000} seconds exceeded. Showing partial results.`);
              
              clearInterval(interval);
              setIsScanning(false);
              setScanCompleted(true);
              
              toast({
                title: "Partial Results Available",
                description: "Some scans are taking longer than expected. Showing available results now.",
                variant: "default" 
              });
              
              fetchAndProcessResults(scanId);
            } else {
              console.log("[POLL] Continuing to wait for all scanners to complete...");
            }
          }
          else if (data.status === 'failed') {
            console.error(`[POLL] Scan failed: ${data.message || 'Unknown error'}`);
            clearInterval(interval);
            setIsScanning(false);
            setScanError(data.message || 'Scan failed');
            
            toast({
              title: "Scan Failed",
              description: data.message || "The scan process failed. Please try again.",
              variant: "destructive"
            });
          }
        } catch (error) {
          console.error("[POLL] Error polling scan status:", error);
          clearInterval(interval);
          setIsScanning(false);
          setScanError(error instanceof Error ? error.message : "Failed to check scan status");
          
          toast({
            title: "Connection Error",
            description: "Failed to communicate with the scan server.",
            variant: "destructive"
          });
        }
      }, 3000);
      
      return () => clearInterval(interval);
    }
  }, [scanId, isScanning, scanProgress, API_URL]);

  // Function to fetch and process scan results
  const fetchAndProcessResults = async (scanId: string) => {
    try {
      console.log("[RESULTS] Fetching results for scan ID:", scanId);
      const resultsResponse = await fetch(`${API_URL}/scanner/${scanId}/result`);
      
      console.log(`[RESULTS] Response status: ${resultsResponse.status}`);
      
      if (!resultsResponse.ok) {
        console.error(`[RESULTS] Error fetching results: ${resultsResponse.status}`);
        throw new Error(`Failed to get results: ${resultsResponse.status}`);
      }
      
      const resultsData = await resultsResponse.json();
      console.log("[RESULTS] Scan results received:", resultsData);
      
      // Log which scanners were used vs which were requested
      if (resultsData.scanners_used) {
        console.log(`[RESULTS] Scanners used: ${resultsData.scanners_used.join(', ')}`);
        
        // Check if basic scanner was included
        const basicScannerUsed = resultsData.scanners_used.includes(scannerTypes.BASIC);
        console.log(`[RESULTS] Basic scanner used: ${basicScannerUsed}`);
      }
      
      // Check if any scanners are still running
      const isPartialScan = resultsData.status === 'partially_completed';
      if (isPartialScan && resultsData.scanners_running) {
        console.log(`[RESULTS] Scanners still running: ${resultsData.scanners_running.join(', ')}`);
      }
      
      // Ensure the vulnerabilities field is properly set
      if (!resultsData.vulnerabilities && resultsData.summary) {
        console.log("[RESULTS] Setting vulnerabilities from summary data");
        resultsData.vulnerabilities = resultsData.summary;
      }
      
      setScanResults(resultsData);
      
      // Check if a report was automatically created
      if (resultsData.report_id) {
        console.log(`[RESULTS] Report ID found: ${resultsData.report_id}`);
        setReportId(resultsData.report_id);
      }
      
      toast({
        title: isPartialScan ? "Partial Scan Completed" : "Scan Completed",
        description: `The vulnerability scan has ${isPartialScan ? 'partially' : 'been'} completed. Found ${resultsData.findings?.length || 0} vulnerabilities.`,
        variant: "success"
      });
    } catch (error) {
      console.error("[RESULTS] Error fetching results:", error);
      setScanError(error instanceof Error ? error.message : "Failed to fetch scan results");
    }
  };

  // Simulate scan progress for demo mode
  useEffect(() => {
    if (DEMO_MODE && isScanning) {
      const interval = setInterval(() => {
        setScanProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval)
            setIsScanning(false)
            setScanCompleted(true)
            // Simulate scan results with empty data (we don't want fake results)
            setScanResults({
              url: url,
              timestamp: new Date().toISOString(),
              scanDuration: "0s",
              vulnerabilities: emptyVulnerabilityData,
              findings: []
            })
            return 100
          }
          return prev + Math.random() * 5
        })
      }, 500)
      return () => clearInterval(interval)
    }
  }, [isScanning, url]);

  // Start a scan
  const startScan = async () => {
    if (!url) {
      setScanError("Please enter a URL")
      return
    }

    // Make sure URL has proper protocol
    let targetUrl = url;
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      targetUrl = 'http://' + targetUrl;
    }

    if (!isValidUrl(targetUrl)) {
      setScanError("Please enter a valid URL")
      return
    }
    
    // Reset states
    setScanError(null)
    setScanResults(null)
    setScanCompleted(false)
    setScanProgress(0)
    setIsScanning(true)
    setReportId(null)
    
    if (DEMO_MODE) {
      // Demo mode uses simulated progress
      console.log("Starting demo scan for:", targetUrl);
      return;
    }
    
    // Save scan start time for timeout tracking
    const startTime = new Date().getTime().toString();
    localStorage.setItem('scan_start_current', startTime);
    
    // Production mode - call the actual API
    try {
      // Make sure basic scanner is included
      const updatedScanners = [...selectedScanners];
      if (!updatedScanners.includes(scannerTypes.BASIC)) {
        console.log("[SCAN] Adding basic scanner to selected scanners");
        updatedScanners.push(scannerTypes.BASIC);
      }
      
      // Prepare the request payload to match the backend's expectations
      const payload = {
        url: targetUrl, 
        scanners: updatedScanners,
        scanner_group: scannerGroup
      };
      
      console.log("[SCAN] Starting scan with configuration:", {
        url: targetUrl,
        scanners: updatedScanners,
        scannerGroup: scannerGroup,
        apiUrl: API_URL
      });
      console.log("[SCAN] Full payload:", JSON.stringify(payload, null, 2));

      const response = await fetch(`${API_URL}/scanner/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      console.log("[SCAN] Response status:", response.status);
      
      if (!response.ok) {
        let errorText = "Server error";
        try {
          const errorData = await response.json();
          errorText = errorData.detail || `Error ${response.status}`;
          console.error("[SCAN] Server error response (JSON):", errorData);
        } catch (e) {
          errorText = await response.text() || `Error ${response.status}`;
          console.error("[SCAN] Server error response (Text):", errorText);
        }
        throw new Error(`Server responded with status: ${response.status}. ${errorText}`);
      }
      
      const data = await response.json();
      console.log("[SCAN] Scan started successfully:", data);
      setScanId(data.scan_id);
      
      // Save scan start time with the correct ID for timeout tracking
      localStorage.setItem(`scan_start_${data.scan_id}`, startTime);
      
      toast({
        title: "Scan Started",
        description: `Real scan started with scanners: ${updatedScanners.join(', ')}`,
        variant: "default"
      });
    } catch (error) {
      console.error("[SCAN] Error during scan start:", error);
      setScanError(error instanceof Error ? error.message : "An unknown error occurred");
      setIsScanning(false);
      
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to start scan",
        variant: "destructive"
      });
    }
  }

  // Download a report
  const downloadReport = async (format: string) => {
    if (DEMO_MODE) {
      // For demo mode, just log the action
      console.log(`Downloading report in ${format} format for URL: ${scanResults?.url}`);
      toast({
        title: "Demo Mode",
        description: `In real mode, this would download a ${format.toUpperCase()} report.`,
        variant: "default"
      });
      return;
    }
    
    // Production mode - download actual reports
    try {
      if (!reportId) {
        throw new Error('No report ID available');
      }
      
      // Open in new tab to download
      window.open(`${API_URL}/reports/${reportId}/export/${format}`, '_blank');
      
      toast({
        title: "Report Downloaded",
        description: `Your ${format.toUpperCase()} report is being downloaded.`,
        variant: "success"
      });
    } catch (error) {
      console.error('Error downloading report:', error);
      setScanError(error instanceof Error ? error.message : "Failed to download report");
      
      toast({
        title: "Download Failed",
        description: error instanceof Error ? error.message : "Failed to download report",
        variant: "destructive"
      });
    }
  }

  // Generate a new report if needed
  const generateReport = async () => {
    if (DEMO_MODE) {
      setReportId("demo-report-123");
      toast({
        title: "Demo Mode",
        description: "In real mode, this would generate a new report.",
        variant: "default"
      });
      return;
    }
    
    try {
      if (!scanId || !scanResults) {
        throw new Error('No scan results available');
      }
      
      // Request a new report generation
      const response = await fetch(`${API_URL}/reports/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scan_id: scanId })
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      const data = await response.json();
      setReportId(data.report_id);
      
      toast({
        title: "Report Generated",
        description: "Your vulnerability report has been generated successfully.",
        variant: "success"
      });
    } catch (error) {
      console.error('Error generating report:', error);
      toast({
        title: "Report Generation Failed",
        description: error instanceof Error ? error.message : "Failed to generate report",
        variant: "destructive"
      });
    }
  }

  // Get a badge for a severity level
  const getSeverityBadge = (severity: string) => {
    const variants: Record<string, any> = {
      critical: { variant: "destructive", label: "Critical" },
      high: { variant: "destructive", label: "High" },
      medium: { variant: "secondary", label: "Medium" },
      low: { variant: "outline", label: "Low" },
      info: { variant: "success", label: "Info" }
    }
    
    const { variant, label } = variants[severity] || variants.info
    
    return <Badge variant={variant}>{label}</Badge>
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6 text-center">Web Vulnerability Scanner</h1>
      
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Scan a Website</CardTitle>
          <CardDescription>
            Enter the URL of the website you want to scan for vulnerabilities
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col md:flex-row gap-4">
            <Input
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1"
              disabled={isScanning}
            />
            <Button onClick={startScan} disabled={isScanning}>
              {isScanning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Scanning...
                </>
              ) : (
                "Start Scan"
              )}
            </Button>
          </div>
          
          {!DEMO_MODE && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Scanner Group</label>
                  <Select 
                    value={scannerGroup} 
                    onValueChange={(value: string) => setScannerGroup(value)}
                    disabled={isScanning}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select scanner group" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={scannerGroups.ESSENTIAL}>Essential - Basic Security Checks</SelectItem>
                      <SelectItem value={scannerGroups.COMMON}>Common - Standard Security Suite</SelectItem>
                      <SelectItem value={scannerGroups.ADVANCED}>Comprehensive - Complete Analysis</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Scan Options</label>
                  <div className="flex flex-wrap gap-2">
                    <Badge 
                      variant={selectedScanners.includes(scannerTypes.XSS) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => {
                        if (isScanning) return;
                        setSelectedScanners((prev: string[]) => 
                          prev.includes(scannerTypes.XSS) 
                            ? prev.filter((s: string) => s !== scannerTypes.XSS) 
                            : [...prev, scannerTypes.XSS]
                        )
                      }}
                    >
                      XSS
                    </Badge>
                    <Badge 
                      variant={selectedScanners.includes(scannerTypes.SQL_INJECTION) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => {
                        if (isScanning) return;
                        setSelectedScanners((prev: string[]) => 
                          prev.includes(scannerTypes.SQL_INJECTION) 
                            ? prev.filter((s: string) => s !== scannerTypes.SQL_INJECTION) 
                            : [...prev, scannerTypes.SQL_INJECTION]
                        )
                      }}
                    >
                      SQL Injection
                    </Badge>
                    <Badge 
                      variant={selectedScanners.includes(scannerTypes.HTTP_METHODS) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => {
                        if (isScanning) return;
                        setSelectedScanners((prev: string[]) => 
                          prev.includes(scannerTypes.HTTP_METHODS) 
                            ? prev.filter((s: string) => s !== scannerTypes.HTTP_METHODS) 
                            : [...prev, scannerTypes.HTTP_METHODS]
                        )
                      }}
                    >
                      HTTP Methods
                    </Badge>
                    <Badge 
                      variant={selectedScanners.includes(scannerTypes.FILE_UPLOAD) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => {
                        if (isScanning) return;
                        setSelectedScanners((prev: string[]) => 
                          prev.includes(scannerTypes.FILE_UPLOAD) 
                            ? prev.filter((s: string) => s !== scannerTypes.FILE_UPLOAD) 
                            : [...prev, scannerTypes.FILE_UPLOAD]
                        )
                      }}
                    >
                      File Upload
                    </Badge>
                  </div>
                </div>
              </div>
            </>
          )}
          
          {/* Add debug info near the scan button */}
          {!DEMO_MODE && selectedScanners && selectedScanners.length > 0 && !isScanning && (
            <DebugScannerInfo 
              scannersSelected={selectedScanners} 
            />
          )}
          
          {scanError && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{scanError}</AlertDescription>
            </Alert>
          )}
          
          {isScanning && (
            <div className="mt-6">
              <p className="text-sm text-gray-500 mb-2">
                Scanning in progress... {Math.round(scanProgress)}%
              </p>
              <Progress value={scanProgress} />
            </div>
          )}
        </CardContent>
      </Card>
      
      {scanCompleted && scanResults && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>
                    Scan Results 
                    {scanResults.status === 'partially_completed' && (
                      <Badge variant="outline" className="ml-2">Partial</Badge>
                    )}
                  </CardTitle>
                  {scanResults.status === 'partially_completed' && (
                    <p className="text-xs text-orange-500 mt-1">
                      Some scanners are still running. Partial results shown.
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => downloadReport("pdf")}>
                    <FileText className="mr-2 h-4 w-4" /> PDF
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => downloadReport("html")}>
                    <FileCode className="mr-2 h-4 w-4" /> HTML
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => downloadReport("json")}>
                    <FileJson className="mr-2 h-4 w-4" /> JSON
                  </Button>
                </div>
              </div>
              <CardDescription>
                Scan {scanResults.status === 'partially_completed' ? 'partially' : ''} completed for {scanResults.url} on {scanResults.timestamp ? new Date(scanResults.timestamp).toLocaleString() : 'Unknown date'}
              </CardDescription>
              {scanResults.scanners_used && (
                <div className="mt-1 text-xs text-muted-foreground">
                  <span className="font-medium">Scanners used:</span> {scanResults.scanners_used.join(', ')}
                </div>
              )}
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="overview" className="w-full">
                <TabsList className="mb-4">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="findings">Findings</TabsTrigger>
                  <TabsTrigger value="charts">Charts</TabsTrigger>
                </TabsList>
                
                <TabsContent value="overview">
                  <div className="space-y-6">
                    <Alert variant={scanResults.summary && (scanResults.summary.critical > 0 || scanResults.summary.high > 0) ? "destructive" : "success"}>
                      {scanResults.summary && (scanResults.summary.critical > 0 || scanResults.summary.high > 0) ? (
                        <AlertCircle className="h-4 w-4" />
                      ) : (
                        <CheckCircle className="h-4 w-4" />
                      )}
                      <AlertTitle>
                        {scanResults.summary && (scanResults.summary.critical > 0 || scanResults.summary.high > 0)
                          ? `${(scanResults.summary.critical || 0) + (scanResults.summary.high || 0)} Critical/High Vulnerabilities Found`
                          : "No Critical/High Vulnerabilities Found"}
                      </AlertTitle>
                      <AlertDescription>
                        {scanResults.summary && (scanResults.summary.critical > 0 || scanResults.summary.high > 0)
                          ? "Your website has serious security issues that need immediate attention."
                          : "Your website passed critical security checks."}
                      </AlertDescription>
                    </Alert>
                    
                    <VulnerabilityStats data={scanResults.summary || emptyVulnerabilityData} />
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <Card>
                        <CardHeader>
                          <CardTitle>Scan Details</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <dl className="space-y-2">
                            <div className="flex justify-between">
                              <dt className="font-medium">URL:</dt>
                              <dd>{scanResults?.url || "N/A"}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="font-medium">Scan Duration:</dt>
                              <dd>{scanResults?.scan_duration ? `${scanResults.scan_duration.toFixed(2)}s` : "N/A"}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="font-medium">Total Issues:</dt>
                              <dd>
                                {scanResults?.findings?.length || 
                                 (scanResults?.summary && typeof scanResults.summary === 'object'
                                   ? Object.values(scanResults.summary).reduce(
                                       (a, b) => a + (typeof b === 'number' ? b : 0), 
                                       0
                                     )
                                   : 0)
                                }
                              </dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="font-medium">Scan ID:</dt>
                              <dd>{scanId || "N/A"}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="font-medium">Report ID:</dt>
                              <dd>{reportId || "N/A"}</dd>
                            </div>
                          </dl>
                        </CardContent>
                      </Card>
                      
                      <Card>
                        <CardHeader>
                          <CardTitle>Risk Assessment</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-center">
                            <div className={`text-5xl font-bold mb-2 ${
                              scanResults.summary && scanResults.summary.critical > 0 
                                ? "text-red-600" 
                                : scanResults.summary && scanResults.summary.high > 0 
                                  ? "text-orange-500" 
                                  : "text-green-600"
                            }`}>
                              {scanResults.summary && scanResults.summary.critical > 0 ? "High" : 
                               scanResults.summary && scanResults.summary.high > 0 ? "Medium" : "Low"}
                            </div>
                            <p className="text-gray-500">
                              {scanResults.summary && scanResults.summary.critical > 0
                                ? "Critical vulnerabilities require immediate attention"
                                : scanResults.summary && scanResults.summary.high > 0
                                ? "High severity issues should be addressed soon"
                                : "Your website has a good security posture"}
                            </p>
                            
                            {scanResults?.findings && scanResults.findings.length > 0 && (
                              <div className="mt-4 pt-4 border-t border-gray-200">
                                <h3 className="text-sm font-medium mb-2">Top vulnerabilities:</h3>
                                <ul className="text-left space-y-1">
                                  {scanResults.findings.slice(0, 3).map((finding, idx) => (
                                    <li key={idx} className="text-sm">
                                      <span className={`inline-block w-16 ${
                                        finding.severity === 'critical' ? 'text-red-600' :
                                        finding.severity === 'high' ? 'text-orange-500' :
                                        finding.severity === 'medium' ? 'text-yellow-500' :
                                        'text-blue-500'
                                      }`}>
                                        {finding.severity.charAt(0).toUpperCase() + finding.severity.slice(1)}:
                                      </span>
                                      {finding.name}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="findings">
                  <Table>
                    <TableCaption>List of vulnerabilities found during the scan</TableCaption>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Vulnerability</TableHead>
                        <TableHead>Severity</TableHead>
                        <TableHead>Location</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Remediation</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {scanResults.findings && scanResults.findings.length > 0 ? (
                        scanResults.findings.map((finding: any, index: number) => (
                          <TableRow key={finding.id || index}>
                            <TableCell className="font-medium">{finding.name}</TableCell>
                            <TableCell>{getSeverityBadge(finding.severity)}</TableCell>
                            <TableCell className="font-mono text-sm">{finding.location}</TableCell>
                            <TableCell>{finding.description}</TableCell>
                            <TableCell>{finding.remediation}</TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-4">
                            No specific findings available
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TabsContent>
                
                <TabsContent value="charts">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Vulnerability Distribution</CardTitle>
                      </CardHeader>
                      <CardContent className="h-80">
                        <VulnerabilityChart 
                          data={scanResults.vulnerabilities || emptyVulnerabilityData} 
                          type="pie" 
                        />
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardHeader>
                        <CardTitle>Severity Breakdown</CardTitle>
                      </CardHeader>
                      <CardContent className="h-80">
                        <VulnerabilityChart 
                          data={scanResults.vulnerabilities || emptyVulnerabilityData} 
                          type="bar" 
                        />
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" onClick={() => router.push("/")}>
                Back to Home
              </Button>
              <Button
                onClick={() => {
                  setUrl("")
                  setScanResults(null)
                  setScanCompleted(false)
                  setScanId(null)
                  setReportId(null)
                }}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                New Scan
              </Button>
            </CardFooter>
          </Card>
          
          {/* Add debug info with results */}
          {scanCompleted && scanResults && scanResults.scanners_used && (
            <DebugScannerInfo 
              scannersSelected={selectedScanners} 
              scannersUsed={scanResults.scanners_used} 
            />
          )}
        </div>
      )}
    </div>
  )
} 