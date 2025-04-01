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
import { Loader2, AlertCircle, CheckCircle, Download, RefreshCw } from "lucide-react"
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { VulnerabilityChart, VulnerabilityStats } from "@/components/ui/vulnerability-chart"

// API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

// Sample vulnerability data for demonstration
const sampleVulnerabilityData = {
  critical: 3,
  high: 7,
  medium: 12,
  low: 8,
  info: 15
};

// For development/demo mode
const DEMO_MODE = false;

export default function ScannerPage() {
  const router = useRouter()
  const [url, setUrl] = useState("")
  const [isScanning, setIsScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState(0)
  const [scanCompleted, setScanCompleted] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)
  const [scanResults, setScanResults] = useState<any>(null)
  const [scanId, setScanId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("overview")

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
          const response = await fetch(`${API_URL}/scan/${scanId}`);
          if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
          }
          
          const data = await response.json();
          
          // Update progress
          setScanProgress(data.progress || Math.min(scanProgress + 5, 95));
          
          if (data.status === 'completed') {
            clearInterval(interval);
            setIsScanning(false);
            setScanCompleted(true);
            
            // Get scan results
            const resultsResponse = await fetch(`${API_URL}/scan/${scanId}/result`);
            if (!resultsResponse.ok) {
              throw new Error(`Failed to get results: ${resultsResponse.status}`);
            }
            
            const resultsData = await resultsResponse.json();
            setScanResults(resultsData);
          } else if (data.status === 'failed') {
            clearInterval(interval);
            setIsScanning(false);
            setScanError(data.message || 'Scan failed');
          }
        } catch (error) {
          clearInterval(interval);
          setIsScanning(false);
          setScanError(error instanceof Error ? error.message : "Failed to check scan status");
        }
      }, 3000);
      
      return () => clearInterval(interval);
    }
  }, [scanId, isScanning, scanProgress]);

  // Simulate scan progress for demo mode
  useEffect(() => {
    if (DEMO_MODE && isScanning) {
      const interval = setInterval(() => {
        setScanProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval)
            setIsScanning(false)
            setScanCompleted(true)
            // Simulate scan results
            setScanResults({
              url: url,
              timestamp: new Date().toISOString(),
              scanDuration: "2m 34s",
              vulnerabilities: {
                critical: sampleVulnerabilityData.critical,
                high: sampleVulnerabilityData.high,
                medium: sampleVulnerabilityData.medium,
                low: sampleVulnerabilityData.low,
                info: sampleVulnerabilityData.info
              },
              findings: [
                {
                  id: "1",
                  name: "SQL Injection",
                  severity: "critical",
                  description: "SQL injection vulnerability in login form",
                  location: "/login.php",
                  remediation: "Use prepared statements and parameterized queries"
                },
                {
                  id: "2",
                  name: "Cross-Site Scripting (XSS)",
                  severity: "high",
                  description: "Reflected XSS in search parameter",
                  location: "/search?q=",
                  remediation: "Implement proper output encoding"
                },
                {
                  id: "3",
                  name: "Insecure Direct Object Reference",
                  severity: "medium",
                  description: "IDOR vulnerability in user profile",
                  location: "/profile?id=123",
                  remediation: "Implement proper access controls"
                },
                {
                  id: "4",
                  name: "Missing Security Headers",
                  severity: "low",
                  description: "Missing Content-Security-Policy header",
                  location: "HTTP Headers",
                  remediation: "Add appropriate security headers"
                },
                {
                  id: "5",
                  name: "Information Disclosure",
                  severity: "info",
                  description: "Server version information disclosed",
                  location: "HTTP Headers",
                  remediation: "Configure server to hide version information"
                }
              ]
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

    if (!isValidUrl(url)) {
      setScanError("Please enter a valid URL")
      return
    }
    
    // Reset states
    setScanError(null)
    setScanResults(null)
    setScanCompleted(false)
    setScanProgress(0)
    setIsScanning(true)
    
    if (DEMO_MODE) {
      // Demo mode uses simulated progress
      console.log("Starting demo scan for:", url);
      return;
    }
    
    // Production mode - call the actual API
    try {
      const response = await fetch(`${API_URL}/scan/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      const data = await response.json();
      setScanId(data.id);
      console.log("Scan started with ID:", data.id);
    } catch (error) {
      setScanError(error instanceof Error ? error.message : "An unknown error occurred");
      setIsScanning(false);
    }
  }

  // Download a report
  const downloadReport = async (format: string) => {
    if (DEMO_MODE) {
      // For demo mode, just log the action
      console.log(`Downloading report in ${format} format for URL: ${scanResults.url}`);
      return;
    }
    
    // Production mode - download actual reports
    try {
      if (!scanResults || !scanId) {
        throw new Error('No scan results available');
      }
      
      window.open(`${API_URL}/scan/${scanId}/report/${format}?include_details=true`, '_blank');
    } catch (error) {
      console.error('Error downloading report:', error);
      setScanError(error instanceof Error ? error.message : "Failed to download report");
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
        <CardContent>
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
                <CardTitle>Scan Results</CardTitle>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => downloadReport("pdf")}>
                    <Download className="mr-2 h-4 w-4" /> PDF
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => downloadReport("html")}>
                    <Download className="mr-2 h-4 w-4" /> HTML
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => downloadReport("json")}>
                    <Download className="mr-2 h-4 w-4" /> JSON
                  </Button>
                </div>
              </div>
              <CardDescription>
                Scan completed for {scanResults.url} on {new Date(scanResults.timestamp).toLocaleString()}
              </CardDescription>
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
                    <Alert variant={scanResults.vulnerabilities && scanResults.vulnerabilities.critical > 0 ? "destructive" : "success"}>
                      {scanResults.vulnerabilities && scanResults.vulnerabilities.critical > 0 ? (
                        <AlertCircle className="h-4 w-4" />
                      ) : (
                        <CheckCircle className="h-4 w-4" />
                      )}
                      <AlertTitle>
                        {scanResults.vulnerabilities && scanResults.vulnerabilities.critical > 0
                          ? `${scanResults.vulnerabilities.critical} Critical Vulnerabilities Found`
                          : "No Critical Vulnerabilities Found"}
                      </AlertTitle>
                      <AlertDescription>
                        {scanResults.vulnerabilities && scanResults.vulnerabilities.critical > 0
                          ? "Your website has critical security issues that need immediate attention."
                          : "Your website passed critical security checks."}
                      </AlertDescription>
                    </Alert>
                    
                    <VulnerabilityStats data={scanResults.vulnerabilities || {}} />
                    
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
                              <dd>{scanResults?.scanDuration || "N/A"}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="font-medium">Total Issues:</dt>
                              <dd>
                              {scanResults?.vulnerabilities && typeof scanResults.vulnerabilities === 'object'
                                  ? Object.values(scanResults.vulnerabilities).reduce(
                                      (a: number, b) => a + (typeof b === 'number' ? b : 0), // Ensure b is a number
                                      0 as number
                                    )
                                  : 0}
                              </dd>
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
                            <div className="text-5xl font-bold mb-2 text-red-500">
                              {scanResults.vulnerabilities && scanResults.vulnerabilities.critical > 0 ? "High" : 
                               scanResults.vulnerabilities && scanResults.vulnerabilities.high > 0 ? "Medium" : "Low"}
                            </div>
                            <p className="text-gray-500">
                              {scanResults.vulnerabilities && scanResults.vulnerabilities.critical > 0
                                ? "Critical vulnerabilities require immediate attention"
                                : scanResults.vulnerabilities && scanResults.vulnerabilities.high > 0
                                ? "High severity issues should be addressed soon"
                                : "Your website has a good security posture"}
                            </p>
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
                        scanResults.findings.map((finding: any) => (
                          <TableRow key={finding.id}>
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
                          data={scanResults.vulnerabilities || {}} 
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
                          data={scanResults.vulnerabilities || {}} 
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
                }}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                New Scan
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}
    </div>
  )
} 