# CareerSeed AI - User Experience Guide

This document illustrates the step-by-step user journey, explaining exactly what is happening behind the scenes for each feature.

---

## 🧑‍💻 Feature: "Rank My Existing Jobs" (MatchV2)
*(Often accessed via a "Scan My Jobs" or "Adzuna Job Feed" button on the UI)*

1. **User Action:** The student clicks "Upload CV" and selects their PDF. They hit a button to rank the current job feed.
2. **Behind the Scenes:** The UI tells the C# backend to package all 30 jobs currently stored in the frontend state alongside the user's PDF, and sends it directly to the Python AI.
3. **What to Expect:** Within basically 2 seconds, the dashboard refreshes. All 30 jobs are now mathematically re-ordered.
4. **The Results UI:**
   - Next to each job is a crisp percentage: **"89% Match"**.
   - If the user clicks "View Details" on any of the Top 5 jobs, they will see personalized text: *"Your backend experience is very strong, but this job strictly requires CI/CD Docker pipelines which are absent from your CV."*

---

## 🌍 Feature: "Live Hunt on LinkedIn" (/cv/search-jobs)
*(Often accessed via a "Hunt for New Jobs" specific tab on the UI)*

1. **User Action:** The user fills out a mini-form: Job Title ("Cyber Security Analyst"), Location ("Berlin"), and uploads their CV. They click "Start AI Hunt".
2. **Behind the Scenes:** This is a heavy request. The frontend should display a nice loading spinner. The Python AI is literally opening LinkedIn, searching for Berlin cyber security roles, clicking into 20+ profiles, copying their descriptions, and routing them to the math brain.
3. **What to Expect:** The loading spinner will spin for around 45 to 60 seconds depending on LinkedIn's server latency.
4. **The Results UI:**
   - The user receives a beautiful grid containing brand new jobs sourced directly from the internet right at that moment.
   - The jobs are completely pre-ranked using the user's uploaded CV attributes, taking the guesswork out of the application process.

## 📝 Parsing Feedback
When you first upload a CV, the system takes roughly 5 to 10 seconds to read it. Our generative AI engine scans paragraphs and bullet points, attempting to deduce your true name and distinct skills. If your PDF is heavily encrypted, password-protected, or essentially just a scanned image of paper, the system cannot see text. In these rare events, the UI will display your name as "Unknown" and skills as blank arrays, though it will gracefully attempt to continue processing any readable data.
