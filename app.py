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
    if 'current_form_section' not in st.session_state: # New state for current form section
        st.session_state.current_form_section = None # Will be set after user type and NPP


    # --- Step 1: Choose User Role ---
    if st.session_state.user_type_chosen is None:
        st.write("Welcome! Are you a new or existing patient?")
        
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
                    if user_choice == "New User":
                        st.session_state.current_form_section = "display_npp" # Start with NPP for new users
                    st.rerun() # Rerun to display next state

    # --- Display Content Based on Role ---
    elif st.session_state.user_type_chosen == "New User":
        # --- Section: Display NPP and Get Confirmation ---
        if not st.session_state.npp_agreed:
            st.header("Notice of Privacy Practices (NPP)")
            st.write("Please review our Notice of Privacy Practices. You must agree to proceed with your pre-appointment registration.")

            npp_content = ""
            npp_file_path = "npp.md"
            if os.path.exists(npp_file_path):
                try:
                    with open(npp_file_path, "r", encoding="utf-8") as f:
                        npp_content = f.read()
                    st.markdown(npp_content, unsafe_allow_html=True)
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
                            st.session_state.current_form_section = "demographics_1" # Move to first form section
                            st.rerun()
                        else:
                            st.error("You must agree to the NPP to proceed with registration.")
                with col_npp_buttons[1]:
                    if st.form_submit_button("Go Back to User Type Selection"):
                        st.session_state.clear()
                        st.rerun()

        # --- Multi-section form begins here (only if NPP is agreed) ---
        else:
            st.write("Please fill out the following details for your first-time appointment, section by section.")

            # Demographics Part 1
            if st.session_state.current_form_section == "demographics_1":
                st.header("1. Patient Demographics & Contact Information (1/3)")
                with st.form(key='form_demographics_1'):
                    patient_name = st.text_input("Full Legal Name*", value=st.session_state.new_patient_info.get("patient_demographics", {}).get("full_legal_name", ""), key="np_patient_name")
                    patient_dob = st.date_input("Date of Birth*", min_value=date(1900, 1, 1), max_value=date.today(), value=st.session_state.new_patient_info.get("patient_demographics", {}).get("date_of_birth", date.today()), key="np_patient_dob")
                    patient_phone = st.text_input("Phone Number*", value=st.session_state.new_patient_info.get("patient_demographics", {}).get("phone_number", ""), key="np_patient_phone")
                    patient_email = st.text_input("Email Address*", value=st.session_state.new_patient_info.get("patient_demographics", {}).get("email_address", ""), key="np_patient_email")

                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        if st.form_submit_button("Next"):
                            if patient_name and patient_dob and patient_phone and patient_email:
                                st.session_state.new_patient_info.setdefault("patient_demographics", {})
                                st.session_state.new_patient_info["patient_demographics"]["full_legal_name"] = patient_name
                                st.session_state.new_patient_info["patient_demographics"]["date_of_birth"] = patient_dob.isoformat()
                                st.session_state.new_patient_info["patient_demographics"]["phone_number"] = patient_phone
                                st.session_state.new_patient_info["patient_demographics"]["email_address"] = patient_email
                                st.session_state.current_form_section = "demographics_2"
                                st.rerun()
                            else:
                                st.error("Please fill in all required fields.")
                    with col_buttons[1]:
                        if st.form_submit_button("Back to NPP"):
                            st.session_state.npp_agreed = False # Go back to NPP screen
                            st.rerun()

            # Demographics Part 2
            elif st.session_state.current_form_section == "demographics_2":
                st.header("1. Patient Demographics & Contact Information (2/3)")
                with st.form(key='form_demographics_2'):
                    gender_options = ["Select", "Male", "Female", "Non-binary", "Prefer not to say"]
                    current_gender = st.session_state.new_patient_info.get("patient_demographics", {}).get("gender", "Select")
                    current_gender_index = gender_options.index(current_gender) if current_gender in gender_options else 0
                    patient_gender = st.selectbox("Gender*", gender_options, index=current_gender_index, key="np_patient_gender")
                    patient_address = st.text_area("Current Address", value=st.session_state.new_patient_info.get("patient_demographics", {}).get("address", ""), key="np_patient_address")
                    preferred_language = st.text_input("Preferred Language", value=st.session_state.new_patient_info.get("patient_demographics", {}).get("preferred_language", "English"), key="np_preferred_language")

                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        if st.form_submit_button("Next"):
                            if patient_gender != "Select":
                                st.session_state.new_patient_info["patient_demographics"]["gender"] = patient_gender
                                st.session_state.new_patient_info["patient_demographics"]["address"] = patient_address
                                st.session_state.new_patient_info["patient_demographics"]["preferred_language"] = preferred_language
                                st.session_state.current_form_section = "emergency_contact"
                                st.rerun()
                            else:
                                st.error("Please select your gender.")
                    with col_buttons[1]:
                        if st.form_submit_button("Back"):
                            st.session_state.current_form_section = "demographics_1"
                            st.rerun()

            # Emergency Contact
            elif st.session_state.current_form_section == "emergency_contact":
                st.header("1. Patient Demographics & Contact Information (3/3 - Emergency Contact)")
                with st.form(key='form_emergency_contact'):
                    emergency_contact_name = st.text_input("Emergency Contact's Name", value=st.session_state.new_patient_info.get("emergency_contact", {}).get("name", ""), key="np_ec_name")
                    emergency_contact_relationship = st.text_input("Relationship to Patient", value=st.session_state.new_patient_info.get("emergency_contact", {}).get("relationship", ""), key="np_ec_relationship")
                    emergency_contact_phone = st.text_input("Emergency Contact's Phone", value=st.session_state.new_patient_info.get("emergency_contact", {}).get("phone", ""), key="np_ec_phone")

                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        if st.form_submit_button("Next"):
                            st.session_state.new_patient_info.setdefault("emergency_contact", {})
                            st.session_state.new_patient_info["emergency_contact"]["name"] = emergency_contact_name
                            st.session_state.new_patient_info["emergency_contact"]["relationship"] = emergency_contact_relationship
                            st.session_state.new_patient_info["emergency_contact"]["phone"] = emergency_contact_phone
                            st.session_state.current_form_section = "insurance_1"
                            st.rerun()
                    with col_buttons[1]:
                        if st.form_submit_button("Back"):
                            st.session_state.current_form_section = "demographics_2"
                            st.rerun()

            # Insurance Part 1
            elif st.session_state.current_form_section == "insurance_1":
                st.header("2. Insurance & Financial Information (1/2 - Primary Insurance)")
                with st.form(key='form_insurance_1'):
                    primary_insurance_provider = st.text_input("Primary Insurance Provider Name*", value=st.session_state.new_patient_info.get("insurance_and_financial", {}).get("primary_insurance", {}).get("provider_name", ""), key="np_pi_provider")
                    policy_number = st.text_input("Policy Number*", value=st.session_state.new_patient_info.get("insurance_and_financial", {}).get("primary_insurance", {}).get("policy_number", ""), key="np_pi_policy")
                    group_number = st.text_input("Group Number (if applicable)", value=st.session_state.new_patient_info.get("insurance_and_financial", {}).get("primary_insurance", {}).get("group_number", ""), key="np_pi_group")
                    subscriber_name = st.text_input("Subscriber Name (if different)", value=st.session_state.new_patient_info.get("insurance_and_financial", {}).get("primary_insurance", {}).get("subscriber_name", ""), key="np_pi_subscriber_name")
                    subscriber_dob_val = None
                    if st.session_state.new_patient_info.get("insurance_and_financial", {}).get("primary_insurance", {}).get("subscriber_dob"):
                        try:
                            subscriber_dob_val = date.fromisoformat(st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["subscriber_dob"])
                        except ValueError:
                            subscriber_dob_val = None
                    subscriber_dob = st.date_input("Subscriber Date of Birth (if different)", min_value=date(1900, 1, 1), max_value=date.today(), value=subscriber_dob_val, key="np_pi_subscriber_dob")

                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        if st.form_submit_button("Next"):
                            if primary_insurance_provider and policy_number:
                                st.session_state.new_patient_info.setdefault("insurance_and_financial", {}).setdefault("primary_insurance", {})
                                st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["provider_name"] = primary_insurance_provider
                                st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["policy_number"] = policy_number
                                st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["group_number"] = group_number
                                st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["subscriber_name"] = subscriber_name
                                st.session_state.new_patient_info["insurance_and_financial"]["primary_insurance"]["subscriber_dob"] = subscriber_dob.isoformat() if subscriber_dob else None
                                st.session_state.current_form_section = "insurance_2"
                                st.rerun()
                            else:
                                st.error("Please provide your Primary Insurance Provider Name and Policy Number.")
                    with col_buttons[1]:
                        if st.form_submit_button("Back"):
                            st.session_state.current_form_section = "emergency_contact"
                            st.rerun()

            # Insurance Part 2
            elif st.session_state.current_form_section == "insurance_2":
                st.header("2. Insurance & Financial Information (2/2)")
                with st.form(key='form_insurance_2'):
                    has_secondary_insurance_val = st.session_state.new_patient_info.get("insurance_and_financial", {}).get("secondary_insurance", {}).get("has_secondary_insurance", False)
                    has_secondary_insurance_index = 1 if has_secondary_insurance_val else 0
                    has_secondary_insurance = st.radio(
                        "Do you have secondary insurance?",
                        ("No", "Yes"),
                        index=has_secondary_insurance_index,
                        key="np_secondary_insurance_radio"
                    )
                    secondary_insurance_provider = st.session_state.new_patient_info.get("insurance_and_financial", {}).get("secondary_insurance", {}).get("provider_name", "")
                    secondary_policy_number = st.session_state.new_patient_info.get("insurance_and_financial", {}).get("secondary_insurance", {}).get("policy_number", "")
                    
                    if has_secondary_insurance == "Yes":
                        secondary_insurance_provider = st.text_input("Secondary Insurance Provider Name", value=secondary_insurance_provider, key="np_si_provider")
                        secondary_policy_number = st.text_input("Secondary Policy Number", value=secondary_policy_number, key="np_si_policy")

                    reason_for_visit_brief = st.text_area("Brief Reason for Visit*", value=st.session_state.new_patient_info.get("insurance_and_financial", {}).get("reason_for_visit_brief", ""), help="e.g., 'Routine check-up', 'Follow-up for blood pressure'", key="np_reason_brief")
                    financial_responsibility_ack = st.checkbox("I understand my financial responsibility (co-pays, deductibles, etc.)*", value=st.session_state.new_patient_info.get("insurance_and_financial", {}).get("financial_responsibility_acknowledged", False), key="np_financial_ack")

                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        if st.form_submit_button("Next"):
                            if reason_for_visit_brief and financial_responsibility_ack:
                                st.session_state.new_patient_info.setdefault("insurance_and_financial", {}).setdefault("secondary_insurance", {})
                                st.session_state.new_patient_info["insurance_and_financial"]["secondary_insurance"]["has_secondary_insurance"] = (has_secondary_insurance == "Yes")
                                st.session_state.new_patient_info["insurance_and_financial"]["secondary_insurance"]["provider_name"] = secondary_insurance_provider if has_secondary_insurance == "Yes" else None
                                st.session_state.new_patient_info["insurance_and_financial"]["secondary_insurance"]["policy_number"] = secondary_policy_number if has_secondary_insurance == "Yes" else None
                                st.session_state.new_patient_info["insurance_and_financial"]["reason_for_visit_brief"] = reason_for_visit_brief
                                st.session_state.new_patient_info["insurance_and_financial"]["financial_responsibility_acknowledged"] = financial_responsibility_ack
                                st.session_state.current_form_section = "medical_history_prompt"
                                st.rerun()
                            else:
                                st.error("Please provide a brief reason for visit and acknowledge financial responsibility.")
                    with col_buttons[1]:
                        if st.form_submit_button("Back"):
                            st.session_state.current_form_section = "insurance_1"
                            st.rerun()

            # Medical History Prompt
            elif st.session_state.current_form_section == "medical_history_prompt":
                st.header("3. Medical History (Initial Overview)")
                st.info("A detailed medical history will be collected during your appointment.")
                with st.form(key='form_medical_history_prompt'):
                    medical_history_opt_in = st.radio(
                        "Would you like to provide an initial overview of your medical history now?",
                        ("No", "Yes"),
                        index=1 if st.session_state.new_patient_info.get("medical_history_overview", {}).get("opt_in", False) else 0,
                        key="mh_opt_in_radio"
                    )
                    
                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        if st.form_submit_button("Next"):
                            st.session_state.new_patient_info.setdefault("medical_history_overview", {})["opt_in"] = (medical_history_opt_in == "Yes")
                            if medical_history_opt_in == "Yes":
                                st.session_state.current_form_section = "medical_history_details"
                            else:
                                st.session_state.current_form_section = "appointment_details"
                            st.rerun()
                    with col_buttons[1]:
                        if st.form_submit_button("Back"):
                            st.session_state.current_form_section = "insurance_2"
                            st.rerun()

            # Medical History Details
            elif st.session_state.current_form_section == "medical_history_details":
                st.header("3. Medical History (Details)")
                with st.form(key='form_medical_history_details'):
                    reason_for_appointment_full = st.text_area("Can you describe the Reason for your Appointment/Chief Complaint in more detail?", value=st.session_state.new_patient_info.get("medical_history_overview", {}).get("reason_for_appointment_full", ""), key="mh_full_reason")
                    known_allergies = st.text_area("Do you have any Known Allergies (e.g., medications, food, environmental)?", value=st.session_state.new_patient_info.get("medical_history_overview", {}).get("known_allergies", ""), key="mh_allergies")
                    current_medications = st.text_area("Please list your Current Medications (including OTC and supplements) and Dosages (e.g., 'Amlodipine 5mg daily')", value=st.session_state.new_patient_info.get("medical_history_overview", {}).get("current_medications", ""), key="mh_meds")
                    major_past_medical_conditions = st.text_area("Do you have any Major Past Medical Conditions/Diagnoses (e.g., 'Diabetes, Hypertension, Asthma')?", value=st.session_state.new_patient_info.get("medical_history_overview", {}).get("major_past_medical_conditions", ""), key="mh_conditions")
                    referring_physician = st.text_input("Is there a Referring Physician (name, if any)?", value=st.session_state.new_patient_info.get("medical_history_overview", {}).get("referring_physician", ""), key="mh_referring")

                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        if st.form_submit_button("Next"):
                            st.session_state.new_patient_info.setdefault("medical_history_overview", {})
                            st.session_state.new_patient_info["medical_history_overview"]["reason_for_appointment_full"] = reason_for_appointment_full
                            st.session_state.new_patient_info["medical_history_overview"]["known_allergies"] = known_allergies
                            st.session_state.new_patient_info["medical_history_overview"]["current_medications"] = current_medications
                            st.session_state.new_patient_info["medical_history_overview"]["major_past_medical_conditions"] = major_past_medical_conditions
                            st.session_state.new_patient_info["medical_history_overview"]["referring_physician"] = referring_physician
                            st.session_state.current_form_section = "appointment_details"
                            st.rerun()
                    with col_buttons[1]:
                        if st.form_submit_button("Back"):
                            st.session_state.current_form_section = "medical_history_prompt"
                            st.rerun()

            # Appointment Details
            elif st.session_state.current_form_section == "appointment_details":
                st.header("4. Appointment Details")
                with st.form(key='form_appointment_details'):
                    desired_app_date_val = st.session_state.new_patient_info.get("appointment_details", {}).get("desired_appointment_date")
                    if desired_app_date_val:
                        try: desired_app_date_val = date.fromisoformat(desired_app_date_val)
                        except ValueError: desired_app_date_val = date.today()
                    else: desired_app_date_val = date.today()

                    desired_appointment_date = st.date_input("Desired Appointment Date*", min_value=date.today(), value=desired_app_date_val, key="np_app_date")

                    desired_app_time_val = st.session_state.new_patient_info.get("appointment_details", {}).get("desired_appointment_time")
                    if desired_app_time_val:
                        try: desired_app_time_val = time.fromisoformat(desired_app_time_val)
                        except ValueError: desired_app_time_val = time(9,0)
                    else: desired_app_time_val = time(9,0)

                    desired_appointment_time = st.time_input("Desired Appointment Time*", value=desired_app_time_val, key="np_app_time")

                    preferred_provider = st.text_input("Preferred Provider (e.g., Dr. Smith)", value=st.session_state.new_patient_info.get("appointment_details", {}).get("preferred_provider", ""), key="np_app_provider")
                    special_needs = st.text_area("Any Special Needs (e.g., interpreter, wheelchair access)", value=st.session_state.new_patient_info.get("appointment_details", {}).get("special_needs", ""), key="np_app_special_needs")

                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        if st.form_submit_button("Next"):
                            if desired_appointment_date and desired_appointment_time:
                                st.session_state.new_patient_info.setdefault("appointment_details", {})
                                st.session_state.new_patient_info["appointment_details"]["desired_appointment_date"] = desired_appointment_date.isoformat()
                                st.session_state.new_patient_info["appointment_details"]["desired_appointment_time"] = desired_appointment_time.isoformat()
                                st.session_state.new_patient_info["appointment_details"]["preferred_provider"] = preferred_provider
                                st.session_state.new_patient_info["appointment_details"]["special_needs"] = special_needs
                                st.session_state.current_form_section = "legal_compliance"
                                st.rerun()
                            else:
                                st.error("Please provide your desired appointment date and time.")
                    with col_buttons[1]:
                        if st.form_submit_button("Back"):
                            if st.session_state.new_patient_info.get("medical_history_overview", {}).get("opt_in", False):
                                st.session_state.current_form_section = "medical_history_details"
                            else:
                                st.session_state.current_form_section = "medical_history_prompt"
                            st.rerun()

            # Legal & Compliance
            elif st.session_state.current_form_section == "legal_compliance":
                st.header("5. Legal & Compliance")
                st.write("Please review and acknowledge the following statements.")
                with st.form(key='form_legal_compliance'):
                    consent_treatment_ack = st.checkbox("I acknowledge initial consent for treatment (full consent upon arrival)*", value=st.session_state.new_patient_info.get("legal_compliance", {}).get("consent_for_treatment_acknowledged", False), key="np_lc_consent_ack")
                    hipaa_ack = st.checkbox("I acknowledge receipt and understanding of HIPAA Privacy Practices*", value=st.session_state.new_patient_info.get("legal_compliance", {}).get("hipaa_privacy_acknowledged", False), key="np_lc_hipaa_ack")

                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        if st.form_submit_button("Review & Submit"):
                            if consent_treatment_ack and hipaa_ack:
                                st.session_state.new_patient_info.setdefault("legal_compliance", {})
                                st.session_state.new_patient_info["legal_compliance"]["consent_for_treatment_acknowledged"] = consent_treatment_ack
                                st.session_state.new_patient_info["legal_compliance"]["hipaa_privacy_acknowledged"] = hipaa_ack
                                st.session_state.current_form_section = "summary"
                                st.rerun()
                            else:
                                st.error("Please acknowledge both statements to proceed.")
                    with col_buttons[1]:
                        if st.form_submit_button("Back"):
                            st.session_state.current_form_section = "appointment_details"
                            st.rerun()

            # Summary and Final Submission
            elif st.session_state.current_form_section == "summary":
                st.header("Summary of Your Information")
                st.write("Please review the details you've provided before final submission.")

                st.json(st.session_state.new_patient_info)

                col_buttons = st.columns(2)
                with col_buttons[0]:
                    if st.button("Submit Final Form"):
                        json_payload = json.dumps(st.session_state.new_patient_info, indent=4)
                        st.success("Form submitted successfully! Here is the JSON payload:")
                        st.code(json_payload, language='json')
                        st.write("The patient information is stored in the `st.session_state.new_patient_info` variable.")

                        st.markdown("---")
                        if st.button("Start Over", key="start_over_button_new"):
                            st.session_state.clear()
                            st.rerun()
                with col_buttons[1]:
                    if st.button("Back to Legal & Compliance"):
                        st.session_state.current_form_section = "legal_compliance"
                        st.rerun()

    elif st.session_state.user_type_chosen == "Existing User":
        st.info("Thank you for being an existing patient! For existing patients, please contact our support team at 123-456-7890 or log in to your patient portal for appointment management.")
        if st.button("Go Back to User Type Selection", key="go_back_button_existing"):
            st.session_state.clear() # Clear all state to go back to initial choice
            st.rerun()


if __name__ == '__main__':
    app()
