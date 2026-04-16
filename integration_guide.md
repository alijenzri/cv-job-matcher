# CareerSeed: .NET Microservices Integration Guide

Because the CareerSeed infrastructure splits standard CRUD business operations (.NET) away from machine learning logic (Python AI Engine), seamless network communication is strictly required.

This guide provides exactly how to integrate the C# Backend with the AI microservice, specifically targeting the two primary user-facing job features.

---

## 1. Batch Matching Existing Data (MatchV2)

**Use Case:** Your .NET application already fetched a massive array of job listings from an external provider APIs (e.g. Adzuna). You need the Python engine to mathematically rank them against the user's uploaded CV file.

### HTTP Request Details
- **Endpoint:** `POST {PYTHON_SERVER_URL}/api/v1/matchV2`
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `file`: The raw binary of the PDF/DOCX file.
  - `jobs_data`: A raw JSON String containing the array of job objects.
  
### C# HttpClient Example
```csharp
public async Task<string> RankAdzunaJobsAsync(byte[] cvFileBytes, string fileName, string adzunaJsonArray)
{
    using var client = new HttpClient();
    
    // Construct the Multipart Form
    using var form = new MultipartFormDataContent();
    
    // 1. Attach CV File
    var fileContent = new ByteArrayContent(cvFileBytes);
    fileContent.Headers.ContentType = MediaTypeHeaderValue.Parse("application/pdf");
    form.Add(fileContent, "file", fileName);
    
    // 2. Attach Job Array (as a string, to prevent C# to FastAPI Pydantic parsing errors)
    form.Add(new StringContent(adzunaJsonArray), "jobs_data");

    // 3. Fire Request!
    var response = await client.PostAsync("http://127.0.0.1:8000/api/v1/matchV2", form);
    response.EnsureSuccessStatusCode();

    // Returns a MatchBatchResultV2 JSON string
    return await response.Content.ReadAsStringAsync();
}
```

---

## 2. Live Web Scraping & Searching

**Use Case:** You do not have jobs loaded from an API. You want the Python AI Engine to autonomously search LinkedIn in real-time based on the CV.

### HTTP Request Details
- **Endpoint:** `POST {PYTHON_SERVER_URL}/api/v1/cv/search-jobs`
- **Content-Type:** `multipart/form-data`
- **Headers:** *Parameters must be passed as headers to safely avoid mixups with file uploads.*
  - `job-title`: The string query (e.g. "React Developer").
  - `location`: Target city/country (e.g. "Paris").
  - `max-results`: Minimum search depth integer (max 50).
- **Parameters:**
  - `file`: The raw CV File binary.

### C# HttpClient Example
```csharp
public async Task<string> LiveSearchAndRankAsync(byte[] cvFileBytes, string fileName, string jobTitle, string location)
{
    using var client = new HttpClient();
    
    // Add Query Data to Headers
    client.DefaultRequestHeaders.Add("job-title", jobTitle);
    client.DefaultRequestHeaders.Add("location", location);
    client.DefaultRequestHeaders.Add("max-results", "10");

    using var form = new MultipartFormDataContent();
    
    // Attach CV File
    var fileContent = new ByteArrayContent(cvFileBytes);
    fileContent.Headers.ContentType = MediaTypeHeaderValue.Parse("application/pdf");
    form.Add(fileContent, "file", fileName);

    // Fire Request! Note: This may take ~45 seconds due to live web scraping.
    // Configure HttpClient.Timeout = TimeSpan.FromMinutes(2) heavily before trying!
    var response = await client.PostAsync("http://127.0.0.1:8000/api/v1/cv/search-jobs", form);
    response.EnsureSuccessStatusCode();

    // Returns a JobSearchResponse JSON string
    return await response.Content.ReadAsStringAsync();
}
```

---

## JSON Response Handling Recommendations
The endpoints both return a deeply nested object holding parsed User CV statistics alongside a ranked array of `results`.
We highly recommend using `System.Text.Json` combined with a `try/catch` block. Since Generative AI (LLMs) can occasionally time-out or fail, the resulting array items will usually degrade gracefully (returning `"Intelligence generation failed."` strings rather than crashing the properties), preventing fatal C# deserialization errors.
