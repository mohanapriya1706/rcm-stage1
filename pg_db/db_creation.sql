-- Step 1: Create the Database
-- You would run this command in your PostgreSQL client (e.g., pgAdmin or psql)
-- Connect to your PostgreSQL server (e.g., 'postgres' database).
-- Then run:
-- DROP DATABASE IF EXISTS rcm_ai_system;
-- CREATE DATABASE rcm_ai_system;
-- After creation, you MUST connect to 'rcm_ai_system' to run the rest of the script.
-- In pgAdmin, right-click on the new database and select 'Query Tool'.

-- Step 2: Create Tables with Schema and Constraints (REORDERED FOR DEPENDENCIES)

-- Drop tables in reverse order of new creation dependencies (for easy re-running)
-- This ensures that tables with foreign keys are dropped before the tables they reference.
DROP TABLE IF EXISTS staff_alert_queue CASCADE;
DROP TABLE IF EXISTS pa_documentation_package_tracker CASCADE;
DROP TABLE IF EXISTS pa_request_tracking CASCADE;
DROP TABLE IF EXISTS referral_status_tracker CASCADE;
DROP TABLE IF EXISTS appointment_details CASCADE;
DROP TABLE IF EXISTS patient_appointment_requests CASCADE;
DROP TABLE IF EXISTS waitlist_queue CASCADE;
DROP TABLE IF EXISTS verification_log CASCADE;
DROP TABLE IF EXISTS patient_communication_log CASCADE;
DROP TABLE IF EXISTS patient_profiles CASCADE;
DROP TABLE IF EXISTS patient_communication_preferences CASCADE;
DROP TABLE IF EXISTS patient_eligibility_details CASCADE;
DROP TABLE IF EXISTS payer_network_agreements CASCADE;
DROP TABLE IF EXISTS provider_schedules CASCADE;
DROP TABLE IF EXISTS service_cost_catalog CASCADE;
DROP TABLE IF EXISTS service_prior_authorization_rules CASCADE;
DROP TABLE IF EXISTS service_preparation_instructions_kb CASCADE;
DROP TABLE IF EXISTS historical_schedule_data CASCADE;
DROP TABLE IF EXISTS historical_denial_patterns CASCADE;

-- Knowledge Base/Rule Tables (some might reference each other, or main tables, order optimized)
DROP TABLE IF EXISTS pre_registration_question_templates CASCADE;
DROP TABLE IF EXISTS follow_up_rules_knowledge_base CASCADE;
DROP TABLE IF EXISTS help_text_explanations CASCADE;
DROP TABLE IF EXISTS resolution_strategy_kb CASCADE;
DROP TABLE IF EXISTS outreach_templates_kb CASCADE;
DROP TABLE IF EXISTS scheduling_optimization_rules_kb CASCADE;
DROP TABLE IF EXISTS payer_portal_navigation_map CASCADE;
DROP TABLE IF EXISTS edi_mapping_rules CASCADE;
DROP TABLE IF EXISTS referral_explanation_knowledge_base CASCADE;

-- Core Parent Tables (created first, as nothing directly references them via FKs yet)
CREATE TABLE patient_demographics (
    patient_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR(10),
    address TEXT,
    phone_number VARCHAR(20),
    email_address VARCHAR(255)
);

CREATE TABLE provider_details (
    provider_id SERIAL PRIMARY KEY,
    provider_name VARCHAR(255) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    npi VARCHAR(10) UNIQUE,
    tax_id VARCHAR(20),
    clinic_location_id VARCHAR(100), -- Dummy for simplicity
    contact_info VARCHAR(255),
    rating NUMERIC(2,1), -- e.g., 4.5
    pcp_designation_flag BOOLEAN DEFAULT FALSE
);

CREATE TABLE services (
    service_code VARCHAR(50) PRIMARY KEY, -- e.g., CPT code, internal service code
    service_description VARCHAR(255) NOT NULL,
    typical_cost_range VARCHAR(100) -- e.g., '$800 - $1200'
);

CREATE TABLE payer_system_access_credentials (
    payer_name VARCHAR(100) PRIMARY KEY,
    portal_url VARCHAR(255),
    edi_endpoint VARCHAR(255),
    api_key TEXT, -- Should be encrypted in a real system
    username VARCHAR(255), -- Should be encrypted
    password TEXT -- Should be encrypted
);


-- Patient-Dependent Tables (FK to patient_demographics)
CREATE TABLE patient_profiles (
    patient_id INT PRIMARY KEY,
    medical_complexity_score INT, -- e.g., 1-5
    historical_no_show_rate NUMERIC(5,2), -- e.g., 0.15 for 15%
    preferred_language VARCHAR(50),
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id) ON DELETE CASCADE
);

CREATE TABLE patient_communication_preferences (
    patient_id INT PRIMARY KEY,
    preferred_channel VARCHAR(50) NOT NULL, -- e.g., 'SMS', 'Email', 'Patient Portal'
    opt_in_status BOOLEAN DEFAULT TRUE,
    preferred_time_for_reminders TIME, -- e.g., '09:00:00'
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id) ON DELETE CASCADE
);

CREATE TABLE patient_communication_log (
    log_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    communication_type VARCHAR(50) NOT NULL, -- e.g., 'SMS Reminder', 'Chat Message', 'Email Outreach'
    message_sent TEXT NOT NULL,
    patient_response TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50), -- e.g., 'Sent', 'Delivered', 'Read', 'Replied'
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id) ON DELETE CASCADE
);

CREATE TABLE patient_eligibility_details (
    patient_id INT NOT NULL,
    payer_name VARCHAR(100) NOT NULL,
    verification_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    member_id VARCHAR(100) NOT NULL,
    group_number VARCHAR(100),
    plan_name VARCHAR(100),
    coverage_status VARCHAR(50) NOT NULL, -- 'Active', 'Inactive', 'Pending'
    effective_date DATE,
    termination_date DATE,
    deductible_amount NUMERIC(10,2),
    deductible_met_ytd NUMERIC(10,2),
    coinsurance_percentage NUMERIC(5,2),
    copay_specialist NUMERIC(10,2),
    copay_pcp NUMERIC(10,2),
    out_of_pocket_max_amount NUMERIC(10,2),
    out_of_pocket_met_ytd NUMERIC(10,2),
    referral_required_flag BOOLEAN,
    pcp_designation VARCHAR(255),
    specific_service_limitations JSONB, -- e.g., {"DME": "Limited to $500/year", "PT": "20 visits/year"}
    PRIMARY KEY (patient_id, payer_name), -- A patient has one eligibility record per payer
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id) ON DELETE CASCADE
);


-- Provider/Service/Payer Related Tables (depend on core entities)
CREATE TABLE provider_schedules (
    schedule_id SERIAL PRIMARY KEY,
    provider_id INT NOT NULL,
    date DATE NOT NULL,
    time_slot TIME NOT NULL,
    availability_status VARCHAR(50) NOT NULL, -- 'Open', 'Booked', 'Blocked'
    assigned_room_id VARCHAR(50), -- Dummy for simplicity
    appointment_type_capacity VARCHAR(100), -- e.g., 'New Patient Slot', 'Follow-up'
    CONSTRAINT fk_provider_id FOREIGN KEY (provider_id) REFERENCES provider_details(provider_id) ON DELETE CASCADE,
    UNIQUE (provider_id, date, time_slot) -- Ensure no duplicate slots for a provider
);

CREATE TABLE resource_availability (
    resource_id VARCHAR(100) PRIMARY KEY, -- e.g., 'MRI-1', 'ExamRoom-A'
    resource_type VARCHAR(100) NOT NULL, -- e.g., 'MRI Machine', 'Exam Room', 'Nurse'
    location_id VARCHAR(100), -- Dummy for simplicity
    availability_schedule JSONB, -- JSONB to store complex schedules e.g., {"2025-07-01": {"09:00-12:00": "Available"}}
    required_for_service JSONB -- JSONB list of service codes, e.g., ["CPT70551", "CPT12345"]
);

CREATE TABLE payer_network_agreements (
    agreement_id SERIAL PRIMARY KEY,
    provider_id INT NOT NULL,
    payer_name VARCHAR(100) NOT NULL,
    network_status VARCHAR(50) NOT NULL, -- 'In-Network', 'Out-of-Network'
    effective_date DATE NOT NULL,
    termination_date DATE,
    CONSTRAINT fk_provider_id FOREIGN KEY (provider_id) REFERENCES provider_details(provider_id) ON DELETE CASCADE,
    UNIQUE (provider_id, payer_name) -- A provider has one agreement status per payer
);

CREATE TABLE service_cost_catalog (
    catalog_id SERIAL PRIMARY KEY,
    service_code VARCHAR(50) NOT NULL,
    payer_name VARCHAR(100) NOT NULL,
    provider_id INT, -- Optional, for provider-specific rates
    negotiated_rate NUMERIC(10,2) NOT NULL,
    allowed_amount_range VARCHAR(100), -- e.g., '$900 - $1100'
    CONSTRAINT fk_service_code FOREIGN KEY (service_code) REFERENCES services(service_code) ON DELETE CASCADE,
    CONSTRAINT fk_provider_id FOREIGN KEY (provider_id) REFERENCES provider_details(provider_id)
);

CREATE TABLE service_prior_authorization_rules (
    rule_id SERIAL PRIMARY KEY,
    payer_name VARCHAR(100) NOT NULL,
    service_code VARCHAR(50) NOT NULL,
    prior_authorization_required BOOLEAN NOT NULL,
    referral_required BOOLEAN,
    required_documentation_list JSONB, -- e.g., ["Physician Progress Notes", "Imaging Reports"]
    keywords_for_medical_necessity JSONB, -- e.g., ["failed conservative therapy", "pain level >= 7"]
    payer_portal_url VARCHAR(255),
    payer_auth_phone VARCHAR(20),
    CONSTRAINT fk_service_code FOREIGN KEY (service_code) REFERENCES services(service_code) ON DELETE CASCADE,
    UNIQUE (payer_name, service_code) -- One rule per payer-service combo
);

CREATE TABLE service_preparation_instructions_kb (
    instruction_id SERIAL PRIMARY KEY,
    service_type_code VARCHAR(50) NOT NULL,
    instruction_category VARCHAR(100) NOT NULL, -- 'Dietary', 'Medication', 'Arrival'
    instruction_text TEXT NOT NULL,
    fasting_required BOOLEAN,
    common_patient_questions JSONB, -- e.g., ["Can I drink coffee?", "Can I wear my watch?"]
    common_patient_answers JSONB, -- Corresponding answers
    CONSTRAINT fk_service_type_code FOREIGN KEY (service_type_code) REFERENCES services(service_code) ON DELETE CASCADE
);


-- Intermediate Tables (depend on Patients, Providers, Services)
CREATE TABLE patient_appointment_requests (
    request_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    requested_service_type VARCHAR(255) NOT NULL, -- Could be a service code or description
    requested_provider_id INT,
    requested_date_range TEXT, -- e.g., '2025-07-01 to 2025-07-15'
    requested_time_range TEXT, -- e.g., 'After 4 PM'
    urgency_score INT, -- e.g., 1-5
    timestamp_added TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id) ON DELETE CASCADE,
    CONSTRAINT fk_requested_provider_id FOREIGN KEY (requested_provider_id) REFERENCES provider_details(provider_id)
);

CREATE TABLE waitlist_queue (
    waitlist_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    desired_provider_id INT,
    desired_date_range TEXT,
    desired_time_range TEXT,
    service_type VARCHAR(255) NOT NULL,
    timestamp_added TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Active', -- e.g., 'Active', 'Fulfilled', 'Expired'
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id) ON DELETE CASCADE,
    CONSTRAINT fk_desired_provider_id FOREIGN KEY (desired_provider_id) REFERENCES provider_details(provider_id)
);

CREATE TABLE appointment_details (
    appointment_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    provider_id INT NOT NULL,
    service_code VARCHAR(50) NOT NULL,
    payer_name VARCHAR(100) NOT NULL,
    appointment_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    clinic_address TEXT,
    appointment_status VARCHAR(50) NOT NULL, -- 'Scheduled', 'Canceled', 'Completed'
    reminder_status VARCHAR(50), -- e.g., 'Sent 24hr', 'Confirmed'
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id) ON DELETE CASCADE,
    CONSTRAINT fk_provider_id FOREIGN KEY (provider_id) REFERENCES provider_details(provider_id),
    CONSTRAINT fk_service_code FOREIGN KEY (service_code) REFERENCES services(service_code)
);

CREATE TABLE historical_schedule_data (
    past_appointment_id INT PRIMARY KEY, -- Linking to a historical appointment in a real EHR
    provider_id INT NOT NULL,
    service_code VARCHAR(50) NOT NULL,
    patient_complexity INT,
    actual_duration_minutes INT,
    no_show_flag BOOLEAN,
    patient_satisfaction_score NUMERIC(2,1),
    appointment_date_time TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_provider_id FOREIGN KEY (provider_id) REFERENCES provider_details(provider_id),
    CONSTRAINT fk_service_code FOREIGN KEY (service_code) REFERENCES services(service_code)
);

CREATE TABLE referral_status_tracker (
    referral_id VARCHAR(100) PRIMARY KEY, -- e.g., 'REF-PAT123-PROV456'
    patient_id INT NOT NULL,
    referring_provider_id INT,
    referred_to_provider_id INT,
    payer_name VARCHAR(100),
    service_type VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- 'Pending Request', 'Sent to Payer', 'Approved', 'Denied'
    approval_expiration_date DATE,
    last_update_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id) ON DELETE CASCADE,
    CONSTRAINT fk_referring_provider FOREIGN KEY (referring_provider_id) REFERENCES provider_details(provider_id),
    CONSTRAINT fk_referred_to_provider FOREIGN KEY (referred_to_provider_id) REFERENCES provider_details(provider_id)
);

CREATE TABLE verification_log (
    verification_log_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    payer_name VARCHAR(100) NOT NULL,
    verification_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- 'Success', 'Failed', 'Partial'
    method_used VARCHAR(50), -- 'API', 'RPA', 'EDI'
    error_message TEXT,
    raw_response_data TEXT, -- Or JSONB for structured responses
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id) ON DELETE CASCADE
);


-- Knowledge Base Tables (Internal References & Cross-References)
CREATE TABLE help_text_explanations (
    help_text_id VARCHAR(100) PRIMARY KEY,
    term VARCHAR(255) NOT NULL,
    explanation_text TEXT NOT NULL,
    example_usage TEXT
);

CREATE TABLE follow_up_rules_knowledge_base (
    rule_id VARCHAR(100) PRIMARY KEY,
    trigger_question_id VARCHAR(100) NOT NULL,
    trigger_answer TEXT NOT NULL,
    next_question_ids JSONB NOT NULL -- JSONB array of question_id strings
);

CREATE TABLE pre_registration_question_templates (
    question_id VARCHAR(100) PRIMARY KEY, -- e.g., 'Q_FULL_NAME', 'Q_ALLERGIES'
    question_text TEXT NOT NULL,
    expected_answer_type VARCHAR(50) NOT NULL, -- 'Text', 'Date', 'Boolean', 'Dropdown_List'
    follow_up_logic_id VARCHAR(100), -- FK to follow_up_rules_knowledge_base
    help_text_id VARCHAR(100), -- FK to help_text_explanations
    category VARCHAR(100), -- 'Demographics', 'Medical History'
    order_index INT,
    CONSTRAINT fk_follow_up_logic FOREIGN KEY (follow_up_logic_id) REFERENCES follow_up_rules_knowledge_base(rule_id),
    CONSTRAINT fk_help_text FOREIGN KEY (help_text_id) REFERENCES help_text_explanations(help_text_id)
);

CREATE TABLE referral_explanation_knowledge_base (
    concept VARCHAR(100) PRIMARY KEY, -- e.g., 'Referral'
    explanation TEXT NOT NULL,
    how_to_get_it TEXT,
    consequences_of_missing TEXT
);

CREATE TABLE resolution_strategy_kb (
    strategy_id VARCHAR(100) PRIMARY KEY,
    strategy_description TEXT NOT NULL,
    responsible_role VARCHAR(100) -- 'Scheduling Staff', 'Auth Specialist'
);

CREATE TABLE historical_denial_patterns (
    pattern_id SERIAL PRIMARY KEY,
    payer_name VARCHAR(100) NOT NULL,
    service_code VARCHAR(50) NOT NULL,
    denial_reason_code VARCHAR(100) NOT NULL,
    contributing_factor VARCHAR(255),
    denial_frequency_score NUMERIC(5,2), -- e.g., 0.75 for 75%
    resolution_strategy_id VARCHAR(100), -- FK to resolution_strategy_kb
    CONSTRAINT fk_service_code FOREIGN KEY (service_code) REFERENCES services(service_code),
    CONSTRAINT fk_resolution_strategy FOREIGN KEY (resolution_strategy_id) REFERENCES resolution_strategy_kb(strategy_id)
);

CREATE TABLE outreach_templates_kb (
    template_id VARCHAR(100) PRIMARY KEY,
    missing_info_field VARCHAR(100), -- e.g., 'Policy Number', 'DOB'
    channel VARCHAR(50) NOT NULL, -- 'SMS', 'Email', 'Patient Portal'
    template_text TEXT NOT NULL, -- Use placeholders like [Patient Name], [Missing_Info_Field]
    secure_submission_method_text TEXT
);

CREATE TABLE scheduling_optimization_rules_kb (
    rule_id SERIAL PRIMARY KEY,
    optimization_goal VARCHAR(100), -- e.g., 'Minimize Wait Times', 'Maximize Provider Utilization'
    constraint_type VARCHAR(100), -- e.g., 'No complex cases after X PM'
    constraint_value TEXT,
    provider_specific_preference JSONB, -- e.g., {"Dr. Smith": {"afternoon": "fast_followups"}}
    patient_type_preference JSONB -- e.g., {"new_patient_slots": "morning"}
);

CREATE TABLE payer_portal_navigation_map (
    payer_name VARCHAR(100) PRIMARY KEY,
    login_url VARCHAR(255),
    login_elements_json JSONB, -- JSON describing elements (xpath, id, name) for username/password
    eligibility_search_elements_json JSONB, -- JSON describing search form elements
    data_extraction_elements_json JSONB -- JSON describing elements to scrape for eligibility/benefits
);

CREATE TABLE edi_mapping_rules (
    edi_type VARCHAR(50) PRIMARY KEY, -- e.g., '270_Request', '271_Response'
    segment_mapping_json JSONB, -- JSON defining how to map internal data to EDI segments/elements
    parsing_rules_json JSONB -- JSON defining how to parse incoming EDI segments to internal format
);

-- Final Operational/Tracking Tables (depend on many others, including KBs and appointments)
CREATE TABLE pa_request_tracking (
    pa_request_id VARCHAR(100) PRIMARY KEY, -- Unique ID, can be generated like 'PA-12345'
    appointment_id INT,
    patient_id INT NOT NULL,
    provider_id INT NOT NULL,
    service_code VARCHAR(50) NOT NULL,
    payer_name VARCHAR(100) NOT NULL,
    initiation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    submission_method VARCHAR(50), -- 'Electronic', 'Fax', 'Phone'
    current_status VARCHAR(50) NOT NULL, -- 'Initiated', 'Submitted', 'Pending Review', 'Approved', 'Denied', 'Requires More Info'
    payer_auth_number VARCHAR(100),
    denial_reason_code VARCHAR(100),
    next_action_timestamp TIMESTAMP WITH TIME ZONE,
    alert_staff_flag BOOLEAN DEFAULT FALSE,
    staff_alert_reason TEXT,
    CONSTRAINT fk_appointment_id FOREIGN KEY (appointment_id) REFERENCES appointment_details(appointment_id) ON DELETE SET NULL,
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id),
    CONSTRAINT fk_provider_id FOREIGN KEY (provider_id) REFERENCES provider_details(provider_id),
    CONSTRAINT fk_service_code FOREIGN KEY (service_code) REFERENCES services(service_code)
);

CREATE TABLE pa_documentation_package_tracker (
    document_package_id SERIAL PRIMARY KEY,
    pa_request_id VARCHAR(100) NOT NULL,
    patient_id INT NOT NULL,
    service_code VARCHAR(50) NOT NULL,
    payer_name VARCHAR(100) NOT NULL,
    ai_summarized_rationale TEXT,
    extracted_document_ids JSONB, -- List of conceptual EHR Document IDs
    flagged_keywords_found JSONB, -- List of keywords/phrases extracted
    status VARCHAR(50) DEFAULT 'Draft', -- 'Draft', 'Ready for Review', 'Submitted'
    review_required_flag BOOLEAN DEFAULT TRUE,
    reviewer_comments TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pa_request_id FOREIGN KEY (pa_request_id) REFERENCES pa_request_tracking(pa_request_id) ON DELETE CASCADE,
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id),
    CONSTRAINT fk_service_code FOREIGN KEY (service_code) REFERENCES services(service_code)
);

CREATE TABLE staff_alert_queue (
    alert_id SERIAL PRIMARY KEY,
    appointment_id INT,
    patient_id INT NOT NULL,
    alert_type VARCHAR(100) NOT NULL, -- 'Denial Risk', 'PA Needs Review', 'Missing Info'
    risk_level VARCHAR(50), -- 'High', 'Medium', 'Low'
    predicted_reason TEXT,
    recommended_action TEXT,
    responsible_staff_role VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'New', -- 'New', 'Acknowledged', 'Resolved'
    CONSTRAINT fk_appointment_id FOREIGN KEY (appointment_id) REFERENCES appointment_details(appointment_id) ON DELETE SET NULL,
    CONSTRAINT fk_patient_id FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id)
);


-- End of CREATE TABLE statements


---
--- Step 3: Insert Dummy Data
--- Ensure order of insertion respects foreign key constraints
---
INSERT INTO patient_demographics (patient_id, full_name, dob, gender, address, phone_number, email_address) VALUES
(101, 'John Doe', '1985-03-15', 'Male', '123 Main St, Anytown, USA', '555-123-4567', 'john.doe@example.com'),
(102, 'Jane Smith', '1992-07-22', 'Female', '456 Oak Ave, Anytown, USA', '555-987-6543', 'jane.smith@example.com'),
(103, 'Alice Brown', '1970-11-01', 'Female', '789 Pine Ln, Otherville, USA', '555-555-1212', 'alice.brown@example.com');

INSERT INTO patient_profiles (patient_id, medical_complexity_score, historical_no_show_rate, preferred_language) VALUES
(101, 3, 0.10, 'English'),
(102, 2, 0.05, 'English'),
(103, 4, 0.20, 'English');

INSERT INTO patient_communication_preferences (patient_id, preferred_channel, opt_in_status, preferred_time_for_reminders) VALUES
(101, 'SMS', TRUE, '09:00:00'),
(102, 'Email', TRUE, '10:00:00'),
(103, 'SMS', TRUE, '14:00:00');

-- Provider & Resource-Related Data
INSERT INTO provider_details (provider_id, provider_name, specialty, npi, tax_id, clinic_location_id, contact_info, rating, pcp_designation_flag) VALUES
(201, 'Dr. Alice Brown', 'Dermatology', '1234567890', 'TAX123', 'Clinic A', '555-111-2222', 4.8, FALSE),
(202, 'Dr. Bob White', 'Cardiology', '0987654321', 'TAX456', 'Clinic B', '555-333-4444', 4.5, FALSE),
(203, 'Dr. Carol Green', 'Internal Medicine', '1122334455', 'TAX789', 'Clinic A', '555-666-7777', 4.7, TRUE);

INSERT INTO provider_schedules (provider_id, date, time_slot, availability_status, assigned_room_id, appointment_type_capacity) VALUES
(201, '2025-07-01', '10:00:00', 'Open', 'Room 1', 'New Patient Slot'),
(201, '2025-07-01', '10:30:00', 'Booked', 'Room 1', 'Follow-up'),
(201, '2025-07-01', '11:00:00', 'Open', 'Room 1', 'Follow-up'),
(201, '2025-07-01', '16:00:00', 'Open', 'Room 1', 'New Patient Slot'), -- For "after 4 PM"
(201, '2025-07-02', '16:30:00', 'Open', 'Room 1', 'Follow-up'), -- For alternative suggestions
(202, '2025-07-05', '09:00:00', 'Open', 'Room 2', 'New Patient Slot'),
(203, '2025-07-03', '09:00:00', 'Open', 'Room 3', 'PCP Visit');

INSERT INTO resource_availability (resource_id, resource_type, location_id, availability_schedule, required_for_service) VALUES
('MRI-Unit-A', 'MRI Machine', 'Imaging Center', '{"2025-07-01": {"09:00-17:00": "Available"}}'::jsonb, '["CPT70551", "CPT72148"]'::jsonb),
('ExamRoom-1', 'Exam Room', 'Clinic A', '{"2025-07-01": {"08:00-17:00": "Available"}}'::jsonb, '[]'::jsonb);

-- Payer & Insurance-Related Data
INSERT INTO payer_network_agreements (provider_id, payer_name, network_status, effective_date) VALUES
(201, 'Aetna PPO', 'In-Network', '2020-01-01'),
(201, 'Blue Cross Basic', 'In-Network', '2019-06-01'),
(202, 'Aetna PPO', 'In-Network', '2021-03-01'),
(202, 'Blue Cross Basic', 'Out-of-Network', '2021-03-01'), -- Dr White not in-network for BCBS
(203, 'Aetna PPO', 'In-Network', '2018-01-01'),
(203, 'Blue Cross Basic', 'In-Network', '2018-01-01');

INSERT INTO patient_eligibility_details (patient_id, payer_name, member_id, group_number, plan_name, coverage_status, effective_date, deductible_amount, deductible_met_ytd, coinsurance_percentage, copay_specialist, copay_pcp, out_of_pocket_max_amount, out_of_pocket_met_ytd, referral_required_flag, specific_service_limitations) VALUES
(101, 'Aetna PPO', 'AETNA12345', 'GRP-AET', 'Aetna Gold', 'Active', '2024-01-01', 1000.00, 200.00, 20.00, 40.00, 20.00, 5000.00, 250.00, FALSE, '{"DME": "Limited to $500/year"}'::jsonb),
(102, 'Blue Cross Basic', 'BCBS67890', 'GRP-BCBS', 'BCBS Silver', 'Active', '2024-01-01', 1500.00, 800.00, 30.00, 50.00, 30.00, 7500.00, 1000.00, TRUE, '{"MRI": "Requires prior auth"}'::jsonb),
(103, 'Aetna PPO', 'AETNA54321', 'GRP-AET', 'Aetna Gold', 'Active', '2024-01-01', 1000.00, 1000.00, 20.00, 40.00, 20.00, 5000.00, 4500.00, FALSE, '{}'::jsonb); -- Deductible met, close to OOP max

INSERT INTO payer_system_access_credentials (payer_name, portal_url, edi_endpoint, api_key, username, password) VALUES
('Aetna PPO', 'https://www.aetna.com/provider', 'edi.aetna.com/270', 'aetna_api_key_xyz', 'aetna_user', 'secure_aet_pass'),
('Blue Cross Basic', 'https://www.bcbs.com/provider', NULL, NULL, 'bcbs_user', 'secure_bcbs_pass'); -- Simulate no direct API for BCBS

-- Service & Clinical Data
INSERT INTO services (service_code, service_description, typical_cost_range) VALUES
('CPT70551', 'MRI Brain without contrast', '$800 - $1200'),
('CPT99203', 'Dermatology Consult - New Patient', '$150 - $250'),
('CPT99213', 'Cardiology Consult - Follow-up', '$100 - $200');

INSERT INTO service_cost_catalog (service_code, payer_name, provider_id, negotiated_rate) VALUES
('CPT70551', 'Aetna PPO', 201, 950.00), -- Dr. Brown (Derm) uses this, Payer rate
('CPT70551', 'Blue Cross Basic', NULL, 1100.00), -- General BCBS rate for MRI
('CPT99203', 'Aetna PPO', 201, 180.00); -- Dr. Brown (Derm) consult with Aetna

INSERT INTO service_prior_authorization_rules (payer_name, service_code, prior_authorization_required, referral_required, required_documentation_list, keywords_for_medical_necessity) VALUES
('Aetna PPO', 'CPT70551', TRUE, FALSE, '["Physician Progress Notes", "Imaging Reports"]'::jsonb, '["failed conservative therapy", "neurological deficits"]'::jsonb),
('Blue Cross Basic', 'CPT70551', TRUE, TRUE, '["PCP Referral", "Specialist Notes", "Imaging Reports"]'::jsonb, '["persistent symptoms", "diagnostic clarity"]'::jsonb),
('Aetna PPO', 'CPT99203', FALSE, FALSE, '[]'::jsonb, '[]'::jsonb),
('Blue Cross Basic', 'CPT99203', FALSE, FALSE, '[]'::jsonb, '[]'::jsonb),
('Blue Cross Basic', 'CPT99213', FALSE, TRUE, '["PCP Referral"]'::jsonb, '[]'::jsonb);

INSERT INTO service_preparation_instructions_kb (service_type_code, instruction_category, instruction_text, fasting_required, common_patient_questions, common_patient_answers) VALUES
('CPT70551', 'Arrival', 'Please arrive 15 minutes early and wear comfortable clothing. Do not wear any metal items.', FALSE, '["Can I drink coffee?", "Can I wear my watch?"]'::jsonb, '["Yes, coffee is fine as fasting is not required.", "No, please remove all metal, including watches."]'::jsonb),
('CPT99203', 'General', 'No specific preparation needed. You may bring a list of your medications and any questions.', FALSE, '[]'::jsonb, '[]'::jsonb);

-- Intermediate Tables (depend on Patients, Providers, Services)
INSERT INTO patient_appointment_requests (patient_id, requested_service_type, requested_provider_id, requested_date_range, requested_time_range, urgency_score) VALUES
(101, 'Dermatology Consult', 201, '2025-07-01 to 2025-07-15', 'After 4 PM', 3);

INSERT INTO waitlist_queue (patient_id, desired_provider_id, desired_date_range, desired_time_range, service_type) VALUES
(101, 201, '2025-07-01', '10:00:00', 'Dermatology Consult');

INSERT INTO appointment_details (patient_id, provider_id, service_code, payer_name, appointment_date_time, clinic_address, appointment_status, reminder_status) VALUES
(101, 201, 'CPT99203', 'Aetna PPO', '2025-07-01 16:00:00+05:30', '123 Main St, Anytown', 'Scheduled', 'None'), -- John Doe, Dr. Brown, Derm Consult
(102, 202, 'CPT99213', 'Blue Cross Basic', '2025-07-05 09:00:00+05:30', '456 Oak Ave, Anytown', 'Scheduled', 'None'), -- Jane Smith, Dr. White, Cardio Consult - note: Dr White out-of-network for BCBS
(103, 201, 'CPT70551', 'Aetna PPO', '2025-07-10 10:00:00+05:30', 'Imaging Center, Otherville', 'Scheduled', 'None'); -- Alice Brown, Dr. Brown, MRI Brain

INSERT INTO historical_schedule_data (past_appointment_id, provider_id, service_code, patient_complexity, actual_duration_minutes, no_show_flag, patient_satisfaction_score, appointment_date_time) VALUES
(1, 201, 'CPT99203', 2, 30, FALSE, 4.5, '2025-06-10 10:00:00+05:30'),
(2, 201, 'CPT99203', 1, 15, FALSE, 4.8, '2025-06-10 10:30:00+05:30'),
(3, 202, 'CPT99213', 3, 45, TRUE, 3.0, '2025-06-12 11:00:00+05:30');

INSERT INTO referral_status_tracker (referral_id, patient_id, referring_provider_id, referred_to_provider_id, payer_name, service_type, status) VALUES
('REF-JS102-BW202', 102, 203, 202, 'Blue Cross Basic', 'Cardiology Consult', 'Pending Request');

INSERT INTO verification_log (patient_id, payer_name, status, method_used, error_message) VALUES
(101, 'Aetna PPO', 'Failed', 'API', 'Missing Member ID in query.');


-- Rules & Historical Data (Knowledge Bases) - REORDERED INSERTS
-- Insert parent KBs first
INSERT INTO help_text_explanations (help_text_id, term, explanation_text, example_usage) VALUES
('HELP_GUARANTOR', 'Guarantor', 'A guarantor is the person responsible for paying the medical bill. This is often the patient themselves, or a parent for a minor.', 'Example: If you are an adult paying for your own care, you are the guarantor.');

INSERT INTO follow_up_rules_knowledge_base (rule_id, trigger_question_id, trigger_answer, next_question_ids) VALUES
('RULE_ALLERGIES_FOLLOWUP', 'Q_ALLERGIES_YN', 'true', '["Q_LIST_ALLERGIES"]'::jsonb),
('RULE_GUARANTOR_FOLLOWUP', 'Q_GUARANTOR_YN', 'true', '["Q_GUARANTOR_NAME"]'::jsonb);

INSERT INTO resolution_strategy_kb (strategy_id, strategy_description, responsible_role) VALUES
('STRAT_VERIFY_REFERRAL', 'Verify PCP referral status and obtain if missing.', 'Scheduling Staff'),
('STRAT_ADD_CLINICAL_NOTES', 'Upload additional clinical notes to payer portal to justify medical necessity.', 'Auth Specialist');

-- Now insert KBs that reference the above
INSERT INTO pre_registration_question_templates (question_id, question_text, expected_answer_type, follow_up_logic_id, help_text_id, category, order_index) VALUES
('Q_FULL_NAME', 'What is your full legal name?', 'Text', NULL, NULL, 'Demographics', 1),
('Q_DOB', 'What is your date of birth? (MM/DD/YYYY)', 'Date', NULL, NULL, 'Demographics', 2),
('Q_ALLERGIES_YN', 'Do you have any known allergies?', 'Boolean', 'RULE_ALLERGIES_FOLLOWUP', NULL, 'Medical History', 3),
('Q_LIST_ALLERGIES', 'Please list your allergies and typical reaction.', 'Text', NULL, NULL, 'Medical History', 4),
('Q_GUARANTOR_YN', 'Is there someone else financially responsible for your medical bills (guarantor)?', 'Boolean', 'RULE_GUARANTOR_FOLLOWUP', 'HELP_GUARANTOR', 'Financial', 5),
('Q_GUARANTOR_NAME', 'Please provide the full name of the guarantor.', 'Text', NULL, NULL, 'Financial', 6);

INSERT INTO historical_denial_patterns (payer_name, service_code, denial_reason_code, contributing_factor, denial_frequency_score, resolution_strategy_id) VALUES
('Blue Cross Basic', 'CPT99213', 'Missing Referral', 'PCP Not On File', 0.85, 'STRAT_VERIFY_REFERRAL'),
('Aetna PPO', 'CPT70551', 'Lack of Medical Necessity', 'Insufficient Documentation', 0.70, 'STRAT_ADD_CLINICAL_NOTES');

INSERT INTO outreach_templates_kb (template_id, missing_info_field, channel, template_text, secure_submission_method_text) VALUES
('TEMPLATE_SMS_POLICY', 'Policy Number', 'SMS', 'Hi [Patient Name], this is [Clinic Name]. We need your [Missing_Info_Field] for your [Payer_Name] insurance. Please reply or visit [Secure Portal URL].', 'securely via our patient portal at [Secure Portal URL]'),
('TEMPLATE_EMAIL_DOB', 'DOB', 'Email', 'Dear [Patient Name], we need to confirm your [Missing_Info_Field] for your records. Please provide it via [Secure Portal URL] or call us.', 'secure patient portal at [Secure Portal URL]');

INSERT INTO scheduling_optimization_rules_kb (optimization_goal, constraint_type, constraint_value, provider_specific_preference, patient_type_preference) VALUES
('Maximize Provider Utilization', 'Fill Cancellations', NULL, '{"201": {"afternoon": "fast_followups"}}'::jsonb, '{"low_no_show_risk": "priority_fill"}'::jsonb),
('Balance Complexity', 'No complex cases after 3 PM', NULL, '{"201": {"complex_cases_only": "morning"}}'::jsonb, '{"high_complexity": "morning_only"}'::jsonb);

INSERT INTO payer_portal_navigation_map (payer_name, login_url, login_elements_json, eligibility_search_elements_json, data_extraction_elements_json) VALUES
('Blue Cross Basic', 'https://www.bcbs.com/provider/login',
    '{"username_field": {"type": "id", "value": "username"}, "password_field": {"type": "id", "value": "password"}, "login_button": {"type": "id", "value": "loginBtn"}}'::jsonb,
    '{"member_id_field": {"type": "name", "value": "memberId"}, "dob_field": {"type": "name", "value": "dob"}, "search_button": {"type": "id", "value": "searchBtn"}}'::jsonb,
    '{"coverage_status": {"type": "xpath", "value": "//div[@id=''coverageStatus'']"}, "deductible_met": {"type": "xpath", "value": "//span[@class=''deductibleMet'']"}}'::jsonb);

INSERT INTO edi_mapping_rules (edi_type, segment_mapping_json, parsing_rules_json) VALUES
('270_Request', '{"patient_name": "NM1*IL*1", "member_id": "REF*0F"}'::jsonb, '{}'::jsonb),
('271_Response', '{}'::jsonb, '{"coverage_status": "EB*1*3", "deductible_amount": "AMT*D"}'::jsonb);

INSERT INTO referral_explanation_knowledge_base (concept, explanation, how_to_get_it, consequences_of_missing) VALUES
('Referral', 'A referral is a written recommendation from your Primary Care Provider (PCP) to see a specialist. Your insurance plan may require it for coverage.', 'Contact your PCP''s office and request a referral to the specialist you plan to see. Provide them with the specialist''s name and specialty.', 'Without a required referral, your insurance may not cover the visit, leading to higher out-of-pocket costs or a denied claim.');


-- Final Operational/Tracking Tables (depend on many others, including KBs and appointments)
INSERT INTO pa_request_tracking (pa_request_id, appointment_id, patient_id, provider_id, service_code, payer_name, current_status, alert_staff_flag, staff_alert_reason) VALUES
('PA-AB103-MRI', 3, 103, 201, 'CPT70551', 'Aetna PPO', 'Initiated', FALSE, NULL);

INSERT INTO pa_documentation_package_tracker (pa_request_id, patient_id, service_code, payer_name, ai_summarized_rationale, extracted_document_ids, flagged_keywords_found, status) VALUES
('PA-AB103-MRI', 103, 'CPT70551', 'Aetna PPO', 'Patient presents with persistent headaches and neurological symptoms. MRI indicated to rule out intracranial pathology. Failed prior conservative management.', '["EHR-DOC-001", "EHR-DOC-002"]'::jsonb, '["persistent headaches", "neurological deficits", "failed conservative therapy"]'::jsonb, 'Ready for Review');

INSERT INTO staff_alert_queue (patient_id, alert_type, risk_level, predicted_reason, recommended_action, responsible_staff_role, appointment_id) VALUES
(102, 'Denial Risk', 'High', 'Missing Referral for Specialist Visit (BCBS Basic requires referrals). Provider is Out-of-Network for BCBS.', 'Verify referral status with PCP and inform patient about OON risk.', 'Auth Specialist', 2); -- Alert for Jane Smith's appointment