-- Enable UUID generation (PostgreSQL only)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'provider', 'staff', 'patient')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE genders (
    gender_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gender_name TEXT UNIQUE NOT NULL
);
CREATE TABLE ethnicities (
    ethnicity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ethnicity_name TEXT UNIQUE NOT NULL
);
CREATE TABLE languages (
    language_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    language_name TEXT UNIQUE NOT NULL
);
CREATE TABLE specialties (
    specialty_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    specialty_name TEXT UNIQUE NOT NULL
);
CREATE TABLE patients (
    patient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dob DATE NOT NULL,
    gender_id UUID REFERENCES genders(gender_id),
    ethnicity_id UUID REFERENCES ethnicities(ethnicity_id),
    primary_language_id UUID REFERENCES languages(language_id),
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE providers (
    provider_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    npi TEXT UNIQUE NOT NULL,
    specialty_id UUID REFERENCES specialties(specialty_id),
    license_number TEXT,
    phone TEXT,
    email TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE locations (
    location_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    phone TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE clinics (
    clinic_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    location_id UUID REFERENCES locations(location_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE services (
    service_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    cpt_code TEXT UNIQUE,
    cost NUMERIC(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE appointment_statuses (
    status_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status_name TEXT UNIQUE NOT NULL
);
CREATE TABLE appointments (
    appointment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    provider_id UUID REFERENCES providers(provider_id),
    clinic_id UUID REFERENCES clinics(clinic_id),
    service_id UUID REFERENCES services(service_id),
    status_id UUID REFERENCES appointment_statuses(status_id),
    appointment_datetime TIMESTAMP NOT NULL,
    duration_minutes INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE provider_availability (
    availability_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID REFERENCES providers(provider_id),
    day_of_week TEXT CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    clinic_id UUID REFERENCES clinics(clinic_id),
    is_available BOOLEAN DEFAULT TRUE
);
CREATE TABLE clinic_resources (
    resource_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id UUID REFERENCES clinics(clinic_id),
    resource_name TEXT NOT NULL,
    resource_type TEXT NOT NULL, -- e.g., 'Room', 'Machine', 'Device'
    is_available BOOLEAN DEFAULT TRUE
);
CREATE TABLE clinic_resource_bookings (
    booking_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_id UUID REFERENCES clinic_resources(resource_id),
    appointment_id UUID REFERENCES appointments(appointment_id),
    booking_start TIMESTAMP NOT NULL,
    booking_end TIMESTAMP NOT NULL
);
CREATE TABLE provider_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID REFERENCES providers(provider_id),
    clinic_id UUID REFERENCES clinics(clinic_id),
    start_date DATE NOT NULL,
    end_date DATE,
    is_primary BOOLEAN DEFAULT FALSE
);
CREATE TABLE staff_assignments (
    staff_assignment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    clinic_id UUID REFERENCES clinics(clinic_id),
    role TEXT NOT NULL, -- e.g., 'Receptionist', 'Billing', 'Admin'
    start_date DATE NOT NULL,
    end_date DATE
);
CREATE TABLE patient_provider_links (
    link_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    provider_id UUID REFERENCES providers(provider_id),
    start_date DATE NOT NULL,
    end_date DATE
);
CREATE TABLE referral_statuses (
    status_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status_name TEXT UNIQUE NOT NULL
);
CREATE TABLE referrals (
    referral_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    referring_provider_id UUID REFERENCES providers(provider_id),
    referred_to_provider_id UUID REFERENCES providers(provider_id),
    referral_reason TEXT NOT NULL,
    status_id UUID REFERENCES referral_statuses(status_id),
    referral_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE insurance_providers (
    insurance_provider_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_name TEXT NOT NULL,
    contact_number TEXT,
    address TEXT,
    plan_type TEXT -- e.g., HMO, PPO, Medicaid
);
CREATE TABLE patient_insurance (
    patient_insurance_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    insurance_provider_id UUID REFERENCES insurance_providers(insurance_provider_id),
    policy_number TEXT NOT NULL,
    group_number TEXT,
    effective_date DATE NOT NULL,
    expiration_date DATE,
    is_primary BOOLEAN DEFAULT FALSE
);
CREATE TABLE diagnosis_codes (
    diagnosis_code TEXT PRIMARY KEY, -- e.g., 'I10' for Hypertension
    description TEXT NOT NULL,
    code_set TEXT NOT NULL -- e.g., 'ICD-10'
);
CREATE TABLE procedure_codes (
    procedure_code TEXT PRIMARY KEY, -- e.g., '99213'
    description TEXT NOT NULL,
    code_set TEXT NOT NULL -- e.g., 'CPT'
);
CREATE TABLE claims (
    claim_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_id UUID REFERENCES appointments(appointment_id),
    patient_id UUID REFERENCES patients(patient_id),
    insurance_provider_id UUID REFERENCES insurance_providers(insurance_provider_id),
    claim_date DATE NOT NULL,
    total_amount DECIMAL(10,2),
    status TEXT NOT NULL,
    submitted_at TIMESTAMP,
    paid_at TIMESTAMP
);
CREATE TABLE claim_items (
    claim_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID REFERENCES claims(claim_id),
    procedure_code TEXT REFERENCES procedure_codes(procedure_code),
    diagnosis_code TEXT REFERENCES diagnosis_codes(diagnosis_code),
    amount DECIMAL(10,2) NOT NULL,
    quantity INTEGER DEFAULT 1
);
-- Table 27: clinical_notes
CREATE TABLE clinical_notes (
    note_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    appointment_id UUID REFERENCES appointments(appointment_id),
    provider_id UUID REFERENCES providers(provider_id),
    note_type TEXT NOT NULL,
    note_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Table 28: vital_signs
CREATE TABLE vital_signs (
    vital_sign_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    appointment_id UUID REFERENCES appointments(appointment_id),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    height_cm DECIMAL(5,2),
    weight_kg DECIMAL(5,2),
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    heart_rate INTEGER,
    respiratory_rate INTEGER,
    temperature_celsius DECIMAL(4,2),
    oxygen_saturation INTEGER
);

-- Table 29: medications
CREATE TABLE medications (
    medication_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    brand_name TEXT,
    dosage_form TEXT,
    strength TEXT,
    route TEXT
);

-- Table 30: prescriptions
CREATE TABLE prescriptions (
    prescription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    provider_id UUID REFERENCES providers(provider_id),
    appointment_id UUID REFERENCES appointments(appointment_id),
    medication_id UUID REFERENCES medications(medication_id),
    dosage TEXT,
    frequency TEXT,
    duration TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    instructions TEXT,
    prescribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 31: allergies
CREATE TABLE allergies (
    allergy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    allergen TEXT NOT NULL,
    reaction TEXT,
    severity TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 32: immunizations
CREATE TABLE immunizations (
    immunization_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    vaccine_name TEXT NOT NULL,
    administered_date DATE NOT NULL,
    provider_id UUID REFERENCES providers(provider_id),
    lot_number TEXT,
    manufacturer TEXT,
    site TEXT,
    route TEXT
);

-- Table 33: billing_records
CREATE TABLE billing_records (
    billing_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    appointment_id UUID REFERENCES appointments(appointment_id),
    service_description TEXT NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    insurance_covered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 34: payments
CREATE TABLE payments (
    payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    billing_id UUID REFERENCES billing_records(billing_id),
    payment_date DATE NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    method TEXT NOT NULL CHECK (method IN ('cash', 'credit_card', 'insurance', 'other')),
    status TEXT CHECK (status IN ('paid', 'pending', 'failed')) DEFAULT 'pending'
);


-- Table 36: lab_tests
CREATE TABLE lab_tests (
    lab_test_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    appointment_id UUID REFERENCES appointments(appointment_id),
    test_name TEXT NOT NULL,
    result TEXT,
    units TEXT,
    reference_range TEXT,
    performed_date DATE NOT NULL,
    result_date DATE
);

-- Table 37: admin_settings
CREATE TABLE admin_settings (
    setting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============== Block 1: Core Entities & Lookups ==================

-- Genders
INSERT INTO genders (gender_name) VALUES ('Male'), ('Female'), ('Other');

-- Ethnicities
INSERT INTO ethnicities (ethnicity_name) VALUES ('Hispanic'), ('Non-Hispanic'), ('Asian');

-- Languages
INSERT INTO languages (language_name) VALUES ('English'), ('Spanish'), ('Tamil');

-- Specialties
INSERT INTO specialties (specialty_name) VALUES ('Cardiology'), ('General Medicine'), ('Pediatrics');

-- Users
INSERT INTO users (user_id, username, password_hash, email, role) VALUES
  (uuid_generate_v4(), 'alice_s', 'hash1', 'alice.s@example.com', 'patient'),
  (uuid_generate_v4(), 'dr_clark', 'hash2', 'emily.clark@clinic.com', 'provider'),
  (uuid_generate_v4(), 'rebecca_a', 'hash3', 'rebecca.admin@clinic.com', 'staff');

-- Locations
INSERT INTO locations (location_id, name, address, city, state, zip, phone) VALUES
  (uuid_generate_v4(), 'Main Clinic', '123 Health St', 'Coimbatore', 'Tamil Nadu', '641001', '0422-123456'),
  (uuid_generate_v4(), 'Downtown Clinic', '456 Wellness Ave', 'Coimbatore', 'Tamil Nadu', '641002', '0422-654321');

-- Patients
INSERT INTO patients (patient_id, user_id, first_name, last_name, dob, gender_id, ethnicity_id, primary_language_id, phone, email, address, city, state, zip) VALUES
  (uuid_generate_v4(), (SELECT user_id FROM users WHERE username = 'alice_s'), 'Alice', 'Smith', '1990-05-12',
   (SELECT gender_id FROM genders WHERE gender_name='Female'),
   (SELECT ethnicity_id FROM ethnicities WHERE ethnicity_name='Asian'),
   (SELECT language_id FROM languages WHERE language_name='English'),
   '9876543210', 'alice.s@example.com', '12 Rose Street', 'Coimbatore', 'TN', '641001');

-- Providers
INSERT INTO providers (provider_id, user_id, first_name, last_name, npi, specialty_id, phone, email) VALUES
  (uuid_generate_v4(), (SELECT user_id FROM users WHERE username = 'dr_clark'), 'Emily', 'Clark', '1112223334',
   (SELECT specialty_id FROM specialties WHERE specialty_name='Cardiology'), '9444444444', 'emily.clark@clinic.com');

-- Clinics
INSERT INTO clinics (clinic_id, name, location_id) VALUES
  (uuid_generate_v4(), 'Coimbatore Heart Center', (SELECT location_id FROM locations WHERE name='Main Clinic'));

-- Services
INSERT INTO services (service_id, name, description, cpt_code, cost) VALUES
  (uuid_generate_v4(), 'Cardiac Consultation', 'Initial cardiac consult', '99243', 150.00),
  (uuid_generate_v4(), 'General Checkup', 'Routine physical exam', '99214', 100.00);

-- =============== Block 2: Scheduling & Assignments ==================

-- Appointment statuses
INSERT INTO appointment_statuses (status_name) VALUES ('Scheduled'), ('Completed'), ('Cancelled');

-- Appointments
INSERT INTO appointments (appointment_id, patient_id, provider_id, clinic_id, service_id, status_id, appointment_datetime, duration_minutes) VALUES
  (uuid_generate_v4(), (SELECT patient_id FROM patients WHERE first_name='Alice'),
   (SELECT provider_id FROM providers WHERE last_name='Clark'),
   (SELECT clinic_id FROM clinics WHERE name='Coimbatore Heart Center'),
   (SELECT service_id FROM services WHERE name='Cardiac Consultation'),
   (SELECT status_id FROM appointment_statuses WHERE status_name='Scheduled'),
   '2025-07-10 09:00', 30);

-- Provider availability
INSERT INTO provider_availability (provider_id, day_of_week, start_time, end_time, clinic_id) VALUES
  ((SELECT provider_id FROM providers WHERE last_name='Clark'), 'Tuesday', '09:00', '17:00',
   (SELECT clinic_id FROM clinics WHERE name='Coimbatore Heart Center'));

-- Clinic resources
INSERT INTO clinic_resources (clinic_id, resource_name, resource_type) VALUES
  ((SELECT clinic_id FROM clinics WHERE name='Coimbatore Heart Center'), 'Exam Room 1', 'Room');

-- Resource bookings
INSERT INTO clinic_resource_bookings (resource_id, appointment_id, booking_start, booking_end) VALUES
  ((SELECT resource_id FROM clinic_resources WHERE resource_name='Exam Room 1'),
   (SELECT appointment_id FROM appointments LIMIT 1), '2025-07-10 09:00', '2025-07-10 09:30');

-- Provider assignments
INSERT INTO provider_assignments (provider_id, clinic_id, start_date, is_primary) VALUES
  ((SELECT provider_id FROM providers WHERE last_name='Clark'),
   (SELECT clinic_id FROM clinics WHERE name='Coimbatore Heart Center'), '2025-01-01', TRUE);

-- Staff assignments
INSERT INTO staff_assignments (user_id, clinic_id, role, start_date) VALUES
  ((SELECT user_id FROM users WHERE username='rebecca_a'),
   (SELECT clinic_id FROM clinics WHERE name='Coimbatore Heart Center'), 'Receptionist', '2025-06-01');

-- Patient-provider links
INSERT INTO patient_provider_links (patient_id, provider_id, start_date) VALUES
  ((SELECT patient_id FROM patients WHERE first_name='Alice'),
   (SELECT provider_id FROM providers WHERE last_name='Clark'), '2025-06-01');

-- =============== Block 3: Referrals, Insurance & Coding ==============

-- Referral statuses
INSERT INTO referral_statuses (status_name) VALUES ('Pending'), ('Approved'), ('Denied');

-- Referrals
INSERT INTO referrals (patient_id, referring_provider_id, referred_to_provider_id, referral_reason, status_id, referral_date) VALUES
  ((SELECT patient_id FROM patients WHERE first_name='Alice'),
   (SELECT provider_id FROM providers WHERE last_name='Clark'),
   (SELECT provider_id FROM providers WHERE last_name='Clark'),
   'Cardiac follow-up',
   (SELECT status_id FROM referral_statuses WHERE status_name='Pending'), '2025-07-10');

-- Insurance providers (including MediPlus)
INSERT INTO insurance_providers (provider_name, contact_number, address, plan_type) VALUES 
  ('Blue Cross Blue Shield', '800-555-1234', '123 Health St, Boston, MA 02115', 'PPO'),
  ('UnitedHealthcare', '877-555-5678', '456 Care Ave, Minneapolis, MN 55440', 'HMO'),
  ('Kaiser Permanente', '888-555-9012', '789 Wellness Blvd, Oakland, CA 94612', 'HMO'),
  ('Aetna', '855-555-3456', '101 Insurance Way, Hartford, CT 06103', 'PPO'),
  ('Medicaid', '866-555-7890', '500 Government Ln, Washington, DC 20001', 'Medicaid'),
  ('MediPlus', '888-222-3333', '321 Care Blvd, Chennai, TN 600001', 'HMO');

-- Patient insurance
INSERT INTO patient_insurance (patient_insurance_id, patient_id, insurance_provider_id, policy_number, effective_date, is_primary) VALUES
  (uuid_generate_v4(), (SELECT patient_id FROM patients WHERE first_name='Alice'),
   (SELECT insurance_provider_id FROM insurance_providers WHERE provider_name='MediPlus'), 'POL12345', '2025-01-01', TRUE);

-- Diagnosis codes
INSERT INTO diagnosis_codes (diagnosis_code, description, code_set) VALUES
  ('I10', 'Essential (primary) hypertension', 'ICD-10'),
  ('E11.9', 'Type 2 diabetes mellitus without complications', 'ICD-10'),
  ('J45.909', 'Unspecified asthma, uncomplicated', 'ICD-10'),
  ('M54.5', 'Low back pain', 'ICD-10'),
  ('F41.1', 'Generalized anxiety disorder', 'ICD-10');

-- Procedure codes
INSERT INTO procedure_codes (procedure_code, description, code_set) VALUES
  ('99243', 'Cardiac consultation', 'CPT'),
  ('93000', 'Electrocardiogram', 'CPT'),
  ('71045', 'Chest x-ray, single view', 'CPT'),
  ('36415', 'Venipuncture', 'CPT'),
  ('99395', 'Preventive medicine exam (age 18–39)', 'CPT');

-- Claims
INSERT INTO claims (claim_id, appointment_id, patient_id, insurance_provider_id, claim_date, total_amount, status, submitted_at) VALUES
  (uuid_generate_v4(),
   (SELECT appointment_id FROM appointments LIMIT 1),
   (SELECT patient_id FROM patients WHERE first_name='Alice'),
   (SELECT insurance_provider_id FROM insurance_providers WHERE provider_name='MediPlus'),
   '2025-07-11', 150.00, 'Submitted', '2025-07-11 10:00');

-- Claim items
INSERT INTO claim_items (claim_item_id, claim_id, procedure_code, diagnosis_code, amount, quantity) VALUES
  (uuid_generate_v4(), (SELECT claim_id FROM claims LIMIT 1), '99243', 'I10', 150.00, 1);

-- =============== Block 4: Clinical Notes, Medications, Immunizations ==============

-- Clinical notes
INSERT INTO clinical_notes (note_id, patient_id, appointment_id, provider_id, note_type, note_content) VALUES
  (uuid_generate_v4(), (SELECT patient_id FROM patients WHERE first_name='Alice'),
   (SELECT appointment_id FROM appointments LIMIT 1),
   (SELECT provider_id FROM providers WHERE last_name='Clark'),
   'SOAP', 'Patient is stable, follow-up in 3 months.');

-- Vital signs
INSERT INTO vital_signs (vital_sign_id, patient_id, appointment_id, height_cm, weight_kg, blood_pressure_systolic, blood_pressure_diastolic, heart_rate, temperature_celsius) VALUES
  (uuid_generate_v4(), (SELECT patient_id FROM patients WHERE first_name='Alice'),
   (SELECT appointment_id FROM appointments LIMIT 1), 165, 60, 120, 80, 72, 36.6);

-- Medications
INSERT INTO medications (medication_id, name, brand_name, dosage_form, strength, route) VALUES
  (uuid_generate_v4(), 'Atorvastatin', 'Lipitor', 'Tablet', '20mg', 'oral');

-- Prescriptions
INSERT INTO prescriptions (prescription_id, patient_id, provider_id, appointment_id, medication_id, dosage, frequency, start_date, duration, instructions) VALUES
  (uuid_generate_v4(), (SELECT patient_id FROM patients WHERE first_name='Alice'),
   (SELECT provider_id FROM providers WHERE last_name='Clark'),
   (SELECT appointment_id FROM appointments LIMIT 1),
   (SELECT medication_id FROM medications WHERE name='Atorvastatin'), '1 tablet', 'once daily', '2025-07-10', '90 days', 'Take with water.');

-- Allergies
INSERT INTO allergies (allergy_id, patient_id, allergen, reaction, severity) VALUES
  (uuid_generate_v4(), (SELECT patient_id FROM patients WHERE first_name='Alice'), 'Penicillin', 'Rash', 'Moderate');

-- Immunizations
INSERT INTO immunizations (immunization_id, patient_id, vaccine_name, administered_date, provider_id, lot_number, manufacturer, site, route) VALUES
  (uuid_generate_v4(), (SELECT patient_id FROM patients WHERE first_name='Alice'),
   'Influenza', '2024-10-01',
   (SELECT provider_id FROM providers WHERE last_name='Clark'),
   'LOT123', 'ACME Biopharma', 'left arm', 'IM');

-- =============== Block 5: Billing, Payments, Labs, Settings ==============

-- Billing
INSERT INTO billing_records (billing_id, patient_id, appointment_id, service_description, amount, insurance_covered) VALUES
  (uuid_generate_v4(), (SELECT patient_id FROM patients WHERE first_name='Alice'),
   (SELECT appointment_id FROM appointments LIMIT 1),
   'Cardiac Consultation', 150.00, TRUE);

-- Payments
INSERT INTO payments (payment_id, billing_id, payment_date, amount, method, status) VALUES
  (uuid_generate_v4(), (SELECT billing_id FROM billing_records ORDER BY billing_id DESC LIMIT 1),
   '2025-07-12', 150.00, 'insurance', 'paid');

-- Lab tests
INSERT INTO lab_tests (lab_test_id, patient_id, appointment_id, test_name, result, units, reference_range, performed_date, result_date) VALUES
  (uuid_generate_v4(), (SELECT patient_id FROM patients WHERE first_name='Alice'),
   (SELECT appointment_id FROM appointments LIMIT 1),
   'CBC', 'Normal', '', 'N/A', '2025-07-10', '2025-07-11');

-- Admin settings
INSERT INTO admin_settings (setting_id, setting_key, setting_value) VALUES
  (uuid_generate_v4(), 'max_daily_appointments', '20'),
  (uuid_generate_v4(), 'default_service_fee', '100');
