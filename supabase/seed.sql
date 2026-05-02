-- AutoCI Seed Data — NovaCo Synthetic Recruitment Dataset
-- Creates one role with deliberately bad TTF for demo purposes

-- ======================================================================
-- 1. ROLES
-- ======================================================================
INSERT INTO roles (role_id, title, department, target_ttf_days, opened_date, status)
VALUES
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Senior Java Developer', 'Engineering', 45, '2025-01-15', 'open'),
  ('b2c3d4e5-f6a7-8901-bcde-f12345678901', 'Product Manager', 'Product', 60, '2025-02-01', 'filled'),
  ('c3d4e5f6-a7b8-9012-cdef-123456789012', 'UX Designer', 'Design', 40, '2025-03-10', 'open'),
  ('d4e5f6a7-b8c9-0123-defa-234567890123', 'Data Engineer', 'Engineering', 50, '2025-04-01', 'open'),
  ('e5f6a7b8-c9d0-1234-efab-345678901234', 'DevOps Engineer', 'Engineering', 35, '2025-05-15', 'filled');

-- ======================================================================
-- 2. INTERVIEWERS
-- ======================================================================
INSERT INTO interviewers (interviewer_id, name, department, average_scheduling_lag_days)
VALUES
  ('f6a7b8c9-d0e1-2345-fabc-456789012345', 'Alice Mokoena', 'Engineering', 2.5),
  ('a7b8c9d0-e1f2-3456-abcd-567890123456', 'Bob van der Merwe', 'Engineering', 1.8),
  ('b8c9d0e1-f2a3-4567-bcde-678901234567', 'Carol Ndlovu', 'Product', 3.2),
  ('c9d0e1f2-a3b4-5678-cdef-789012345678', 'David Pretorius', 'Design', 2.0),
  ('d0e1f2a3-b4c5-6789-defa-890123456789', 'Elena Botha', 'Product', 4.1);

-- ======================================================================
-- 3. CANDIDATES (for Senior Java Developer role — deliberately slow pipeline)
-- ======================================================================
INSERT INTO candidates (candidate_id, role_id, source_channel, applied_date, external_id)
VALUES
  -- Senior Java Developer candidates (role a1b2c3d4...) — high volume, long TTF
  ('e1f2a3b4-c5d6-7890-efab-901234567890', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'LinkedIn',    '2025-02-01', 'EXT-001'),
  ('f2a3b4c5-d6e7-8901-fabc-012345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Referral',    '2025-02-10', 'EXT-002'),
  ('a3b4c5d6-e7f8-9012-abcd-123456789012', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'LinkedIn',    '2025-02-15', 'EXT-003'),
  ('b4c5d6e7-f8a9-0123-bcde-234567890123', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Direct',      '2025-03-01', 'EXT-004'),
  ('c5d6e7f8-a9b0-1234-cdef-345678901234', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'LinkedIn',    '2025-03-10', 'EXT-005'),
  ('d6e7f8a9-b0c1-2345-defa-456789012345', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Indeed',      '2025-03-20', 'EXT-006'),
  ('e7f8a9b0-c1d2-3456-efab-567890123456', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'LinkedIn',    '2025-04-01', 'EXT-007'),
  ('f8a9b0c1-d2e3-4567-fabc-678901234567', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Referral',    '2025-04-15', 'EXT-008'),
  ('a9b0c1d2-e3f4-5678-abcd-789012345678', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Indeed',      '2025-05-01', 'EXT-009'),
  ('b0c1d2e3-f4a5-6789-bcde-890123456789', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'LinkedIn',    '2025-05-10', 'EXT-010'),
  -- Product Manager candidates (role b2c3d4e5...)
  ('c1d2e3f4-a5b6-7890-cdef-901234567890', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'LinkedIn',    '2025-02-05', 'EXT-011'),
  ('d2e3f4a5-b6c7-8901-defa-012345678901', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'Referral',    '2025-02-12', 'EXT-012'),
  ('e3f4a5b6-c7d8-9012-efab-123456789012', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'Direct',      '2025-02-18', 'EXT-013'),
  ('f4a5b6c7-d8e9-0123-fabc-234567890123', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'LinkedIn',    '2025-03-01', 'EXT-014'),
  ('a5b6c7d8-e9f0-1234-abcd-345678901234', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'Indeed',      '2025-03-15', 'EXT-015'),
  -- UX Designer candidates (role c3d4e5f6...)
  ('b6c7d8e9-f0a1-2345-bcde-456789012345', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 'LinkedIn',    '2025-03-15', 'EXT-016'),
  ('c7d8e9f0-a1b2-3456-cdef-567890123456', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 'Referral',    '2025-04-01', 'EXT-017'),
  ('d8e9f0a1-b2c3-4567-defa-678901234567', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 'Direct',      '2025-04-10', 'EXT-018'),
  ('e9f0a1b2-c3d4-5678-efab-789012345678', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 'LinkedIn',    '2025-05-01', 'EXT-019'),
  ('f0a1b2c3-d4e5-6789-fabc-890123456789', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 'Indeed',      '2025-05-20', 'EXT-020');

-- ======================================================================
-- 4. PIPELINE EVENTS — Senior Java Developer (deliberately painful)
-- Slow screening, multiple interview rounds, interviewers unavailable
-- ======================================================================
INSERT INTO pipeline_events (candidate_id, stage, event_date, outcome, interviewer_id, notes)
VALUES
  -- EXT-001: Slow screening, eventually rejected at Interview 2
  ('e1f2a3b4-c5d6-7890-efab-901234567890', 'Applied',    '2025-02-01', 'Advanced',    NULL, 'Application received'),
  ('e1f2a3b4-c5d6-7890-efab-901234567890', 'Screening',  '2025-02-20', 'Advanced',    'f6a7b8c9-d0e1-2345-fabc-456789012345', 'Screening completed — 19 day lag'),
  ('e1f2a3b4-c5d6-7890-efab-901234567890', 'Interview 1','2025-03-10', 'Advanced',    'a7b8c9d0-e1f2-3456-abcd-567890123456', 'Technical interview passed'),
  ('e1f2a3b4-c5d6-7890-efab-901234567890', 'Interview 2','2025-04-05', 'Rejected',    'f6a7b8c9-d0e1-2345-fabc-456789012345', 'Cultural fit concerns'),
  -- EXT-002: Referral, still slow
  ('f2a3b4c5-d6e7-8901-fabc-012345678901', 'Applied',    '2025-02-10', 'Advanced',    NULL, 'Referral — prioritised'),
  ('f2a3b4c5-d6e7-8901-fabc-012345678901', 'Screening',  '2025-03-01', 'Advanced',    'f6a7b8c9-d0e1-2345-fabc-456789012345', 'Phone screen OK'),
  ('f2a3b4c5-d6e7-8901-fabc-012345678901', 'Interview 1','2025-03-20', 'Advanced',    'a7b8c9d0-e1f2-3456-abcd-567890123456', 'Good technical fit'),
  ('f2a3b4c5-d6e7-8901-fabc-012345678901', 'Interview 2','2025-04-15', 'Advanced',    'f6a7b8c9-d0e1-2345-fabc-456789012345', 'System design strong'),
  ('f2a3b4c5-d6e7-8901-fabc-012345678901', 'Offer',      '2025-05-05', 'Offer Extended','f6a7b8c9-d0e1-2345-fabc-456789012345', 'Offer sent'),
  -- EXT-003: LinkedIn, drops out at Interview 1
  ('a3b4c5d6-e7f8-9012-abcd-123456789012', 'Applied',    '2025-02-15', 'Advanced',    NULL, ''),
  ('a3b4c5d6-e7f8-9012-abcd-123456789012', 'Screening',  '2025-03-10', 'Advanced',    'a7b8c9d0-e1f2-3456-abcd-567890123456', ''),
  ('a3b4c5d6-e7f8-9012-abcd-123456789012', 'Interview 1','2025-04-01', 'Rejected',    'f6a7b8c9-d0e1-2345-fabc-456789012345', 'Failed coding exercise'),
  -- EXT-004: Direct — fast initial, stalls at Interview 2
  ('b4c5d6e7-f8a9-0123-bcde-234567890123', 'Applied',    '2025-03-01', 'Advanced',    NULL, 'Direct application'),
  ('b4c5d6e7-f8a9-0123-bcde-234567890123', 'Screening',  '2025-03-05', 'Advanced',    'a7b8c9d0-e1f2-3456-abcd-567890123456', 'Quick screen'),
  ('b4c5d6e7-f8a9-0123-bcde-234567890123', 'Interview 1','2025-03-15', 'Advanced',    'f6a7b8c9-d0e1-2345-fabc-456789012345', 'Strong'),
  ('b4c5d6e7-f8a9-0123-bcde-234567890123', 'Interview 2','2025-04-20', 'Advanced',    'a7b8c9d0-e1f2-3456-abcd-567890123456', 'Delayed — scheduling conflict'),
  ('b4c5d6e7-f8a9-0123-bcde-234567890123', 'Offer',      '2025-05-10', 'Offer Extended','f6a7b8c9-d0e1-2345-fabc-456789012345', 'Offer sent'),
  -- EXT-005 to EXT-010: Various stages of pipeline (2025-03 to 2025-05 applicants)
  ('c5d6e7f8-a9b0-1234-cdef-345678901234', 'Applied',    '2025-03-10', 'Advanced',    NULL, ''),
  ('c5d6e7f8-a9b0-1234-cdef-345678901234', 'Screening',  '2025-04-01', 'Rejected',    'f6a7b8c9-d0e1-2345-fabc-456789012345', 'Failed screening'),
  ('d6e7f8a9-b0c1-2345-defa-456789012345', 'Applied',    '2025-03-20', 'Advanced',    NULL, 'Indeed applicant'),
  ('d6e7f8a9-b0c1-2345-defa-456789012345', 'Screening',  '2025-04-10', 'Advanced',    'a7b8c9d0-e1f2-3456-abcd-567890123456', ''),
  ('d6e7f8a9-b0c1-2345-defa-456789012345', 'Interview 1','2025-05-05', 'Rejected',    'f6a7b8c9-d0e1-2345-fabc-456789012345', 'Technical gaps'),
  ('e7f8a9b0-c1d2-3456-efab-567890123456', 'Applied',    '2025-04-01', 'Advanced',    NULL, 'LinkedIn Premium'),
  ('e7f8a9b0-c1d2-3456-efab-567890123456', 'Screening',  '2025-04-25', 'Rejected',    'a7b8c9d0-e1f2-3456-abcd-567890123456', 'Overqualified'),
  ('f8a9b0c1-d2e3-4567-fabc-678901234567', 'Applied',    '2025-04-15', 'Advanced',    NULL, 'Referral'),
  ('f8a9b0c1-d2e3-4567-fabc-678901234567', 'Screening',  '2025-05-05', 'Advanced',    'f6a7b8c9-d0e1-2345-fabc-456789012345', ''),
  ('a9b0c1d2-e3f4-5678-abcd-789012345678', 'Applied',    '2025-05-01', 'Advanced',    NULL, 'Indeed'),
  ('b0c1d2e3-f4a5-6789-bcde-890123456789', 'Applied',    '2025-05-10', NULL,          NULL, 'Recently applied'),
  -- Product Manager pipeline (faster — filled role)
  ('c1d2e3f4-a5b6-7890-cdef-901234567890', 'Applied',    '2025-02-05', 'Advanced',    NULL, ''),
  ('c1d2e3f4-a5b6-7890-cdef-901234567890', 'Screening',  '2025-02-12', 'Advanced',    'c9d0e1f2-a3b4-5678-cdef-789012345678', 'Fast screen'),
  ('c1d2e3f4-a5b6-7890-cdef-901234567890', 'Interview 1','2025-02-20', 'Advanced',    'd0e1f2a3-b4c5-6789-defa-890123456789', 'Strong product sense'),
  ('c1d2e3f4-a5b6-7890-cdef-901234567890', 'Interview 2','2025-03-01', 'Advanced',    'b8c9d0e1-f2a3-4567-bcde-678901234567', 'Good presentation'),
  ('c1d2e3f4-a5b6-7890-cdef-901234567890', 'Offer',      '2025-03-10', 'Offer Extended','b8c9d0e1-f2a3-4567-bcde-678901234567', 'Offer sent, accepted'),
  ('d2e3f4a5-b6c7-8901-defa-012345678901', 'Applied',    '2025-02-12', 'Advanced',    NULL, 'Referral'),
  ('d2e3f4a5-b6c7-8901-defa-012345678901', 'Screening',  '2025-02-18', 'Advanced',    'c9d0e1f2-a3b4-5678-cdef-789012345678', ''),
  ('d2e3f4a5-b6c7-8901-defa-012345678901', 'Interview 1','2025-02-28', 'Rejected',    'd0e1f2a3-b4c5-6789-defa-890123456789', 'Not enough PM experience'),
  ('e3f4a5b6-c7d8-9012-efab-123456789012', 'Applied',    '2025-02-18', 'Advanced',    NULL, 'Direct'),
  ('e3f4a5b6-c7d8-9012-efab-123456789012', 'Screening',  '2025-02-25', 'Advanced',    'c9d0e1f2-a3b4-5678-cdef-789012345678', ''),
  ('e3f4a5b6-c7d8-9012-efab-123456789012', 'Interview 1','2025-03-05', 'Advanced',    'd0e1f2a3-b4c5-6789-defa-890123456789', ''),
  ('e3f4a5b6-c7d8-9012-efab-123456789012', 'Interview 2','2025-03-15', 'Advanced',    'b8c9d0e1-f2a3-4567-bcde-678901234567', ''),
  ('e3f4a5b6-c7d8-9012-efab-123456789012', 'Offer',      '2025-03-25', 'Offer Extended','b8c9d0e1-f2a3-4567-bcde-678901234567', 'Offer sent, declined'),
  ('f4a5b6c7-d8e9-0123-fabc-234567890123', 'Applied',    '2025-03-01', 'Advanced',    NULL, ''),
  ('f4a5b6c7-d8e9-0123-fabc-234567890123', 'Screening',  '2025-03-08', 'Advanced',    'c9d0e1f2-a3b4-5678-cdef-789012345678', ''),
  ('f4a5b6c7-d8e9-0123-fabc-234567890123', 'Interview 1','2025-03-18', 'Rejected',    'd0e1f2a3-b4c5-6789-defa-890123456789', 'Lacked domain knowledge'),
  ('a5b6c7d8-e9f0-1234-abcd-345678901234', 'Applied',    '2025-03-15', 'Advanced',    NULL, ''),
  ('a5b6c7d8-e9f0-1234-abcd-345678901234', 'Screening',  '2025-03-22', 'Advanced',    'c9d0e1f2-a3b4-5678-cdef-789012345678', ''),
  ('a5b6c7d8-e9f0-1234-abcd-345678901234', 'Interview 1','2025-04-01', 'Advanced',    'd0e1f2a3-b4c5-6789-defa-890123456789', ''),
  ('a5b6c7d8-e9f0-1234-abcd-345678901234', 'Interview 2','2025-04-15', 'Rejected',    'b8c9d0e1-f2a3-4567-bcde-678901234567', 'Lost to competitor'),
  -- UX Designer pipeline
  ('b6c7d8e9-f0a1-2345-bcde-456789012345', 'Applied',    '2025-03-15', 'Advanced',    NULL, ''),
  ('b6c7d8e9-f0a1-2345-bcde-456789012345', 'Screening',  '2025-03-25', 'Advanced',    'c9d0e1f2-a3b4-5678-cdef-789012345678', ''),
  ('b6c7d8e9-f0a1-2345-bcde-456789012345', 'Interview 1','2025-04-05', 'Advanced',    'c9d0e1f2-a3b4-5678-cdef-789012345678', 'Strong portfolio'),
  ('c7d8e9f0-a1b2-3456-cdef-567890123456', 'Applied',    '2025-04-01', 'Advanced',    NULL, 'Referral'),
  ('c7d8e9f0-a1b2-3456-cdef-567890123456', 'Screening',  '2025-04-10', 'Advanced',    'c9d0e1f2-a3b4-5678-cdef-789012345678', ''),
  ('c7d8e9f0-a1b2-3456-cdef-567890123456', 'Interview 1','2025-04-20', 'Rejected',    'c9d0e1f2-a3b4-5678-cdef-789012345678', 'Not a culture fit'),
  ('d8e9f0a1-b2c3-4567-defa-678901234567', 'Applied',    '2025-04-10', 'Advanced',    NULL, 'Direct'),
  ('d8e9f0a1-b2c3-4567-defa-678901234567', 'Screening',  '2025-04-18', 'Advanced',    'c9d0e1f2-a3b4-5678-cdef-789012345678', ''),
  ('e9f0a1b2-c3d4-5678-efab-789012345678', 'Applied',    '2025-05-01', 'Advanced',    NULL, ''),
  ('f0a1b2c3-d4e5-6789-fabc-890123456789', 'Applied',    '2025-05-20', NULL,          NULL, 'Recently applied, not yet screened');

-- ======================================================================
-- 5. HIRES
-- ======================================================================
INSERT INTO hires (candidate_id, role_id, offer_date, start_date, salary, accepted)
VALUES
  ('f2a3b4c5-d6e7-8901-fabc-012345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '2025-05-05', '2025-06-01', 950000, TRUE),
  ('b4c5d6e7-f8a9-0123-bcde-234567890123', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '2025-05-10', NULL,       1020000, FALSE),
  ('c1d2e3f4-a5b6-7890-cdef-901234567890', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', '2025-03-10', '2025-04-01', 850000, TRUE);

-- ======================================================================
-- 6. OFFER OUTCOMES
-- ======================================================================
INSERT INTO offer_outcomes (candidate_id, role_id, outcome, decline_reason)
VALUES
  ('f2a3b4c5-d6e7-8901-fabc-012345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Accepted', NULL),
  ('b4c5d6e7-f8a9-0123-bcde-234567890123', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Declined', 'Higher compensation offer elsewhere'),
  ('c1d2e3f4-a5b6-7890-cdef-901234567890', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'Accepted', NULL),
  ('e3f4a5b6-c7d8-9012-efab-123456789012', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'Declined', 'Accepted role at competitor');

-- ======================================================================
-- 7. KEYWORDS
-- ======================================================================
INSERT INTO keywords (keyword_id, label, category, avg_ttf_days, avg_acceptance_rate)
VALUES
  ('f0e1d2c3-b4a5-6789-0fed-cba987654321', 'Java',             'skill',     45.0, 0.65),
  ('e1d2c3b4-a5f6-7890-1fed-cba987654321', 'Senior',           'seniority', 52.0, 0.55),
  ('d2c3b4a5-f6e7-8901-2fed-cba987654321', 'Engineering',      'role_type', 40.0, 0.70),
  ('c3b4a5f6-e7d8-9012-3fed-cba987654321', 'Product Management','role_type',35.0, 0.75),
  ('b4a5f6e7-d8c9-0123-4fed-cba987654321', 'UX/UI',            'role_type', 38.0, 0.68),
  ('a5f6e7d8-c9b0-1234-5fed-cba987654321', 'Python',           'skill',     30.0, 0.72),
  ('6f7e8d9c-0b1a-2345-6fed-cba987654321', 'DevOps',           'role_type', 35.0, 0.78),
  ('7e8d9c0b-1a2f-3456-7fed-cba987654321', 'AWS',              'tool',      28.0, 0.80),
  ('8d9c0b1a-2f3e-4567-8fed-cba987654321', 'Kubernetes',       'tool',      32.0, 0.75);

-- ======================================================================
-- 8. INDUSTRY BENCHMARKS
-- ======================================================================
INSERT INTO industry_benchmarks (role_family, region, median_ttf_days, p25_ttf_days, p75_ttf_days, sample_size, data_source)
VALUES
  ('Senior Java Developer',  'South Africa', 35, 25, 50, 120, 'synthetic'),
  ('Senior Java Developer',  'Global',       30, 20, 45, 500, 'synthetic'),
  ('Product Manager',        'South Africa', 40, 28, 55, 85,  'synthetic'),
  ('Product Manager',        'Global',       35, 24, 48, 400, 'synthetic'),
  ('UX Designer',            'South Africa', 30, 20, 42, 65,  'synthetic'),
  ('UX Designer',            'Global',       28, 18, 38, 300, 'synthetic'),
  ('Data Engineer',          'South Africa', 38, 25, 52, 70,  'synthetic'),
  ('Data Engineer',          'Global',       32, 22, 45, 350, 'synthetic'),
  ('DevOps Engineer',        'South Africa', 25, 18, 35, 60,  'synthetic'),
  ('DevOps Engineer',        'Global',       22, 15, 30, 280, 'synthetic');

-- ======================================================================
-- 9. JOB DESCRIPTIONS (for RAG corpus prep)
-- ======================================================================
INSERT INTO job_descriptions (jd_id, role_id, description_text, posted_date)
VALUES
  ('9a8b7c6d-5e4f-3210-9abc-def012345678', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
   'We are looking for a Senior Java Developer to join our Engineering team. The ideal candidate has 5+ years of Java experience, strong knowledge of Spring Boot, microservices architecture, and cloud-native development. Experience with AWS, Docker, and Kubernetes is highly desirable. You will be responsible for designing and implementing scalable backend services that power our core platform.',
   '2025-01-15'),
  ('8a7b6c5d-4e3f-2109-8abc-def012345679', 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
   'We are seeking an experienced Product Manager to own the roadmap for our recruitment analytics platform. You will work closely with engineering, design, and go-to-market teams to define and deliver features that drive customer value. 4+ years of B2B SaaS product management experience required.',
   '2025-02-01'),
  ('7a6b5c4d-3e2f-1098-7abc-def012345670', 'c3d4e5f6-a7b8-9012-cdef-123456789012',
   'UX Designer needed to craft intuitive, data-rich interfaces. You will own the end-to-end design process from user research to high-fidelity prototypes. Figma proficiency required, experience with data visualisation a strong plus.',
   '2025-03-10');

-- ======================================================================
-- 10. POSTING KEYWORDS (many-to-many)
-- ======================================================================
INSERT INTO posting_keywords (posting_id, posting_type, keyword_id)
VALUES
  ('9a8b7c6d-5e4f-3210-9abc-def012345678', 'internal_jd', 'f0e1d2c3-b4a5-6789-0fed-cba987654321'),
  ('9a8b7c6d-5e4f-3210-9abc-def012345678', 'internal_jd', 'e1d2c3b4-a5f6-7890-1fed-cba987654321'),
  ('9a8b7c6d-5e4f-3210-9abc-def012345678', 'internal_jd', 'd2c3b4a5-f6e7-8901-2fed-cba987654321'),
  ('8a7b6c5d-4e3f-2109-8abc-def012345679', 'internal_jd', 'c3b4a5f6-e7d8-9012-3fed-cba987654321'),
  ('7a6b5c4d-3e2f-1098-7abc-def012345670', 'internal_jd', 'b4a5f6e7-d8c9-0123-4fed-cba987654321');
