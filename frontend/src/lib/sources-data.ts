// Static snapshot of the /sources/ endpoint.
// Captured 2026-05-03 from the deployed backend. Update this file when
// corpora or tables change significantly — no need to fetch on every open.

export interface CorpusEntry {
  name: string;
  description: string;
  chunk_count: number;
  confidential_count: number;
  embedded_count: number;
  samples: { chunk_id: string; chunk_text: string; metadata: Record<string, unknown> | null }[];
}

export interface TableEntry {
  name: string;
  description: string;
  row_count: number;
  columns: { column_name: string; data_type: string }[];
  samples: Record<string, unknown>[];
}

export interface SourcesPayload {
  corpora: CorpusEntry[];
  tables: TableEntry[];
  summary: {
    corpora_count: number;
    tables_count: number;
    total_chunks: number;
    total_table_rows: number;
  };
  as_of: number;
}

export const SOURCES_DATA: SourcesPayload = {
  "corpora": [
    {
      "name": "market_intel",
      "description": "Tavily web search snippets cached during Kaizen runs.",
      "chunk_count": 47,
      "confidential_count": 0,
      "embedded_count": 47,
      "samples": [
        {
          "chunk_id": "ffa95030-975a-46fb-aaa4-2e060b300b69",
          "metadata": { "source": "tavily", "topic": "UX Designer hiring trends South Africa", "title": "UX Designer jobs in South Africa - Pnet" },
          "chunk_text": "**UX Designer jobs in South Africa - Pnet**\n3039 results for UX Designer jobs ; UX Designer. IQbusiness. Stellenbosch ; UX Designer. wePlace (Pty) Ltd. JHB - Eastern Suburbs ; UX Designer. wePlace (Pty) Ltd.\nSource: https://www.pnet.co.za/jobs/ux-designer"
        },
        {
          "chunk_id": "2482d9e6-0866-41e5-9fdf-9601c7c41429",
          "metadata": { "source": "tavily", "topic": "Senior Java Developer hiring trends South Africa", "title": "Java Developer Salary Trends in South Africa - OfferZen" },
          "chunk_text": "**Java Developer Salary Trends in South Africa - OfferZen**\nSenior Java developers with more than ten years of experience can expect an additional 42.3% increase for an average salary of R100 584. At this\nSource: https://www.offerzen.com/blog/java-developer-salary-south-africa"
        },
        {
          "chunk_id": "2a2dd9c2-70e2-458c-bbb8-07f30df11f78",
          "metadata": { "source": "tavily", "topic": "Senior Java Developer hiring trends South Africa", "title": "Senior Java Developer Salary in South Africa in 2026 | PayScale" },
          "chunk_text": "**Senior Java Developer Salary in South Africa in 2026 | PayScale**\n# Average Senior Java Developer Salary in South Africa. Is Average Senior Java Developer Salary in South Africa your job title? Use our tool to get a personalized report on your market worth.What's th\nSource: htt..."
        }
      ]
    },
    {
      "name": "adzuna_postings",
      "description": "Live job-posting bodies from Adzuna for salary/skill benchmarking.",
      "chunk_count": 20,
      "confidential_count": 0,
      "embedded_count": 20,
      "samples": [
        {
          "chunk_id": "a6ac454f-8758-40b0-b5ba-cb88d023fb5d",
          "metadata": { "source": "adzuna", "role": "Senior Java Developer", "title": "Senior Java Developer" },
          "chunk_text": "**Senior Java Developer**\nSenior Java Developer Reference: JHB000124-Resou-2 Our company is looking for a Senior Java Developer to join our dynamic team. The successful candidate will be responsible for gathering system and user requirements, building Java modules, and testing fe..."
        },
        {
          "chunk_id": "9bbb17ef-89c2-4b36-965a-6a2b9cb0057d",
          "metadata": { "source": "adzuna", "role": "Senior Java Developer", "title": "Senior Java Developer" },
          "chunk_text": "**Senior Java Developer**\nJob Title: Senior Java Developer We are currently seeking a highly skilled and experienced Senior Java Developer to join our dynamic team. As a Senior Java Developer, you will be responsible for the development, integration, and maintenance of complex se..."
        },
        {
          "chunk_id": "6b25845c-5546-4cec-b959-45d1ded6a0dc",
          "metadata": { "source": "adzuna", "role": "Senior Java Developer", "title": "Senior Java Developer" },
          "chunk_text": "**Senior Java Developer**\nBachelors Degree in Computer Science, Engineering or equivalent educational credentials that tackle the mysteries of technology like an adventurer unearthing ancient secrets!Minimum 5 years of experience in Java development with mastery in frameworks lik..."
        }
      ]
    },
    {
      "name": "dmaic_methodology",
      "description": "Six Sigma DMAIC reference docs (overview, SIPOC, Five Whys, Kanban, TTF). Used for definitional questions.",
      "chunk_count": 5,
      "confidential_count": 0,
      "embedded_count": 5,
      "samples": [
        {
          "chunk_id": "2d67377f-c249-4e0b-a94e-ebc1b809dfbb",
          "metadata": { "phase": "overview", "tool": "dmaic" },
          "chunk_text": "DMAIC is a data-driven Lean Six Sigma methodology used for process improvement. The five phases are: Define, Measure, Analyse, Improve, and Control. Define scopes the problem with SIPOC. Measure establishes baseline metrics. Analyse identifies root causes using tools like Five Wh..."
        },
        {
          "chunk_id": "0c522744-a2ff-4da2-be93-2e8561672fbb",
          "metadata": { "phase": "measure", "tool": "ttf" },
          "chunk_text": "Time to Fill (TTF) is a key recruitment metric measuring the number of days from job requisition approval to candidate acceptance. Industry benchmarks vary by role, seniority, and geography. A high TTF may indicate bottlenecks in screening, interview scheduling, or offer negotiat..."
        },
        {
          "chunk_id": "039b8a16-2c14-482d-b3a1-eaad9857bcd0",
          "metadata": { "phase": "define", "tool": "sipoc" },
          "chunk_text": "SIPOC stands for Suppliers, Inputs, Process, Outputs, Customers. It is a high-level process mapping tool used in the Define phase of DMAIC. Suppliers provide inputs to the process; the process transforms inputs into outputs; customers receive the outputs. A well-defined SIPOC est..."
        }
      ]
    },
    {
      "name": "role_benchmarks",
      "description": "Per-role benchmark notes (Java Developer, Product Manager, UX Designer, Data Engineer).",
      "chunk_count": 4,
      "confidential_count": 0,
      "embedded_count": 4,
      "samples": [
        {
          "chunk_id": "188ccdcd-5dbe-4a82-b011-793ce8bd0571",
          "metadata": { "role": "UX Designer", "region": "South Africa" },
          "chunk_text": "UX Designer benchmarks for South Africa: median TTF 30 days (25th: 20 days, 75th: 42 days). Global median: 28 days. Key skills: Figma, user research, prototyping, data visualisation. Compensation typically in the R500k-R800k range depending on seniority."
        },
        {
          "chunk_id": "10f9f9c0-1438-4636-aa6a-0be3e8764933",
          "metadata": { "role": "general", "tool": "conversion_funnel" },
          "chunk_text": "Recruitment conversion funnel: Industry benchmarks show that for every 100 applicants, approximately 20-30 advance to screening, 10-15 reach first interview, 3-5 reach final interview, and 1-2 receive offers. A high drop-off rate at any stage indicates a process bottleneck that m..."
        },
        {
          "chunk_id": "2d994159-8529-4888-8c53-24768211ca9e",
          "metadata": { "role": "Senior Java Developer", "region": "South Africa" },
          "chunk_text": "Senior Java Developer benchmarks for South Africa: median TTF 35 days (25th percentile: 25 days, 75th percentile: 50 days). Global median: 30 days. Key skills required: Java, Spring Boot, microservices, AWS, Docker, Kubernetes. The role is in high demand with competitive compensa..."
        }
      ]
    },
    {
      "name": "industry_news",
      "description": "NewsAPI articles fetched during Kaizen runs.",
      "chunk_count": 4,
      "confidential_count": 0,
      "embedded_count": 4,
      "samples": [
        {
          "chunk_id": "86503653-1893-40ad-970d-eb5d76817384",
          "metadata": { "source": "newsapi", "topic": "Product Manager hiring South Africa", "title": "Dawn Meats chief Niall Browne: 'Our €4.75 billion turnover makes us a big butcher'" },
          "chunk_text": "**Dawn Meats chief Niall Browne: 'Our €4.75 billion turnover makes us a big butcher'**\nDawn Meats chief on the potential for its New Zealand deal, why red meat is good for us, and climate change challenges for the industry\nSource: https://www.irishtimes.com/business/2026/04/10/da..."
        },
        {
          "chunk_id": "cf9111e9-11e7-4d50-870f-0d9df1d7b507",
          "metadata": { "source": "newsapi", "topic": "Product Manager hiring South Africa", "title": "The All Black, the internet start-up, and the purported stacks of cash and Vatican millions" },
          "chunk_text": "**The All Black, the internet start-up, and the purported stacks of cash and Vatican millions**\nOutlandish claims and unpaid bills from Ireland-based social-media-for-kids Cybersmarties.\nSource: https://www.nzherald.co.nz/business/the-all-black-the-internet-start-up-and-the-purpo..."
        },
        {
          "chunk_id": "8a2cc360-b2a5-427e-8400-11e7cc7ff747",
          "metadata": { "source": "newsapi", "topic": "Product Manager hiring South Africa", "title": "Open Channels FM: Building WooCommerce, Community Lessons from Checkout Summit" },
          "chunk_text": "**Open Channels FM: Building WooCommerce, Community Lessons from Checkout Summit**\nThe episode recaps Checkout Summit in Palermo, highlighting insights from WooCommerce creators. Hosts discuss the event's intimate nature, engaging talks, networking opportunities, and plans for mo..."
        }
      ]
    },
    {
      "name": "kaizen_case_studies",
      "description": "Prior-Kaizen case studies — used by K4 Five Whys and K5 Ishikawa to ground root-cause analysis in precedent.",
      "chunk_count": 3,
      "confidential_count": 0,
      "embedded_count": 3,
      "samples": [
        {
          "chunk_id": "05cb3575-e323-4c9a-8d86-9f15ec9452cf",
          "metadata": { "case": "offer_acceptance", "role": "general" },
          "chunk_text": "Kaizen Case Study — Offer Acceptance Rate: A financial services firm improved offer acceptance from 55% to 82% by restructuring compensation packages and reducing offer-to-start timeline. Key changes: (1) Salary benchmarking against market data showed offers were 15% below median..."
        },
        {
          "chunk_id": "07d83dfa-22c9-436d-9d38-cfeb42496fa7",
          "metadata": { "case": "scheduling", "role": "general" },
          "chunk_text": "Kaizen Case Study — Interview Scheduling Bottleneck: A retail company reduced average scheduling lag from 8.2 to 2.5 days by implementing calendar integration and automated availability polling. Interviewers were required to maintain at least 3 available slots per week. The impro..."
        },
        {
          "chunk_id": "11190021-3f43-45ef-81c8-533f5d094713",
          "metadata": { "case": "ttf_reduction", "role": "Java Developer" },
          "chunk_text": "Kaizen Case Study — Recruitment TTF Reduction: A technology company reduced Senior Java Developer TTF from 62 to 31 days (50% improvement) over 6 months. Key interventions: (1) Standardised technical assessment to reduce interview rounds from 4 to 3; (2) Implemented automated scr..."
        }
      ]
    }
  ],
  "tables": [
    {
      "name": "roles",
      "description": "Job roles being recruited, with KPI targets per role.",
      "row_count": 5,
      "columns": [
        { "column_name": "role_id", "data_type": "uuid" },
        { "column_name": "title", "data_type": "text" },
        { "column_name": "department", "data_type": "text" },
        { "column_name": "target_ttf_days", "data_type": "integer" },
        { "column_name": "opened_date", "data_type": "date" },
        { "column_name": "status", "data_type": "text" },
        { "column_name": "created_at", "data_type": "timestamp with time zone" },
        { "column_name": "updated_at", "data_type": "timestamp with time zone" },
        { "column_name": "target_conversion_rate", "data_type": "double precision" },
        { "column_name": "target_offer_acceptance_rate", "data_type": "double precision" }
      ],
      "samples": [
        { "title": "Senior Java Developer", "status": "open", "role_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "department": "Engineering", "target_ttf_days": 45, "target_conversion_rate": 0.15, "target_offer_acceptance_rate": 0.85 },
        { "title": "Product Manager", "status": "filled", "role_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901", "department": "Product", "target_ttf_days": 60, "target_conversion_rate": 0.15, "target_offer_acceptance_rate": 0.85 },
        { "title": "UX Designer", "status": "open", "role_id": "c3d4e5f6-a7b8-9012-cdef-123456789012", "department": "Design", "target_ttf_days": 40, "target_conversion_rate": 0.15, "target_offer_acceptance_rate": 0.85 }
      ]
    },
    {
      "name": "candidates",
      "description": "Applicants — synthetic pipeline candidates plus CV-driven applicants from the inbound pipeline.",
      "row_count": 148,
      "columns": [
        { "column_name": "candidate_id", "data_type": "uuid" },
        { "column_name": "role_id", "data_type": "uuid" },
        { "column_name": "source_channel", "data_type": "text" },
        { "column_name": "applied_date", "data_type": "date" },
        { "column_name": "external_id", "data_type": "text" },
        { "column_name": "created_at", "data_type": "timestamp with time zone" },
        { "column_name": "name", "data_type": "text" },
        { "column_name": "email", "data_type": "text" },
        { "column_name": "phone", "data_type": "text" },
        { "column_name": "skills_json", "data_type": "jsonb" },
        { "column_name": "experience_summary", "data_type": "text" },
        { "column_name": "cv_storage_path", "data_type": "text" },
        { "column_name": "dedup_hash", "data_type": "text" },
        { "column_name": "is_duplicate", "data_type": "boolean" },
        { "column_name": "missing_fields_json", "data_type": "jsonb" },
        { "column_name": "confidential", "data_type": "boolean" },
        { "column_name": "source_email_id", "data_type": "uuid" }
      ],
      "samples": [
        { "external_id": "V2-SEN-000", "role_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "applied_date": "2026-01-11", "candidate_id": "0fe6a0a2-669b-5e3e-847f-ddc40404d298", "confidential": false, "is_duplicate": false, "source_channel": "LinkedIn" },
        { "external_id": "V2-SEN-001", "role_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "applied_date": "2025-08-23", "candidate_id": "74bf8de3-374e-5338-b145-8f93b4568ebb", "confidential": false, "is_duplicate": false, "source_channel": "Referral" },
        { "external_id": "V2-SEN-002", "role_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "applied_date": "2025-12-22", "candidate_id": "a89dc5f4-1b29-538d-83a8-71efa76b1d12", "confidential": false, "is_duplicate": false, "source_channel": "LinkedIn" }
      ]
    },
    {
      "name": "pipeline_events",
      "description": "Stage transitions for each candidate (Applied → Screening → Interview 1/2 → Offer → Hired).",
      "row_count": 468,
      "columns": [
        { "column_name": "event_id", "data_type": "uuid" },
        { "column_name": "candidate_id", "data_type": "uuid" },
        { "column_name": "stage", "data_type": "text" },
        { "column_name": "event_date", "data_type": "date" },
        { "column_name": "outcome", "data_type": "text" },
        { "column_name": "interviewer_id", "data_type": "uuid" },
        { "column_name": "notes", "data_type": "text" },
        { "column_name": "created_at", "data_type": "timestamp with time zone" }
      ],
      "samples": [
        { "notes": "Application received", "stage": "Applied", "outcome": "Advanced", "event_id": "446e7843-3f2d-4068-9cca-e1b20b38e78a", "event_date": "2026-01-11", "candidate_id": "0fe6a0a2-669b-5e3e-847f-ddc40404d298" },
        { "notes": "Screening completed", "stage": "Screening", "outcome": "Advanced", "event_id": "69dc0539-c68a-4d73-81c3-045c6465593d", "event_date": "2026-01-25", "candidate_id": "0fe6a0a2-669b-5e3e-847f-ddc40404d298" },
        { "notes": "Failed technical / role fit", "stage": "Interview 1", "outcome": "Rejected", "event_id": "8613d8d7-5ad8-4014-8afd-b920e1d0f17b", "event_date": "2026-02-01", "candidate_id": "0fe6a0a2-669b-5e3e-847f-ddc40404d298" }
      ]
    },
    {
      "name": "hires",
      "description": "Successful hires with offer / start dates and salaries.",
      "row_count": 32,
      "columns": [
        { "column_name": "hire_id", "data_type": "uuid" },
        { "column_name": "candidate_id", "data_type": "uuid" },
        { "column_name": "role_id", "data_type": "uuid" },
        { "column_name": "offer_date", "data_type": "date" },
        { "column_name": "start_date", "data_type": "date" },
        { "column_name": "salary", "data_type": "numeric" },
        { "column_name": "accepted", "data_type": "boolean" },
        { "column_name": "created_at", "data_type": "timestamp with time zone" }
      ],
      "samples": [
        { "salary": 1050000.0, "hire_id": "be19dc94-da2f-5758-8aa4-b0e86579a901", "role_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "accepted": true, "offer_date": "2025-11-13", "start_date": "2025-12-04", "candidate_id": "83ec85e1-5d65-5c1e-9eca-bdc48f5ece35" },
        { "salary": 780000.0, "hire_id": "44140e84-7071-534f-af70-7ec1dc8edfaf", "role_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "accepted": true, "offer_date": "2025-12-10", "start_date": "2025-12-31", "candidate_id": "0a43094e-baa9-5e56-a55f-cd7534bcb785" },
        { "salary": 740000.0, "hire_id": "8828fba2-f314-530d-b804-a765c484223d", "role_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "accepted": true, "offer_date": "2026-02-01", "start_date": "2026-02-22", "candidate_id": "d2296ba7-eeae-58b3-8e29-0384856fc950" }
      ]
    },
    {
      "name": "offer_outcomes",
      "description": "Offer outcomes including decline reasons.",
      "row_count": 32,
      "columns": [
        { "column_name": "offer_id", "data_type": "uuid" },
        { "column_name": "candidate_id", "data_type": "uuid" },
        { "column_name": "role_id", "data_type": "uuid" },
        { "column_name": "outcome", "data_type": "text" },
        { "column_name": "decline_reason", "data_type": "text" },
        { "column_name": "created_at", "data_type": "timestamp with time zone" }
      ],
      "samples": [
        { "outcome": "Accepted", "role_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "offer_id": "3501eeae-1d9f-5c80-bab8-cc64fc934967", "candidate_id": "83ec85e1-5d65-5c1e-9eca-bdc48f5ece35", "decline_reason": null },
        { "outcome": "Accepted", "role_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "offer_id": "4ac64487-0822-52f7-afbe-3712cabaaae6", "candidate_id": "0a43094e-baa9-5e56-a55f-cd7534bcb785", "decline_reason": null },
        { "outcome": "Accepted", "role_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "offer_id": "bf8a51e0-ab14-51f4-ad41-badd9705c493", "candidate_id": "d2296ba7-eeae-58b3-8e29-0384856fc950", "decline_reason": null }
      ]
    },
    {
      "name": "industry_benchmarks",
      "description": "External-market benchmark medians (TTF, conversion, OAR) by role family + region.",
      "row_count": 10,
      "columns": [
        { "column_name": "benchmark_id", "data_type": "uuid" },
        { "column_name": "role_family", "data_type": "text" },
        { "column_name": "region", "data_type": "text" },
        { "column_name": "median_ttf_days", "data_type": "double precision" },
        { "column_name": "p25_ttf_days", "data_type": "double precision" },
        { "column_name": "p75_ttf_days", "data_type": "double precision" },
        { "column_name": "sample_size", "data_type": "integer" },
        { "column_name": "data_source", "data_type": "text" },
        { "column_name": "created_at", "data_type": "timestamp with time zone" },
        { "column_name": "conversion_rate_median", "data_type": "double precision" },
        { "column_name": "offer_acceptance_median", "data_type": "double precision" },
        { "column_name": "source_yield_median", "data_type": "double precision" }
      ],
      "samples": [
        { "region": "South Africa", "data_source": "synthetic", "role_family": "Senior Java Developer", "sample_size": 120, "benchmark_id": "7e44feb5-317a-428d-b70f-f8823d657302", "p25_ttf_days": 25, "p75_ttf_days": 50, "median_ttf_days": 35, "source_yield_median": 0.18, "conversion_rate_median": 0.18, "offer_acceptance_median": 0.82 },
        { "region": "Global", "data_source": "synthetic", "role_family": "Senior Java Developer", "sample_size": 500, "benchmark_id": "095e00d8-facd-4760-b92c-f8c0ada0a409", "p25_ttf_days": 20, "p75_ttf_days": 45, "median_ttf_days": 30, "source_yield_median": 0.18, "conversion_rate_median": 0.18, "offer_acceptance_median": 0.82 },
        { "region": "South Africa", "data_source": "synthetic", "role_family": "Product Manager", "sample_size": 85, "benchmark_id": "b2250513-4c63-41d4-8f0b-d3c30d433687", "p25_ttf_days": 28, "p75_ttf_days": 55, "median_ttf_days": 40, "source_yield_median": 0.18, "conversion_rate_median": 0.12, "offer_acceptance_median": 0.78 }
      ]
    },
    {
      "name": "adzuna_postings",
      "description": "Live job postings from Adzuna with salary ranges + redirect URLs.",
      "row_count": 20,
      "columns": [
        { "column_name": "posting_id", "data_type": "uuid" },
        { "column_name": "adzuna_id", "data_type": "text" },
        { "column_name": "title", "data_type": "text" },
        { "column_name": "company", "data_type": "text" },
        { "column_name": "location", "data_type": "text" },
        { "column_name": "salary_min", "data_type": "numeric" },
        { "column_name": "salary_max", "data_type": "numeric" },
        { "column_name": "posted_date", "data_type": "date" },
        { "column_name": "expired_date", "data_type": "date" },
        { "column_name": "is_repost", "data_type": "boolean" },
        { "column_name": "original_posting_id", "data_type": "uuid" },
        { "column_name": "embedding", "data_type": "USER-DEFINED" },
        { "column_name": "created_at", "data_type": "timestamp with time zone" },
        { "column_name": "redirect_url", "data_type": "text" }
      ],
      "samples": [
        { "title": "UX Designer", "location": "Johannesburg, Gauteng", "adzuna_id": "5652938653", "is_repost": false, "salary_max": 180000.0, "salary_min": 180000.0, "posted_date": "2026-03-04", "posting_id": "abfb3846-36d4-4a4c-8543-61c5e94f2d37" },
        { "title": "UX Designer", "location": "Midrand, North Johannesburg", "adzuna_id": "5699493156", "is_repost": false, "posted_date": "2026-04-15", "posting_id": "b437fefc-4d78-4ab3-9124-382cbf8c572a" },
        { "title": "Senior Specialist CX and UX Designer", "company": "Construct Executive Search", "location": "Gauteng, South Africa", "adzuna_id": "5678777075", "is_repost": false, "posted_date": "2026-03-26", "posting_id": "02dc0b4d-1fb7-4c9f-a128-d5bbca8257a4" }
      ]
    },
    {
      "name": "kaizen_sessions",
      "description": "Kaizen run history with structured output state.",
      "row_count": 24,
      "columns": [
        { "column_name": "session_id", "data_type": "uuid" },
        { "column_name": "role_id", "data_type": "uuid" },
        { "column_name": "trigger_type", "data_type": "text" },
        { "column_name": "phase", "data_type": "text" },
        { "column_name": "status", "data_type": "text" },
        { "column_name": "output_state", "data_type": "jsonb" },
        { "column_name": "dbos_workflow_id", "data_type": "text" },
        { "column_name": "created_at", "data_type": "timestamp with time zone" },
        { "column_name": "updated_at", "data_type": "timestamp with time zone" }
      ],
      "samples": [
        { "phase": "detection", "status": "failed", "session_id": "6d478b50-8d0f-43ca-83b3-746c8d4eb249", "trigger_type": "goal_review_simulation" },
        { "phase": "detection", "status": "failed", "session_id": "b570d66e-a02b-4950-8bb3-3a3ce3288034", "trigger_type": "goal_review_simulation" },
        { "phase": "detection", "status": "failed", "session_id": "7dab2c6a-f057-4b1e-a680-936e3f51c7c7", "trigger_type": "goal_review_simulation" }
      ]
    },
    {
      "name": "agent_invocations",
      "description": "Per-LLM-call cost trace with token counts.",
      "row_count": 549,
      "columns": [
        { "column_name": "invocation_id", "data_type": "uuid" },
        { "column_name": "session_id", "data_type": "uuid" },
        { "column_name": "from_agent", "data_type": "text" },
        { "column_name": "to_agent", "data_type": "text" },
        { "column_name": "tool_used", "data_type": "text" },
        { "column_name": "model_used", "data_type": "text" },
        { "column_name": "input_summary", "data_type": "text" },
        { "column_name": "output_summary", "data_type": "text" },
        { "column_name": "cost_usd", "data_type": "numeric" },
        { "column_name": "duration_ms", "data_type": "integer" },
        { "column_name": "created_at", "data_type": "timestamp with time zone" },
        { "column_name": "input_tokens", "data_type": "integer" },
        { "column_name": "output_tokens", "data_type": "integer" },
        { "column_name": "cached_tokens", "data_type": "integer" }
      ],
      "samples": [
        { "cost_usd": 0.0, "to_agent": "t3_llm", "tool_used": "llm", "from_agent": "d3_gap", "model_used": "deepseek-chat", "session_id": "6d478b50-8d0f-43ca-83b3-746c8d4eb249", "duration_ms": 3435, "input_tokens": 0, "cached_tokens": 0, "invocation_id": "d425bc9f-895f-4aed-bb53-5609c078d427", "output_tokens": 0 },
        { "cost_usd": 0.0, "to_agent": "t3_llm", "tool_used": "llm", "from_agent": "k1_define", "model_used": "deepseek-chat", "session_id": "6d478b50-8d0f-43ca-83b3-746c8d4eb249", "duration_ms": 2270, "input_tokens": 0, "cached_tokens": 0, "invocation_id": "3e8b032d-530a-4470-9722-d84604d0e3af", "output_tokens": 0 }
      ]
    },
    {
      "name": "inbound_emails",
      "description": "Queue table for the inbound CV pipeline (status: pending / processing / processed / not_cv / error).",
      "row_count": 0,
      "columns": [
        { "column_name": "id", "data_type": "uuid" },
        { "column_name": "svix_id", "data_type": "text" },
        { "column_name": "status", "data_type": "text" },
        { "column_name": "sender", "data_type": "text" },
        { "column_name": "recipient", "data_type": "text" },
        { "column_name": "subject", "data_type": "text" },
        { "column_name": "body_text", "data_type": "text" },
        { "column_name": "body_html", "data_type": "text" },
        { "column_name": "attachment_filename", "data_type": "text" },
        { "column_name": "attachment_storage_path", "data_type": "text" },
        { "column_name": "attachment_mime", "data_type": "text" },
        { "column_name": "attachment_size", "data_type": "integer" },
        { "column_name": "dedup_hash", "data_type": "text" },
        { "column_name": "is_duplicate", "data_type": "boolean" },
        { "column_name": "classified_as_cv", "data_type": "boolean" },
        { "column_name": "confidential", "data_type": "boolean" },
        { "column_name": "candidate_id", "data_type": "uuid" },
        { "column_name": "error_log", "data_type": "text" },
        { "column_name": "raw_webhook_payload", "data_type": "jsonb" },
        { "column_name": "received_at", "data_type": "timestamp with time zone" },
        { "column_name": "processed_at", "data_type": "timestamp with time zone" }
      ],
      "samples": []
    }
  ],
  "summary": {
    "corpora_count": 6,
    "tables_count": 10,
    "total_chunks": 83,
    "total_table_rows": 1288
  },
  "as_of": 1777844014
};
