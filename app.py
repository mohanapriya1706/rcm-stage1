import streamlit as st
import json
from datetime import date, time
import os # To check for file existence

def app():
    st.set_page_config(
        page_title="RCM Healthcare Patient Pre-Appointment",
        layout="centered",
        initial_sidebar_state="auto"
    )

    st.title("🏥 RCM Healthcare Patient Pre-Appointment")

    # Initialize session state variables
    if 'user_type_chosen' not in st.session_state:
        st.session_state.user_type_chosen = None # Stores the user's initial selection
    if 'new_patient_info' not in st.session_state:
        st.session_state.new_patient_info = {}
    if 'npp_agreed' not in st.session_state:
        st.session_state.npp_agreed = False # New state variable for NPP agreement


    # --- Step 1: Choose User Role ---
    if st.session_state.user_type_chosen is None:
        st.write("Welcome! Are you a new or existing patient?")
        
        # Using a form to group the radio button and a submit button
        with st.form(key="user_role_form"):
            user_choice = st.radio(
                "Please select your patient status:",
                ("Select", "New User", "Existing User"),
                key="initial_user_type_radio"
            )
            confirm_button = st.form_submit_button("Confirm Selection")

            if confirm_button:
                if user_choice == "Select":
                    st.error("Please select 'New User' or 'Existing User' to proceed.")
                else:
                    st.session_state.user_type_chosen = user_choice
                    st.rerun() # Rerun to display next state


    # --- Step 2: Display Content Based on Role ---
    if st.session_state.user_type_chosen == "New User":
        # --- Section: Display NPP and Get Confirmation ---
        if not st.session_state.npp_agreed: # Only show NPP if not yet agreed
            st.header("Notice of Privacy Practices (NPP)")
            st.write("Please review our Notice of Privacy Practices. You must agree to proceed with your pre-appointment registration.")

            npp_content = ""
            npp_file_path = "npp.md"
            if os.path.exists(npp_file_path):
                try:
                    with open(npp_file_path, "r", encoding="utf-8") as f:
                        npp_content = f.read()
                    st.markdown(npp_content, unsafe_allow_html=True) # Use unsafe_allow_html if npp.md contains HTML
                except Exception as e:
                    st.error(f"Error reading NPP document: {e}")
                    npp_content = "Could not load NPP document content."
            else:
                st.error(f"Error: NPP document '{npp_file_path}' not found in the current directory.")
                npp_content = "Placeholder NPP content: This is a placeholder for the Notice of Privacy Practices. Please ensure the 'npp.md' file is in the same directory as the Streamlit app."
                st.markdown(npp_content)


            with st.form(key='npp_agreement_form'):
                agree_npp = st.checkbox("I have read and agree to the Notice of Privacy Practices*", key="agree_npp_checkbox")
                
                col_npp_buttons = st.columns(2)
                with col_npp_buttons[0]:
                    if st.form_submit_button("Proceed to Registration"):
                        if agree_npp:
                            st.session_state.npp_agreed = True
                            st.rerun() # After agreeing, immediately show the form section
                        else:
                            st.error("You must agree to the NPP to proceed with registration.")
                with col_npp_buttons[1]:
                    if st.form_submit_button("Go Back to User Type Selection"):
                        st.session_state.clear() # Clear all state to restart
                        st.rerun()
        else: # If NPP is agreed, show the form
            st.write("Please fill out the following details for your first-time appointment.")

            with st.form(key='new_patient_pre_appointment_form'):
                st.header("Patient Demographics & Contact Information")
                col1, col2 = st.columns(2)
                with col1:
                    patient_name = st.text_input("Full Legal Name*", key="np_patient_name")
                    patient_dob = st.date_input("Date of Birth*", min_value=date(1900, 1, 1), max_value=date.today(), key="np_patient_dob")
                    patient_phone = st.text_input("Phone Number*", key="np_patient_phone")
                    patient_email = st.text_input("Email Address*", key="np_patient_email")
                with col2:
                    patient_gender = st.selectbox("Gender*", ["Select", "Male", "Female", "Non-binary", "Prefer not to say"], key="np_patient_gender")
                    patient_address = st.text_area("Current Address", key="np_patient_address")
                    preferred_language = st.text_input("Preferred Language", "English", key="np_preferred_language")

                st.subheader("Emergency Contact Information")
                col3, col4 = st.columns(2)
                with col3:
                    emergency_contact_name = st.text_input("Emergency Contact Name", key="np_ec_name")
                with col4:
                    emergency_contact_relationship = st.text_input("Relationship to Patient", key="np_ec_relationship")
                    emergency_contact_phone = st.text_input("Emergency Contact Phone", key="np_ec_phone")

                st.header("Insurance & Financial Information")
                primary_insurance_provider = st.text_input("Primary Insurance Provider Name*", key="np_pi_provider")
                col5, col6 = st.columns(2)
                with col5:
                    policy_number = st.text_input("Policy Number*", key="np_pi_policy")
                    subscriber_name = st.text_input("Subscriber Name (if different)", key="np_pi_subscriber_name")
                with col6:
                    group_number = st.text_input("Group Number (if applicable)", key="np_pi_group")
                    subscriber_dob = st.date_input("Subscriber Date of Birth (if different)", min_value=date(1900, 1, 1), max_value=date.today(), key="np_pi_subscriber_dob")

                has_secondary_insurance = st.radio(
                    "Do you have secondary insurance?",
                    ("No", "Yes"),
                    key="np_secondary_insurance_radio"
                )
                secondary_insurance_provider = ""
                secondary_policy_number = ""
                if has_secondary_insurance == "Yes":
                    secondary_insurance_provider = st.text_input("Secondary Insurance Provider Name", key="np_si_provider")
                    secondary_policy_number = st.text_input("Secondary Policy Number", key="np_si_policy")

                reason_for_visit_brief = st.text_area("Brief Reason for Visit*", help="e.g., 'Routine check-up', 'Follow-up for blood pressure'", key="np_reason_brief")
                financial_responsibility_ack = st.checkbox("I understand my financial responsibility (co-pays, deductibles, etc.)*", key="np_financial_ack")

                st.header("Medical History (Initial Overview)")
                st.info("A detailed medical history will be collected during your appointment.")
                with st.expander("Optional: Provide Medical History Details"):
                    reason_for_appointment_full = st.text_area("Reason for Appointment/Chief Complaint", help="Describe your main health concern in more detail.", key="np_mh_full_reason")
                    known_allergies = st.text_area("Known Allergies (e.g., medications, food, environmental)", key="np_mh_allergies")
                    current_medications = st.text_area("Current Medications (including OTC and supplements) and Dosages", help="Please list name and dosage (e.g., 'Amlodipine 5mg daily')", key="np_mh_meds")
                    major_past_medical_conditions = st.text_area("Major Past Medical Conditions/Diagnoses", help="e.g., 'Diabetes, Hypertension, Asthma'", key="np_mh_conditions")
                    referring_physician = st.text_input("Referring Physician Name (if any)", key="np_mh_referring")

                st.header("Appointment Details")
                col7, col8 = st.columns(2)
                with col7:
                    desired_appointment_date = st.date_input("Desired Appointment Date*", min_value=date.today(), key="np_app_date")
                with col8:
                    desired_appointment_time = st.time_input("Desired Appointment Time*", value=time(9, 0), key="np_app_time")

                preferred_provider = st.text_input("Preferred Provider (e.g., Dr. Smith)", key="np_app_provider")
                special_needs = st.text_area("Any Special Needs (e.g., interpreter, wheelchair access)", key="np_app_special_needs")

                st.header("Legal & Compliance")
                consent_treatment_ack = st.checkbox("I acknowledge initial consent for treatment (full consent upon arrival)*", key="np_lc_consent_ack")
                hipaa_ack = st.checkbox("I acknowledge receipt and understanding of HIPAA Privacy Practices*", key="np_lc_hipaa_ack")

                st.markdown("---")
                submit_button = st.form_submit_button(label='Submit Pre-Appointment Details')

            if submit_button:
                # Basic validation
                required_fields = {
                    "Full Legal Name": patient_name,
                    "Date of Birth": patient_dob,
                    "Phone Number": patient_phone,
                    "Email Address": patient_email,
                    "Primary Insurance Provider Name": primary_insurance_provider,
                    "Policy Number": policy_number,
                    "Brief Reason for Visit": reason_for_visit_brief,
                    "Desired Appointment Date": desired_appointment_date,
                    "Desired Appointment Time": desired_appointment_time,
                    "Financial Responsibility Acknowledgment": financial_responsibility_ack,
                    "Consent for Treatment Acknowledgment": consent_treatment_ack,
                    "HIPAA Acknowledgment": hipaa_ack
                }

                missing_fields = [field_name for field_name, value in required_fields.items() if not value or (isinstance(value, str) and value.strip() == "") or (isinstance(value, (date, time)) and value is None)]
                if patient_gender == "Select":
                    missing_fields.append("Gender")

                if missing_fields:
                    st.error(f"Please fill in all the required fields marked with an asterisk (*). Missing: {', '.join(missing_fields)}")
                else:
                    # Collect data into a dictionary
                    st.session_state.new_patient_info = {
                        "patient_demographics": {
                            "full_legal_name": patient_name,
                            "date_of_birth": patient_dob.isoformat() if patient_dob else None,
                            "gender": patient_gender,
                            "address": patient_address,
                            "phone_number": patient_phone,
                            "email_address": patient_email,
                            "preferred_language": preferred_language
                        },
                        "emergency_contact": {
                            "name": emergency_contact_name,
                            "relationship": emergency_contact_relationship,
                            "phone": emergency_contact_phone
                        },
                        "insurance_and_financial": {
                            "primary_insurance": {
                                "provider_name": primary_insurance_provider,
                                "policy_number": policy_number,
                                "group_number": group_number,
                                "subscriber_name": subscriber_name,
                                "subscriber_dob": subscriber_dob.isoformat() if subscriber_dob else None
                            },
                            "secondary_insurance": {
                                "has_secondary_insurance": (has_secondary_insurance == "Yes"),
                                "provider_name": secondary_insurance_provider if has_secondary_insurance == "Yes" else None,
                                "policy_number": secondary_policy_number if has_secondary_insurance == "Yes" else None
                            },
                            "reason_for_visit_brief": reason_for_visit_brief,
                            "financial_responsibility_acknowledged": financial_responsibility_ack
                        },
                        "medical_history_overview": {
                            "reason_for_appointment_full": reason_for_appointment_full,
                            "known_allergies": known_allergies,
                            "current_medications": current_medications,
                            "major_past_medical_conditions": major_past_medical_conditions,
                            "referring_physician": referring_physician
                        },
                        "appointment_details": {
                            "desired_appointment_date": desired_appointment_date.isoformat() if desired_appointment_date else None,
                            "desired_appointment_time": desired_appointment_time.isoformat() if desired_appointment_time else None,
                            "preferred_provider": preferred_provider,
                            "special_needs": special_needs
                        },
                        "legal_compliance": {
                            "consent_for_treatment_acknowledged": consent_treatment_ack,
                            "hipaa_privacy_acknowledged": hipaa_ack
                        }
                    }

                    st.success("Form submitted successfully! Here is the JSON payload:")
                    st.code(json.dumps(st.session_state.new_patient_info, indent=4), language='json')
                    st.write("The patient information is stored in the `st.session_state.new_patient_info` variable.")

                    st.markdown("---")
                    if st.button("Start Over", key="start_over_button_new"):
                        st.session_state.clear()
                        st.rerun()

    elif st.session_state.user_type_chosen == "Existing User":
        st.info("Thank you for being an existing patient! For existing patients, please contact our support team at 123-456-7890 or log in to your patient portal for appointment management.")
        if st.button("Go Back to User Type Selection", key="go_back_button_existing"):
            st.session_state.clear() # Clear all state to go back to initial choice
            st.rerun()


# Run the app
if __name__ == '__main__':
    app()

