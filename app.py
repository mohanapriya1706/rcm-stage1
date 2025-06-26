import streamlit as st
import json
from datetime import date, time, datetime
import os
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from typing import Optional, Literal

# --- Pydantic Models for Form Validation (remain unchanged) ---

class PatientDemographics(BaseModel):
    full_legal_name: str = Field(..., min_length=2, max_length=100, description="Patient's full legal name")
    date_of_birth: date = Field(..., description="Patient's date of birth")
    gender: Literal["Male", "Female", "Non-binary", "Prefer not to say"] = Field(..., description="Patient's gender, e.g., Male, Female, Non-binary")
    address: str = Field("", description="Patient's current address")
    phone_number: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$", description="Patient's 10-digit phone number")
    email_address: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", description="Patient's email address")
    preferred_language: str = Field("English", description="Patient's preferred language")

    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v: date):
        if v > date.today():
            raise ValueError('Date of birth cannot be in the future.')
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        MIN_AGE_FOR_CONSENT = 18
        if age < MIN_AGE_FOR_CONSENT:
            raise ValueError(f'Patient must be at least {MIN_AGE_FOR_CONSENT} years old to proceed with this form directly. Parental/Guardian consent may be required.')
        return v

class EmergencyContact(BaseModel):
    name: Optional[str] = Field(None, description="Emergency contact's name")
    relationship: Optional[str] = Field(None, description="Emergency contact's relationship to patient")
    phone: Optional[str] = Field(None, min_length=10, max_length=10, pattern=r"^\d{10}$", description="Emergency contact's 10-digit phone number")

class PrimaryInsurance(BaseModel):
    provider_name: str = Field(..., min_length=2, description="Primary insurance provider name")
    policy_number: str = Field(..., min_length=5, description="Primary insurance policy number")
    group_number: Optional[str] = Field(None, description="Primary insurance group number")
    subscriber_dob: Optional[date] = Field(None, description="Primary insurance subscriber date of birth")

    @field_validator('subscriber_dob')
    @classmethod
    def validate_subscriber_dob(cls, v: Optional[date]):
        if v and v > date.today():
            raise ValueError('Subscriber date of birth cannot be in the future.')
        return v

class SecondaryInsurance(BaseModel):
    has_secondary_insurance: bool
    provider_name: Optional[str] = Field(None, description="Secondary insurance provider name")
    policy_number: Optional[str] = Field(None, description="Secondary insurance policy number")

    @model_validator(mode='after')
    def validate_secondary_insurance_details(self) -> 'SecondaryInsurance':
        if self.has_secondary_insurance:
            if not self.provider_name:
                raise ValueError("Provider name is required if secondary insurance is selected.")
            if not self.policy_number:
                raise ValueError("Policy number is required if secondary insurance is selected.")
        return self

class InsuranceAndFinancial(BaseModel):
    primary_insurance: PrimaryInsurance
    secondary_insurance: SecondaryInsurance
    reason_for_visit_brief: str = Field(..., min_length=5, description="Brief reason for visit")
    financial_responsibility_acknowledged: bool = Field(..., description="Acknowledgement of financial responsibility")

class MedicalHistoryOverview(BaseModel):
    opt_in: bool = Field(False, description="Whether the user opted to provide medical history details")
    reason_for_appointment_full: Optional[str] = Field(None, description="Detailed reason for appointment/chief complaint")
    known_allergies: Optional[str] = Field(None, description="Known allergies")
    current_medications: Optional[str] = Field(None, description="Current medications and dosages")
    major_past_medical_conditions: Optional[str] = Field(None, description="Major past medical conditions/diagnoses")
    referring_physician: Optional[str] = Field(None, description="Referring physician name")

    @model_validator(mode='after')
    def medical_history_conditional_fields(self) -> 'MedicalHistoryOverview':
        if not self.opt_in:
            # If opt_in is False, ensure these fields are None
            self.reason_for_appointment_full = None
            self.known_allergies = None
            self.current_medications = None
            self.major_past_medical_conditions = None
            self.referring_physician = None
        return self

class AppointmentDetails(BaseModel):
    desired_appointment_date: date = Field(..., description="Desired appointment date")
    desired_appointment_time: time = Field(..., description="Desired appointment time")
    preferred_provider: Optional[str] = Field(None, description="Preferred provider name")
    special_needs: Optional[str] = Field(None, description="Any special needs")

    @field_validator('desired_appointment_date')
    @classmethod
    def validate_desired_appointment_date(cls, v: date):
        if v < date.today():
            raise ValueError('Desired appointment date cannot be in the past.')
        return v

class LegalCompliance(BaseModel):
    consent_for_treatment_acknowledged: bool = Field(..., description="Acknowledgement of initial consent for treatment")
    hipaa_privacy_acknowledged: bool = Field(..., description="Acknowledgement of HIPAA privacy practices")

class PatientPreAppointmentInfo(BaseModel):
    patient_demographics: PatientDemographics
    emergency_contact: EmergencyContact
    insurance_and_financial: InsuranceAndFinancial
    medical_history_overview: MedicalHistoryOverview
    appointment_details: AppointmentDetails
    legal_compliance: LegalCompliance

# --- Helper function to load NPP content ---
def load_npp_content():
    npp_file_path = "NPP.md" # Adjust path if NPP.md is not in the same directory
    if os.path.exists(npp_file_path):
        try:
            with open(npp_file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            st.error(f"Error reading NPP document: {e}")
            return "Could not load NPP document content."
    else:
        st.error(f"Error: NPP document '{npp_file_path}' not found.")
        return "Placeholder NPP content: This is a placeholder for the Notice of Privacy Practices. Please ensure the 'NPP.md' file is in the correct directory."

# --- Helper function to manage conversation state and ask next question ---
def ask_next_question():
    current_state = st.session_state.conversation_state
    new_patient_info = st.session_state.new_patient_info

    if current_state == "initial_greeting":
        st.session_state.messages.append({"role": "assistant", "content": "Welcome! Are you a new or existing patient?"})
        st.session_state.conversation_state = "user_type_selection"
    
    elif current_state == "user_type_selection":
        st.session_state.messages.append({"role": "assistant", "content": "Please type 'New User' or 'Existing User'."})
    
    elif current_state == "display_npp":
        st.session_state.messages.append({"role": "assistant", "content": "Please review our Notice of Privacy Practices. You must agree to proceed with your pre-appointment registration.\n\n" + st.session_state.npp_content + "\n\nDo you agree to the Notice of Privacy Practices? (Yes/No)"})
        st.session_state.conversation_state = "npp_agreement"

    elif current_state == "npp_agreement":
        st.session_state.messages.append({"role": "assistant", "content": "Please type 'Yes' to agree, or 'No' to go back to the user type selection."})

    elif current_state == "ask_full_legal_name":
        st.session_state.messages.append({"role": "assistant", "content": "Let's start with your demographics. What is your full legal name?"})
        st.session_state.conversation_state = "get_full_legal_name"
    
    elif current_state == "get_full_legal_name":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide your full legal name."})

    elif current_state == "ask_date_of_birth":
        st.session_state.messages.append({"role": "assistant", "content": "What is your date of birth? (YYYY-MM-DD)"})
        st.session_state.conversation_state = "get_date_of_birth"
    
    elif current_state == "get_date_of_birth":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide your date of birth in YYYY-MM-DD format."})

    elif current_state == "ask_phone_number":
        st.session_state.messages.append({"role": "assistant", "content": "What is your 10-digit phone number? (e.g., 5551234567)"})
        st.session_state.conversation_state = "get_phone_number"
    
    elif current_state == "get_phone_number":
        st.session_state.messages.append({"role": "assistant", "content": "Please enter your 10-digit phone number (numbers only)."})

    elif current_state == "ask_email_address":
        st.session_state.messages.append({"role": "assistant", "content": "What is your email address?"})
        st.session_state.conversation_state = "get_email_address"
    
    elif current_state == "get_email_address":
        st.session_state.messages.append({"role": "assistant", "content": "Please enter a valid email address."})

    elif current_state == "ask_gender":
        st.session_state.messages.append({"role": "assistant", "content": "What is your gender? (Male, Female, Non-binary, Prefer not to say)"})
        st.session_state.conversation_state = "get_gender"
    
    elif current_state == "get_gender":
        st.session_state.messages.append({"role": "assistant", "content": "Please select your gender from the options: Male, Female, Non-binary, or Prefer not to say."})

    elif current_state == "ask_address":
        st.session_state.messages.append({"role": "assistant", "content": "What is your current address?"})
        st.session_state.conversation_state = "get_address"
    
    elif current_state == "get_address":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide your full current address."})

    elif current_state == "ask_preferred_language":
        st.session_state.messages.append({"role": "assistant", "content": "What is your preferred language? (e.g., English)"})
        st.session_state.conversation_state = "get_preferred_language"
    
    elif current_state == "get_preferred_language":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide your preferred language."})

    elif current_state == "ask_emergency_contact_name":
        st.session_state.messages.append({"role": "assistant", "content": "Now let's move to emergency contact details. What is your emergency contact's full name? (Type 'Skip' if you don't have one)"})
        st.session_state.conversation_state = "get_emergency_contact_name"
    
    elif current_state == "get_emergency_contact_name":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide your emergency contact's name or type 'Skip'."})
    
    elif current_state == "ask_emergency_contact_relationship":
        st.session_state.messages.append({"role": "assistant", "content": f"What is {new_patient_info.get('emergency_contact', {}).get('name', 'your emergency contact')}'s relationship to you? (e.g., Friend, Parent, Spouse)"})
        st.session_state.conversation_state = "get_emergency_contact_relationship"
    
    elif current_state == "ask_emergency_contact_phone":
        st.session_state.messages.append({"role": "assistant", "content": f"What is {new_patient_info.get('emergency_contact', {}).get('name', 'your emergency contact')}'s 10-digit phone number?"})
        st.session_state.conversation_state = "get_emergency_contact_phone"
    
    elif current_state == "get_emergency_contact_phone":
        st.session_state.messages.append({"role": "assistant", "content": "Please enter your emergency contact's 10-digit phone number (numbers only)."})

    elif current_state == "ask_primary_insurance_provider":
        st.session_state.messages.append({"role": "assistant", "content": "Next, let's gather your insurance information. What is the name of your primary insurance provider?"})
        st.session_state.conversation_state = "get_primary_insurance_provider"
    
    elif current_state == "get_primary_insurance_provider":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide the name of your primary insurance provider."})

    elif current_state == "ask_primary_insurance_policy_number":
        st.session_state.messages.append({"role": "assistant", "content": "What is your primary insurance policy number?"})
        st.session_state.conversation_state = "get_primary_insurance_policy_number"
    
    elif current_state == "get_primary_insurance_policy_number":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide your primary insurance policy number."})

    elif current_state == "ask_primary_insurance_group_number":
        st.session_state.messages.append({"role": "assistant", "content": "Do you have a group number for your primary insurance? If not, type 'None'."})
        st.session_state.conversation_state = "get_primary_insurance_group_number"
    
    elif current_state == "ask_primary_insurance_subscriber_name":
        st.session_state.messages.append({"role": "assistant", "content": "Is the subscriber name on your primary insurance policy different from your name? If so, what is it? If not, type 'Same'."})
        st.session_state.conversation_state = "get_primary_insurance_subscriber_name"

    elif current_state == "ask_primary_insurance_subscriber_dob":
        st.session_state.messages.append({"role": "assistant", "content": "What is the subscriber's date of birth for your primary insurance? (YYYY-MM-DD, or type 'Skip' if not applicable)"})
        st.session_state.conversation_state = "get_primary_insurance_subscriber_dob"
    
    elif current_state == "get_primary_insurance_subscriber_dob":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide the subscriber's date of birth in YYYY-MM-DD format or type 'Skip'."})

    elif current_state == "ask_secondary_insurance_yn":
        st.session_state.messages.append({"role": "assistant", "content": "Do you have secondary insurance? (Yes/No)"})
        st.session_state.conversation_state = "get_secondary_insurance_yn"
    
    elif current_state == "get_secondary_insurance_yn":
        st.session_state.messages.append({"role": "assistant", "content": "Please answer 'Yes' or 'No'."})

    elif current_state == "ask_secondary_insurance_provider":
        st.session_state.messages.append({"role": "assistant", "content": "What is the name of your secondary insurance provider?"})
        st.session_state.conversation_state = "get_secondary_insurance_provider"
    
    elif current_state == "get_secondary_insurance_provider":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide the name of your secondary insurance provider."})

    elif current_state == "ask_secondary_insurance_policy_number":
        st.session_state.messages.append({"role": "assistant", "content": "What is your secondary insurance policy number?"})
        st.session_state.conversation_state = "get_secondary_insurance_policy_number"
    
    elif current_state == "get_secondary_insurance_policy_number":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide your secondary insurance policy number."})

    elif current_state == "ask_reason_for_visit_brief":
        st.session_state.messages.append({"role": "assistant", "content": "What is the brief reason for your visit? (e.g., 'Routine check-up', 'Follow-up for blood pressure')"})
        st.session_state.conversation_state = "get_reason_for_visit_brief"
    
    elif current_state == "get_reason_for_visit_brief":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide a brief reason for your visit."})

    elif current_state == "ask_financial_responsibility":
        st.session_state.messages.append({"role": "assistant", "content": "Do you understand your financial responsibility (co-pays, deductibles, etc.)? (Yes/No)"})
        st.session_state.conversation_state = "get_financial_responsibility"
    
    elif current_state == "get_financial_responsibility":
        st.session_state.messages.append({"role": "assistant", "content": "Please answer 'Yes' or 'No' regarding your understanding of financial responsibility."})

    elif current_state == "ask_medical_history_opt_in":
        st.session_state.messages.append({"role": "assistant", "content": "Would you like to provide an initial overview of your medical history now? (Yes/No)"})
        st.session_state.conversation_state = "get_medical_history_opt_in"
    
    elif current_state == "get_medical_history_opt_in":
        st.session_state.messages.append({"role": "assistant", "content": "Please answer 'Yes' or 'No'."})
    
    elif current_state == "ask_reason_for_appointment_full":
        st.session_state.messages.append({"role": "assistant", "content": "Can you describe the Reason for your Appointment/Chief Complaint in more detail? (Type 'Skip' if you already mentioned it briefly)"})
        st.session_state.conversation_state = "get_reason_for_appointment_full"
    
    elif current_state == "ask_known_allergies":
        st.session_state.messages.append({"role": "assistant", "content": "Do you have any Known Allergies (e.g., medications, food, environmental)? (Type 'None' if no allergies)"})
        st.session_state.conversation_state = "get_known_allergies"
    
    elif current_state == "ask_current_medications":
        st.session_state.messages.append({"role": "assistant", "content": "Please list your Current Medications (including OTC and supplements) and Dosages (e.g., 'Amlodipine 5mg daily'). (Type 'None' if no medications)"})
        st.session_state.conversation_state = "get_current_medications"

    elif current_state == "ask_major_past_medical_conditions":
        st.session_state.messages.append({"role": "assistant", "content": "Do you have any Major Past Medical Conditions/Diagnoses (e.g., 'Diabetes, Hypertension, Asthma')? (Type 'None' if none)"})
        st.session_state.conversation_state = "get_major_past_medical_conditions"

    elif current_state == "ask_referring_physician":
        st.session_state.messages.append({"role": "assistant", "content": "Is there a Referring Physician (name, if any)? (Type 'None' if none)"})
        st.session_state.conversation_state = "get_referring_physician"

    elif current_state == "ask_desired_appointment_date":
        st.session_state.messages.append({"role": "assistant", "content": "Now for appointment details. What is your desired appointment date? (YYYY-MM-DD)"})
        st.session_state.conversation_state = "get_desired_appointment_date"
    
    elif current_state == "get_desired_appointment_date":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide your desired appointment date in YYYY-MM-DD format. Remember, it cannot be in the past."})

    elif current_state == "ask_desired_appointment_time":
        st.session_state.messages.append({"role": "assistant", "content": "What is your desired appointment time? (HH:MM AM/PM, e.g., 10:30 AM)"})
        st.session_state.conversation_state = "get_desired_appointment_time"
    
    elif current_state == "get_desired_appointment_time":
        st.session_state.messages.append({"role": "assistant", "content": "Please provide your desired appointment time in HH:MM AM/PM format."})

    elif current_state == "ask_preferred_provider":
        st.session_state.messages.append({"role": "assistant", "content": "Do you have a preferred provider? (e.g., Dr. Smith, or type 'None')"})
        st.session_state.conversation_state = "get_preferred_provider"
    
    elif current_state == "ask_special_needs":
        st.session_state.messages.append({"role": "assistant", "content": "Do you have any special needs (e.g., interpreter, wheelchair access)? (Type 'None' if none)"})
        st.session_state.conversation_state = "get_special_needs"

    elif current_state == "ask_consent_for_treatment":
        st.session_state.messages.append({"role": "assistant", "content": "Do you acknowledge initial consent for treatment (full consent upon arrival)? (Yes/No)"})
        st.session_state.conversation_state = "get_consent_for_treatment"
    
    elif current_state == "get_consent_for_treatment":
        st.session_state.messages.append({"role": "assistant", "content": "Please answer 'Yes' or 'No'."})

    elif current_state == "ask_hipaa_privacy_acknowledged":
        st.session_state.messages.append({"role": "assistant", "content": "Do you acknowledge receipt and understanding of HIPAA Privacy Practices? (Yes/No)"})
        st.session_state.conversation_state = "get_hipaa_privacy_acknowledged"
    
    elif current_state == "get_hipaa_privacy_acknowledged":
        st.session_state.messages.append({"role": "assistant", "content": "Please answer 'Yes' or 'No'."})

    elif current_state == "review_and_submit":
        st.session_state.messages.append({"role": "assistant", "content": "We have collected all necessary information. Please review the summary and type 'Submit' to finalize, or 'Back' to make changes."})
        st.session_state.messages.append({"role": "assistant", "content": json.dumps(st.session_state.new_patient_info, indent=2)})
        st.session_state.conversation_state = "await_final_submission"
    
    elif current_state == "await_final_submission":
        st.session_state.messages.append({"role": "assistant", "content": "Type 'Submit' to finalize or 'Back' to review."})

    elif current_state == "submission_complete":
        st.session_state.messages.append({"role": "assistant", "content": "Your pre-appointment registration is complete! Thank you. Would you like to 'Start Over'?"})
        st.session_state.conversation_state = "offer_start_over"

    elif current_state == "existing_user_info":
        st.session_state.messages.append({"role": "assistant", "content": "Thank you for being an existing patient! For existing patients, please contact our support team at 123-456-7890 or log in to your patient portal for appointment management. Type 'Start Over' to go back to user selection."})
        st.session_state.conversation_state = "offer_start_over"

def process_response(user_input: str):
    current_state = st.session_state.conversation_state
    new_patient_info = st.session_state.new_patient_info

    # Handle general questions
    if any(keyword in user_input.lower() for keyword in ["what is", "tell me about", "question about", "privacy", "hipaa", "npp"]):
        st.session_state.messages.append({"role": "assistant", "content": "The Notice of Privacy Practices (NPP) describes how your medical information may be used and disclosed and your rights regarding that information. It outlines our commitment to protecting your health information. You can read the full text again here:\n\n" + st.session_state.npp_content})
        # Re-ask the current question after providing the answer
        ask_next_question() 
        return

    # Process form inputs based on current state
    if current_state == "user_type_selection":
        if "new user" in user_input.lower():
            st.session_state.user_type_chosen = "New User"
            st.session_state.conversation_state = "display_npp"
            ask_next_question()
        elif "existing user" in user_input.lower():
            st.session_state.user_type_chosen = "Existing User"
            st.session_state.conversation_state = "existing_user_info"
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "I didn't understand. Please type 'New User' or 'Existing User'."})

    elif current_state == "npp_agreement":
        if "yes" in user_input.lower():
            st.session_state.npp_agreed = True
            st.session_state.conversation_state = "ask_full_legal_name"
            st.session_state.messages.append({"role": "assistant", "content": "Great! Let's start with your pre-appointment registration."})
            ask_next_question()
        elif "no" in user_input.lower():
            st.session_state.npp_agreed = False
            st.session_state.user_type_chosen = None # Go back to initial selection
            st.session_state.conversation_state = "initial_greeting"
            st.session_state.messages.append({"role": "assistant", "content": "Okay, returning to the start."})
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please respond with 'Yes' or 'No'."})

    # Demographics
    elif current_state == "get_full_legal_name":
        try:
            # Temporarily create a PatientDemographics instance to validate just the name
            # This requires dummy values for other fields to satisfy Pydantic's requirements
            temp_demographics = PatientDemographics(
                full_legal_name=user_input,
                date_of_birth=date(2000, 1, 1), # Dummy value
                gender="Male", # Dummy value
                phone_number="1234567890", # Dummy value
                email_address="dummy@example.com" # Dummy value
            )
            st.session_state.new_patient_info.setdefault("patient_demographics", {})["full_legal_name"] = user_input
            st.session_state.conversation_state = "ask_date_of_birth"
            ask_next_question()
        except ValidationError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please enter a valid full legal name (2-100 characters)."})

    elif current_state == "get_date_of_birth":
        try:
            dob = date.fromisoformat(user_input)
            # Dummy values for other required fields to validate date_of_birth
            PatientDemographics(
                full_legal_name="Dummy Name", 
                date_of_birth=dob, 
                gender="Male", 
                address="N/A", 
                phone_number="1234567890", 
                email_address="test@example.com"
            )
            st.session_state.new_patient_info.setdefault("patient_demographics", {})["date_of_birth"] = dob.isoformat()
            st.session_state.conversation_state = "ask_phone_number"
            ask_next_question()
        except ValueError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Invalid date format or age. {e}. Please use YYYY-MM-DD."})
        except ValidationError as e:
            # More specific error message from Pydantic validator
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please use YYYY-MM-DD."})

    elif current_state == "get_phone_number":
        try:
            # Use dummy data to validate just the phone number field
            temp_demographics = PatientDemographics(
                full_legal_name="Dummy Name",
                date_of_birth=date(2000, 1, 1),
                gender="Male",
                phone_number=user_input,
                email_address="dummy@example.com"
            )
            st.session_state.new_patient_info.setdefault("patient_demographics", {})["phone_number"] = user_input
            st.session_state.conversation_state = "ask_email_address"
            ask_next_question()
        except ValidationError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please enter a valid 10-digit phone number (numbers only)."})

    elif current_state == "get_email_address":
        try:
            temp_demographics = PatientDemographics(
                full_legal_name="Dummy Name",
                date_of_birth=date(2000, 1, 1),
                gender="Male",
                phone_number="1234567890",
                email_address=user_input
            )
            st.session_state.new_patient_info.setdefault("patient_demographics", {})["email_address"] = user_input
            st.session_state.conversation_state = "ask_gender"
            ask_next_question()
        except ValidationError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please enter a valid email address."})

    elif current_state == "get_gender":
        gender_options = ["Male", "Female", "Non-binary", "Prefer not to say"]
        if user_input.title() in gender_options: # .title() will capitalize first letter
            st.session_state.new_patient_info.setdefault("patient_demographics", {})["gender"] = user_input.title()
            st.session_state.conversation_state = "ask_address"
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please select from: Male, Female, Non-binary, or Prefer not to say."})

    elif current_state == "get_address":
        # No Pydantic validation for address length in model, so basic check here
        if len(user_input) >= 5: 
            st.session_state.new_patient_info.setdefault("patient_demographics", {})["address"] = user_input
            st.session_state.conversation_state = "ask_preferred_language"
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please provide a more complete address."})
    
    elif current_state == "get_preferred_language":
        if len(user_input) >= 2:
            st.session_state.new_patient_info.setdefault("patient_demographics", {})["preferred_language"] = user_input
            st.session_state.conversation_state = "ask_emergency_contact_name"
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please provide your preferred language."})

    # Emergency Contact
    elif current_state == "get_emergency_contact_name":
        if user_input.lower() == "skip":
            st.session_state.new_patient_info.setdefault("emergency_contact", {})["name"] = None
            st.session_state.new_patient_info["emergency_contact"]["relationship"] = None
            st.session_state.new_patient_info["emergency_contact"]["phone"] = None
            st.session_state.conversation_state = "ask_primary_insurance_provider" # Skip to next section
            ask_next_question()
        elif len(user_input) >= 2:
            st.session_state.new_patient_info.setdefault("emergency_contact", {})["name"] = user_input
            st.session_state.conversation_state = "ask_emergency_contact_relationship"
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please enter a valid name or 'Skip'."})

    elif current_state == "get_emergency_contact_relationship":
        if len(user_input) >= 2:
            st.session_state.new_patient_info["emergency_contact"]["relationship"] = user_input
            st.session_state.conversation_state = "ask_emergency_contact_phone"
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please provide a relationship."})

    elif current_state == "get_emergency_contact_phone":
        try:
            # Use dummy values for name and relationship for validation
            temp_contact = EmergencyContact(
                name="Dummy",
                relationship="Dummy",
                phone=user_input
            )
            st.session_state.new_patient_info["emergency_contact"]["phone"] = user_input
            st.session_state.conversation_state = "ask_primary_insurance_provider"
            ask_next_question()
        except ValidationError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please enter a valid 10-digit phone number (numbers only)."})

    # Insurance and Financial
    elif current_state == "get_primary_insurance_provider":
        try:
            temp_insurance = PrimaryInsurance(
                provider_name=user_input,
                policy_number="dummy" * 5 # Satisfy min_length for policy_number
            )
            st.session_state.new_patient_info.setdefault("insurance_and_financial", {}).setdefault("primary_insurance", {})["provider_name"] = user_input
            st.session_state.conversation_state = "ask_primary_insurance_policy_number"
            ask_next_question()
        except ValidationError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please enter the provider name."})

    elif current_state == "get_primary_insurance_policy_number":
        try:
            temp_insurance = PrimaryInsurance(
                provider_name="Dummy",
                policy_number=user_input
            )
            st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["policy_number"] = user_input
            st.session_state.conversation_state = "ask_primary_insurance_group_number"
            ask_next_question()
        except ValidationError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please enter a valid policy number (at least 5 characters)."})

    elif current_state == "get_primary_insurance_group_number":
        st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["group_number"] = user_input if user_input.lower() != "none" else None
        st.session_state.conversation_state = "ask_primary_insurance_subscriber_name"
        ask_next_question()
    
    elif current_state == "get_primary_insurance_subscriber_name":
        # subscriber_name is not in the Pydantic model for PrimaryInsurance, only subscriber_dob
        # So, no Pydantic validation here for 'subscriber_name' itself.
        st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["subscriber_name"] = user_input if user_input.lower() != "same" else None
        st.session_state.conversation_state = "ask_primary_insurance_subscriber_dob"
        ask_next_question()

    elif current_state == "get_primary_insurance_subscriber_dob":
        if user_input.lower() == "skip":
            st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["subscriber_dob"] = None
            st.session_state.conversation_state = "ask_secondary_insurance_yn"
            ask_next_question()
        else:
            try:
                dob = date.fromisoformat(user_input)
                # Need to provide other required fields for PrimaryInsurance validation
                PrimaryInsurance(
                    provider_name=st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"].get("provider_name", "Dummy"),
                    policy_number=st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"].get("policy_number", "Dummy123"),
                    subscriber_dob=dob
                )
                st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["subscriber_dob"] = dob.isoformat()
                st.session_state.conversation_state = "ask_secondary_insurance_yn"
                ask_next_question()
            except ValueError as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Invalid date format. {e}. Please use YYYY-MM-DD or 'Skip'."})
            except ValidationError as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please use YYYY-MM-DD or 'Skip'."})

    elif current_state == "get_secondary_insurance_yn":
        if "yes" in user_input.lower():
            st.session_state.new_patient_info.setdefault("insurance_and_financial", {}).setdefault("secondary_insurance", {})["has_secondary_insurance"] = True
            st.session_state.conversation_state = "ask_secondary_insurance_provider"
            ask_next_question()
        elif "no" in user_input.lower():
            st.session_state.new_patient_info.setdefault("insurance_and_financial", {}).setdefault("secondary_insurance", {})["has_secondary_insurance"] = False
            st.session_state.new_patient_info["insurance_and_financial"]["secondary_insurance"]["provider_name"] = None
            st.session_state.new_patient_info["insurance_and_financial"]["secondary_insurance"]["policy_number"] = None
            st.session_state.conversation_state = "ask_reason_for_visit_brief"
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please answer 'Yes' or 'No'."})

    elif current_state == "get_secondary_insurance_provider":
        try:
            # Need to create a partial SecondaryInsurance model for validation
            temp_secondary_insurance = SecondaryInsurance(
                has_secondary_insurance=True, # Must be True to trigger validation for provider_name
                provider_name=user_input,
                policy_number="Dummy12345" # Dummy value to satisfy min_length
            )
            st.session_state.new_patient_info["insurance_and_financial"]["secondary_insurance"]["provider_name"] = user_input
            st.session_state.conversation_state = "ask_secondary_insurance_policy_number"
            ask_next_question()
        except ValidationError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please provide the secondary insurance provider name."})

    elif current_state == "get_secondary_insurance_policy_number":
        try:
            temp_secondary_insurance = SecondaryInsurance(
                has_secondary_insurance=True,
                provider_name="Dummy",
                policy_number=user_input
            )
            st.session_state.new_patient_info["insurance_and_financial"]["secondary_insurance"]["policy_number"] = user_input
            st.session_state.conversation_state = "ask_reason_for_visit_brief"
            ask_next_question()
        except ValidationError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please provide the secondary insurance policy number."})

    elif current_state == "get_reason_for_visit_brief":
        try:
            # To validate reason_for_visit_brief, we need to provide dummy data for PrimaryInsurance
            # and SecondaryInsurance, and financial_responsibility_acknowledged.
            temp_insurance_financial = InsuranceAndFinancial(
                primary_insurance=PrimaryInsurance(provider_name="D", policy_number="12345"),
                secondary_insurance=SecondaryInsurance(has_secondary_insurance=False),
                reason_for_visit_brief=user_input,
                financial_responsibility_acknowledged=True
            )
            st.session_state.new_patient_info.setdefault("insurance_and_financial", {})["reason_for_visit_brief"] = user_input
            st.session_state.conversation_state = "ask_financial_responsibility"
            ask_next_question()
        except ValidationError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please provide a brief reason for your visit (at least 5 characters)."})

    elif current_state == "get_financial_responsibility":
        if "yes" in user_input.lower():
            st.session_state.new_patient_info.setdefault("insurance_and_financial", {})["financial_responsibility_acknowledged"] = True
            st.session_state.conversation_state = "ask_medical_history_opt_in"
            ask_next_question()
        elif "no" in user_input.lower():
            st.session_state.messages.append({"role": "assistant", "content": "You must acknowledge financial responsibility to proceed. Please type 'Yes'."})
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please answer 'Yes' or 'No'."})

    # Medical History
    elif current_state == "get_medical_history_opt_in":
        if "yes" in user_input.lower():
            st.session_state.new_patient_info.setdefault("medical_history_overview", {})["opt_in"] = True
            st.session_state.conversation_state = "ask_reason_for_appointment_full"
            ask_next_question()
        elif "no" in user_input.lower():
            st.session_state.new_patient_info.setdefault("medical_history_overview", {})["opt_in"] = False
            # Clear any previously entered medical history details if user opts out
            st.session_state.new_patient_info["medical_history_overview"]["reason_for_appointment_full"] = None
            st.session_state.new_patient_info["medical_history_overview"]["known_allergies"] = None
            st.session_state.new_patient_info["medical_history_overview"]["current_medications"] = None
            st.session_state.new_patient_info["medical_history_overview"]["major_past_medical_conditions"] = None
            st.session_state.new_patient_info["medical_history_overview"]["referring_physician"] = None
            st.session_state.conversation_state = "ask_desired_appointment_date" # Skip medical history details
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please answer 'Yes' or 'No'."})

    elif current_state == "get_reason_for_appointment_full":
        st.session_state.new_patient_info.setdefault("medical_history_overview", {})["reason_for_appointment_full"] = user_input if user_input.lower() != "skip" else None
        st.session_state.conversation_state = "ask_known_allergies"
        ask_next_question()

    elif current_state == "get_known_allergies":
        st.session_state.new_patient_info.setdefault("medical_history_overview", {})["known_allergies"] = user_input if user_input.lower() != "none" else None
        st.session_state.conversation_state = "ask_current_medications"
        ask_next_question()

    elif current_state == "get_current_medications":
        st.session_state.new_patient_info.setdefault("medical_history_overview", {})["current_medications"] = user_input if user_input.lower() != "none" else None
        st.session_state.conversation_state = "ask_major_past_medical_conditions"
        ask_next_question()

    elif current_state == "get_major_past_medical_conditions":
        st.session_state.new_patient_info.setdefault("medical_history_overview", {})["major_past_medical_conditions"] = user_input if user_input.lower() != "none" else None
        st.session_state.conversation_state = "ask_referring_physician"
        ask_next_question()

    elif current_state == "get_referring_physician":
        st.session_state.new_patient_info.setdefault("medical_history_overview", {})["referring_physician"] = user_input if user_input.lower() != "none" else None
        st.session_state.conversation_state = "ask_desired_appointment_date"
        ask_next_question()

    # Appointment Details
    elif current_state == "get_desired_appointment_date":
        try:
            app_date = date.fromisoformat(user_input)
            # Dummy time for Pydantic validation of date
            AppointmentDetails(
                desired_appointment_date=app_date, desired_appointment_time=time(9,0)
            )
            st.session_state.new_patient_info.setdefault("appointment_details", {})["desired_appointment_date"] = app_date.isoformat()
            st.session_state.conversation_state = "ask_desired_appointment_time"
            ask_next_question()
        except ValueError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Invalid date format or date in past. {e}. Please use YYYY-MM-DD and ensure it's not in the past."})
        except ValidationError as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Validation error: {e.errors()[0]['msg']}. Please use YYYY-MM-DD and ensure it's not in the past."})

    elif current_state == "get_desired_appointment_time":
        try:
            # Handle HH:MM AM/PM input
            if "am" in user_input.lower() or "pm" in user_input.lower():
                app_time = datetime.strptime(user_input.upper(), "%I:%M %p").time()
            else: # Assume 24-hour format if no AM/PM
                app_time = time.fromisoformat(user_input)
            
            st.session_state.new_patient_info.setdefault("appointment_details", {})["desired_appointment_time"] = app_time.isoformat()
            st.session_state.conversation_state = "ask_preferred_provider"
            ask_next_question()
        except ValueError:
            st.session_state.messages.append({"role": "assistant", "content": "Invalid time format. Please use HH:MM AM/PM (e.g., 10:30 AM) or HH:MM (e.g., 14:00)."})

    elif current_state == "get_preferred_provider":
        st.session_state.new_patient_info.setdefault("appointment_details", {})["preferred_provider"] = user_input if user_input.lower() != "none" else None
        st.session_state.conversation_state = "ask_special_needs"
        ask_next_question()

    elif current_state == "get_special_needs":
        st.session_state.new_patient_info.setdefault("appointment_details", {})["special_needs"] = user_input if user_input.lower() != "none" else None
        st.session_state.conversation_state = "ask_consent_for_treatment"
        ask_next_question()
    
    # Legal Compliance
    elif current_state == "get_consent_for_treatment":
        if "yes" in user_input.lower():
            st.session_state.new_patient_info.setdefault("legal_compliance", {})["consent_for_treatment_acknowledged"] = True
            st.session_state.conversation_state = "ask_hipaa_privacy_acknowledged"
            ask_next_question()
        elif "no" in user_input.lower():
            st.session_state.messages.append({"role": "assistant", "content": "You must acknowledge consent for treatment to proceed. Please type 'Yes'."})
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please answer 'Yes' or 'No'."})
    
    elif current_state == "get_hipaa_privacy_acknowledged":
        if "yes" in user_input.lower():
            st.session_state.new_patient_info.setdefault("legal_compliance", {})["hipaa_privacy_acknowledged"] = True
            st.session_state.conversation_state = "review_and_submit"
            ask_next_question()
        elif "no" in user_input.lower():
            st.session_state.messages.append({"role": "assistant", "content": "You must acknowledge HIPAA privacy practices to proceed. Please type 'Yes'."})
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please answer 'Yes' or 'No'."})

    # Final Submission
    elif current_state == "await_final_submission":
        if "submit" in user_input.lower():
            try:
                # Ensure all necessary nested dictionaries and boolean flags are present for Pydantic validation
                # The data structure needs to match the PatientPreAppointmentInfo model exactly
                
                # Default values for potentially missing nested dicts
                patient_demographics_data = st.session_state.new_patient_info.get("patient_demographics", {})
                emergency_contact_data = st.session_state.new_patient_info.get("emergency_contact", {})
                insurance_and_financial_data = st.session_state.new_patient_info.get("insurance_and_financial", {})
                medical_history_overview_data = st.session_state.new_patient_info.get("medical_history_overview", {})
                appointment_details_data = st.session_state.new_patient_info.get("appointment_details", {})
                legal_compliance_data = st.session_state.new_patient_info.get("legal_compliance", {})

                # Ensure required sub-models and their required fields have dummy or default values if not yet collected
                # This is crucial for Pydantic to attempt validation of the whole structure.
                
                # PatientDemographics
                # All fields are required except address, which defaults to ""
                if "full_legal_name" not in patient_demographics_data: patient_demographics_data["full_legal_name"] = "Temp Name"
                if "date_of_birth" not in patient_demographics_data: patient_demographics_data["date_of_birth"] = date(2000, 1, 1).isoformat()
                if "gender" not in patient_demographics_data: patient_demographics_data["gender"] = "Male"
                if "phone_number" not in patient_demographics_data: patient_demographics_data["phone_number"] = "1234567890"
                if "email_address" not in patient_demographics_data: patient_demographics_data["email_address"] = "temp@example.com"
                
                # PrimaryInsurance
                primary_insurance_data = insurance_and_financial_data.get("primary_insurance", {})
                if "provider_name" not in primary_insurance_data: primary_insurance_data["provider_name"] = "Temp Provider"
                if "policy_number" not in primary_insurance_data: primary_insurance_data["policy_number"] = "TEMP12345"
                insurance_and_financial_data["primary_insurance"] = primary_insurance_data

                # SecondaryInsurance
                secondary_insurance_data = insurance_and_financial_data.get("secondary_insurance", {})
                if "has_secondary_insurance" not in secondary_insurance_data: secondary_insurance_data["has_secondary_insurance"] = False
                insurance_and_financial_data["secondary_insurance"] = secondary_insurance_data

                # InsuranceAndFinancial
                if "reason_for_visit_brief" not in insurance_and_financial_data: insurance_and_financial_data["reason_for_visit_brief"] = "Temp Reason"
                if "financial_responsibility_acknowledged" not in insurance_and_financial_data: insurance_and_financial_data["financial_responsibility_acknowledged"] = False

                # MedicalHistoryOverview
                if "opt_in" not in medical_history_overview_data: medical_history_overview_data["opt_in"] = False

                # AppointmentDetails
                if "desired_appointment_date" not in appointment_details_data: appointment_details_data["desired_appointment_date"] = date.today().isoformat()
                if "desired_appointment_time" not in appointment_details_data: appointment_details_data["desired_appointment_time"] = time(9,0).isoformat()

                # LegalCompliance
                if "consent_for_treatment_acknowledged" not in legal_compliance_data: legal_compliance_data["consent_for_treatment_acknowledged"] = False
                if "hipaa_privacy_acknowledged" not in legal_compliance_data: legal_compliance_data["hipaa_privacy_acknowledged"] = False

                full_data = {
                    "patient_demographics": patient_demographics_data,
                    "emergency_contact": emergency_contact_data,
                    "insurance_and_financial": insurance_and_financial_data,
                    "medical_history_overview": medical_history_overview_data,
                    "appointment_details": appointment_details_data,
                    "legal_compliance": legal_compliance_data,
                }
                
                validated_info = PatientPreAppointmentInfo(**full_data)
                st.session_state.messages.append({"role": "assistant", "content": "Form data is valid and ready for backend submission!"})
                st.session_state.messages.append({"role": "assistant", "content": f"```json\n{json.dumps(validated_info.dict(), indent=4)}\n```"})
                st.session_state.conversation_state = "submission_complete"
                ask_next_question()
            except ValidationError as e:
                st.session_state.messages.append({"role": "assistant", "content": "Validation Errors Detected! Please review your input. Here are the errors:"})
                for error in e.errors():
                    field = ".".join(error['loc'])
                    message = error['msg']
                    st.session_state.messages.append({"role": "assistant", "content": f"❌ **Error in `{field}`:** {message}"})
                st.session_state.messages.append({"role": "assistant", "content": "Type 'Back' to go to the last section with errors or 'Submit' again if you think it's correct after review."})

        elif "back" in user_input.lower():
            # This 'Back' logic is simplified for chatbot.
            # In a real app, you'd need to track previous states more granularly.
            st.session_state.conversation_state = "ask_hipaa_privacy_acknowledged" # Go back to the last form section
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please type 'Submit' to finalize or 'Back' to review."})

    elif current_state == "offer_start_over":
        if "start over" in user_input.lower():
            st.session_state.clear()
            st.session_state.messages = [] # Clear messages on start over
            st.session_state.conversation_state = "initial_greeting"
            ask_next_question()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Please type 'Start Over' or continue."})


def app():
    st.set_page_config(
        page_title="RCM Healthcare Patient Pre-Appointment Chatbot",
        layout="centered",
        initial_sidebar_state="auto"
    )

    st.title("🏥 RCM Healthcare Patient Pre-Appointment Chatbot")

    # Initialize session state variables
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'conversation_state' not in st.session_state:
        st.session_state.conversation_state = "initial_greeting"
    if 'new_patient_info' not in st.session_state:
        st.session_state.new_patient_info = {}
    if 'npp_agreed' not in st.session_state: # Still useful for internal state tracking
        st.session_state.npp_agreed = False
    if 'npp_content' not in st.session_state:
        st.session_state.npp_content = load_npp_content() # Load NPP content once

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # If this is the first run or after a restart, ask the initial question
    if not st.session_state.messages or st.session_state.messages[-1]["role"] == "user":
        # Only ask the next question if the last message was from the user or it's the very first load
        ask_next_question()

    # Chat input for user
    if user_input := st.chat_input("Type your response here..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        process_response(user_input)
        # Streamlit automatically reruns on input, so no explicit rerun needed here.


if __name__ == '__main__':
    app()