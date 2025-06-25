import streamlit as st
import json
from datetime import date, time

def app():
    st.set_page_config(
        page_title="RCM Healthcare Patient Pre-Appointment Chatbot",
        layout="centered",
        initial_sidebar_state="auto"
    )

    st.title("🏥 RCM Healthcare Patient Pre-Appointment Chatbot")

    # Initialize session state variables if they don't exist
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    if 'current_section' not in st.session_state:
        st.session_state.current_section = "welcome" # Initial state
    if 'patient_data' not in st.session_state:
        st.session_state.patient_data = {}
    if 'medical_history_opt_in' not in st.session_state:
        st.session_state.medical_history_opt_in = False

    # Function to navigate between sections
    def set_section(section_name):
        st.session_state.current_section = section_name
        st.rerun()

    # --- Welcome / User Type Selection ---
    if st.session_state.current_section == "welcome":
        st.write("Welcome! Are you a new or existing patient?")
        user_choice = st.radio(
            "Please select your patient status:",
            ("Select", "New User", "Existing User"),
            key="user_type_radio"
        )
        if user_choice == "New User":
            st.session_state.user_type = "New User"
            st.session_state.current_section = "demographics_1"
            st.rerun()
        elif user_choice == "Existing User":
            st.session_state.user_type = "Existing User"
            st.session_state.current_section = "existing_user_info"
            st.rerun()

    # --- Existing User Information ---
    elif st.session_state.current_section == "existing_user_info":
        st.info("Thank you for being an existing patient! For existing patients, please contact our support team at 123-456-7890 or log in to your patient portal for appointment management.")
        if st.button("Go Back to User Type Selection"):
            st.session_state.user_type = None
            st.session_state.current_section = "welcome"
            st.rerun()

    # --- New User Chatbot Flow ---
    elif st.session_state.user_type == "New User":
        st.write(
            "Let's get some details for your first-time appointment. "
            "This information will help us with pre-registration and insurance verification."
        )

        # --- Section: Demographics Part 1 (Name, DOB, Phone, Email) ---
        if st.session_state.current_section == "demographics_1":
            st.header("1. Patient Demographics & Contact Information (Part 1/3)")
            with st.form(key='demographics_1_form'):
                patient_name = st.text_input("What is your Full Legal Name?*", value=st.session_state.patient_data.get("full_legal_name", ""), key="d1_patient_name")
                patient_dob = st.date_input("What is your Date of Birth?*", min_value=date(1900, 1, 1), max_value=date.today(), value=st.session_state.patient_data.get("date_of_birth", date.today()), key="d1_patient_dob")
                patient_phone = st.text_input("What is your Phone Number?*", value=st.session_state.patient_data.get("phone_number", ""), key="d1_patient_phone")
                patient_email = st.text_input("What is your Email Address?*", value=st.session_state.patient_data.get("email_address", ""), key="d1_patient_email")

                col_buttons = st.columns(2)
                with col_buttons[0]:
                    if st.form_submit_button("Next"):
                        if patient_name and patient_dob and patient_phone and patient_email:
                            st.session_state.patient_data["full_legal_name"] = patient_name
                            st.session_state.patient_data["date_of_birth"] = patient_dob.isoformat()
                            st.session_state.patient_data["phone_number"] = patient_phone
                            st.session_state.patient_data["email_address"] = patient_email
                            set_section("demographics_2")
                        else:
                            st.error("Please fill in all required fields.")
                with col_buttons[1]:
                    if st.form_submit_button("Go Back"):
                        st.session_state.user_type = None
                        st.session_state.current_section = "welcome"
                        st.rerun()

        # --- Section: Demographics Part 2 (Gender, Address, Language) ---
        elif st.session_state.current_section == "demographics_2":
            st.header("1. Patient Demographics & Contact Information (Part 2/3)")
            with st.form(key='demographics_2_form'):
                # Find index of stored gender, default to 0 if not found
                gender_options = ["Select", "Male", "Female", "Non-binary", "Prefer not to say"]
                current_gender_index = gender_options.index(st.session_state.patient_data.get("gender", "Select")) if st.session_state.patient_data.get("gender") in gender_options else 0
                patient_gender = st.selectbox("What is your Gender?*", gender_options, index=current_gender_index, key="d2_patient_gender")
                patient_address = st.text_area("What is your Current Address?", value=st.session_state.patient_data.get("address", ""), key="d2_patient_address")
                preferred_language = st.text_input("What is your Preferred Language?", value=st.session_state.patient_data.get("preferred_language", "English"), key="d2_preferred_language")

                col_buttons = st.columns(2)
                with col_buttons[0]:
                    if st.form_submit_button("Next"):
                        if patient_gender != "Select":
                            st.session_state.patient_data["gender"] = patient_gender
                            st.session_state.patient_data["address"] = patient_address
                            st.session_state.patient_data["preferred_language"] = preferred_language
                            set_section("emergency_contact")
                        else:
                            st.error("Please select your gender.")
                with col_buttons[1]:
                    if st.form_submit_button("Go Back"):
                        set_section("demographics_1")

        # --- Section: Emergency Contact ---
        elif st.session_state.current_section == "emergency_contact":
            st.header("1. Patient Demographics & Contact Information (Part 3/3 - Emergency Contact)")
            with st.form(key='emergency_contact_form'):
                emergency_contact_name = st.text_input("What is your Emergency Contact's Name?", value=st.session_state.patient_data.get("emergency_contact", {}).get("name", ""), key="ec_name")
                emergency_contact_relationship = st.text_input("What is their Relationship to you?", value=st.session_state.patient_data.get("emergency_contact", {}).get("relationship", ""), key="ec_relationship")
                emergency_contact_phone = st.text_input("What is their Phone Number?", value=st.session_state.patient_data.get("emergency_contact", {}).get("phone", ""), key="ec_phone")

                col_buttons = st.columns(2)
                with col_buttons[0]:
                    if st.form_submit_button("Next"):
                        # No mandatory fields for emergency contact, just store
                        st.session_state.patient_data["emergency_contact"] = {
                            "name": emergency_contact_name,
                            "relationship": emergency_contact_relationship,
                            "phone": emergency_contact_phone
                        }
                        set_section("insurance_1")
                with col_buttons[1]:
                    if st.form_submit_button("Go Back"):
                        set_section("demographics_2")

        # --- Section: Insurance Part 1 (Primary Insurance) ---
        elif st.session_state.current_section == "insurance_1":
            st.header("2. Insurance & Financial Information (Part 1/2 - Primary Insurance)")
            with st.form(key='insurance_1_form'):
                primary_insurance_provider = st.text_input("What is the name of your Primary Insurance Provider?*", value=st.session_state.patient_data.get("primary_insurance", {}).get("provider_name", ""), key="i1_provider_name")
                policy_number = st.text_input("What is your Policy Number?*", value=st.session_state.patient_data.get("primary_insurance", {}).get("policy_number", ""), key="i1_policy_number")
                group_number = st.text_input("What is your Group Number (if applicable)?", value=st.session_state.patient_data.get("primary_insurance", {}).get("group_number", ""), key="i1_group_number")
                subscriber_name = st.text_input("What is the Subscriber's Name (if different from patient)?", value=st.session_state.patient_data.get("primary_insurance", {}).get("subscriber_name", ""), key="i1_subscriber_name")
                # Handle date input default value for subscriber DOB
                subscriber_dob_val = None
                if st.session_state.patient_data.get("primary_insurance", {}).get("subscriber_dob"):
                    try:
                        subscriber_dob_val = date.fromisoformat(st.session_state.patient_data["primary_insurance"]["subscriber_dob"])
                    except ValueError:
                        subscriber_dob_val = None # Handle invalid stored date
                subscriber_dob = st.date_input("What is the Subscriber's Date of Birth (if different)?", min_value=date(1900, 1, 1), max_value=date.today(), value=subscriber_dob_val, key="i1_subscriber_dob")


                col_buttons = st.columns(2)
                with col_buttons[0]:
                    if st.form_submit_button("Next"):
                        if primary_insurance_provider and policy_number:
                            st.session_state.patient_data["primary_insurance"] = {
                                "provider_name": primary_insurance_provider,
                                "policy_number": policy_number,
                                "group_number": group_number,
                                "subscriber_name": subscriber_name,
                                "subscriber_dob": subscriber_dob.isoformat() if subscriber_dob else None
                            }
                            set_section("insurance_2")
                        else:
                            st.error("Please provide your Primary Insurance Provider Name and Policy Number.")
                with col_buttons[1]:
                    if st.form_submit_button("Go Back"):
                        set_section("emergency_contact")

        # --- Section: Insurance Part 2 (Secondary Insurance, Reason for Visit, Financial Ack) ---
        elif st.session_state.current_section == "insurance_2":
            st.header("2. Insurance & Financial Information (Part 2/2)")
            with st.form(key='insurance_2_form'):
                has_secondary_insurance_val = st.session_state.patient_data.get("secondary_insurance", {}).get("has_secondary_insurance", False)
                has_secondary_insurance_index = 1 if has_secondary_insurance_val else 0 # 0 for "No", 1 for "Yes"
                has_secondary_insurance = st.radio(
                    "Do you have secondary insurance?",
                    ("No", "Yes"),
                    index=has_secondary_insurance_index,
                    key="i2_secondary_insurance_radio"
                )
                secondary_insurance_provider = ""
                secondary_policy_number = ""
                if has_secondary_insurance == "Yes":
                    secondary_insurance_provider = st.text_input("Secondary Insurance Provider Name", value=st.session_state.patient_data.get("secondary_insurance", {}).get("provider_name", ""), key="i2_secondary_provider")
                    secondary_policy_number = st.text_input("Secondary Policy Number", value=st.session_state.patient_data.get("secondary_insurance", {}).get("policy_number", ""), key="i2_secondary_policy")

                reason_for_visit_brief = st.text_area("Briefly, what is the main Reason for your Visit?*", value=st.session_state.patient_data.get("reason_for_visit_brief", ""), help="e.g., 'Routine check-up', 'New patient consultation for back pain'", key="i2_reason_brief")
                financial_responsibility_ack = st.checkbox("I understand my financial responsibility (co-pays, deductibles, etc.)*", value=st.session_state.patient_data.get("financial_responsibility_acknowledged", False), key="i2_financial_ack")

                col_buttons = st.columns(2)
                with col_buttons[0]:
                    if st.form_submit_button("Next"):
                        if reason_for_visit_brief and financial_responsibility_ack:
                            st.session_state.patient_data["secondary_insurance"] = {
                                "has_secondary_insurance": (has_secondary_insurance == "Yes"),
                                "provider_name": secondary_insurance_provider if has_secondary_insurance == "Yes" else None,
                                "policy_number": secondary_policy_number if has_secondary_insurance == "Yes" else None
                            }
                            st.session_state.patient_data["reason_for_visit_brief"] = reason_for_visit_brief
                            st.session_state.patient_data["financial_responsibility_acknowledged"] = financial_responsibility_ack
                            set_section("medical_history_prompt")
                        else:
                            st.error("Please provide a brief reason for visit and acknowledge financial responsibility.")
                with col_buttons[1]:
                    if st.form_submit_button("Go Back"):
                        set_section("insurance_1")

        # --- Section: Medical History Prompt ---
        elif st.session_state.current_section == "medical_history_prompt":
            st.header("3. Medical History (Initial Overview)")
            st.info("A detailed medical history will be collected during your appointment.")
            with st.form(key='medical_history_prompt_form'):
                medical_history_opt_in = st.radio(
                    "Would you like to provide an initial overview of your medical history now?",
                    ("No", "Yes"),
                    index=1 if st.session_state.medical_history_opt_in else 0, # Set default based on session state
                    key="mh_opt_in_radio"
                )
                col_buttons = st.columns(2)
                with col_buttons[0]:
                    if st.form_submit_button("Next"):
                        st.session_state.medical_history_opt_in = (medical_history_opt_in == "Yes")
                        if medical_history_opt_in == "Yes":
                            set_section("medical_history_details")
                        else:
                            set_section("appointment_details")
                with col_buttons[1]:
                    if st.form_submit_button("Go Back"):
                        set_section("insurance_2")

        # --- Section: Medical History Details ---
        elif st.session_state.current_section == "medical_history_details":
            st.header("3. Medical History (Details)")
            with st.form(key='medical_history_details_form'):
                reason_for_appointment_full = st.text_area("Can you describe the Reason for your Appointment/Chief Complaint in more detail?", value=st.session_state.patient_data.get("medical_history_overview", {}).get("reason_for_appointment_full", ""), key="mh_full_reason")
                known_allergies = st.text_area("Do you have any Known Allergies (e.g., medications, food, environmental)?", value=st.session_state.patient_data.get("medical_history_overview", {}).get("known_allergies", ""), key="mh_allergies")
                current_medications = st.text_area("Please list your Current Medications (including OTC and supplements) and Dosages (e.g., 'Amlodipine 5mg daily')", value=st.session_state.patient_data.get("medical_history_overview", {}).get("current_medications", ""), key="mh_meds")
                major_past_medical_conditions = st.text_area("Do you have any Major Past Medical Conditions/Diagnoses (e.g., 'Diabetes, Hypertension, Asthma')?", value=st.session_state.patient_data.get("medical_history_overview", {}).get("major_past_medical_conditions", ""), key="mh_conditions")
                referring_physician = st.text_input("Is there a Referring Physician (name, if any)?", value=st.session_state.patient_data.get("medical_history_overview", {}).get("referring_physician", ""), key="mh_referring")

                col_buttons = st.columns(2)
                with col_buttons[0]:
                    if st.form_submit_button("Next"):
                        st.session_state.patient_data["medical_history_overview"] = {
                            "reason_for_appointment_full": reason_for_appointment_full,
                            "known_allergies": known_allergies,
                            "current_medications": current_medications,
                            "major_past_medical_conditions": major_past_medical_conditions,
                            "referring_physician": referring_physician
                        }
                        set_section("appointment_details")
                with col_buttons[1]:
                    if st.form_submit_button("Go Back"):
                        set_section("medical_history_prompt")

        # --- Section: Appointment Details ---
        elif st.session_state.current_section == "appointment_details":
            st.header("4. Appointment Details")
            with st.form(key='appointment_details_form'):
                # Handle date input default value for desired appointment date
                desired_app_date_val = None
                if st.session_state.patient_data.get("desired_appointment_date"):
                    try:
                        desired_app_date_val = date.fromisoformat(st.session_state.patient_data["desired_appointment_date"])
                    except ValueError:
                        desired_app_date_val = date.today() # Fallback
                desired_appointment_date = st.date_input("What is your Desired Appointment Date?*", min_value=date.today(), value=desired_app_date_val or date.today(), key="ad_date")

                # Handle time input default value for desired appointment time
                desired_app_time_val = None
                if st.session_state.patient_data.get("desired_appointment_time"):
                    try:
                        # Streamlit's time_input returns datetime.time, so convert from ISO string
                        time_str = st.session_state.patient_data["desired_appointment_time"]
                        desired_app_time_val = time.fromisoformat(time_str)
                    except ValueError:
                        desired_app_time_val = time(9,0) # Fallback
                desired_appointment_time = st.time_input("What is your Desired Appointment Time?*", value=desired_app_time_val or time(9, 0), key="ad_time")

                preferred_provider = st.text_input("Do you have a Preferred Provider (e.g., Dr. Smith)?", value=st.session_state.patient_data.get("preferred_provider", ""), key="ad_provider")
                special_needs = st.text_area("Do you have any Special Needs (e.g., interpreter, wheelchair access)?", value=st.session_state.patient_data.get("special_needs", ""), key="ad_special_needs")

                col_buttons = st.columns(2)
                with col_buttons[0]:
                    if st.form_submit_button("Next"):
                        if desired_appointment_date and desired_appointment_time:
                            st.session_state.patient_data["desired_appointment_date"] = desired_appointment_date.isoformat()
                            st.session_state.patient_data["desired_appointment_time"] = desired_appointment_time.isoformat()
                            st.session_state.patient_data["preferred_provider"] = preferred_provider
                            st.session_state.patient_data["special_needs"] = special_needs
                            set_section("legal_compliance")
                        else:
                            st.error("Please provide your desired appointment date and time.")
                with col_buttons[1]:
                    if st.form_submit_button("Go Back"):
                        if st.session_state.medical_history_opt_in:
                            set_section("medical_history_details")
                        else:
                            set_section("medical_history_prompt")

        # --- Section: Legal & Compliance ---
        elif st.session_state.current_section == "legal_compliance":
            st.header("5. Legal & Compliance")
            st.write("Please review and acknowledge the following statements.")
            with st.form(key='legal_compliance_form'):
                consent_treatment_ack = st.checkbox("I acknowledge initial consent for treatment (full consent upon arrival)*", value=st.session_state.patient_data.get("consent_for_treatment_acknowledged", False), key="lc_consent_ack")
                hipaa_ack = st.checkbox("I acknowledge receipt and understanding of HIPAA Privacy Practices*", value=st.session_state.patient_data.get("hipaa_privacy_acknowledged", False), key="lc_hipaa_ack")

                col_buttons = st.columns(2)
                with col_buttons[0]:
                    if st.form_submit_button("Review & Submit"):
                        if consent_treatment_ack and hipaa_ack:
                            st.session_state.patient_data["consent_for_treatment_acknowledged"] = consent_treatment_ack
                            st.session_state.patient_data["hipaa_privacy_acknowledged"] = hipaa_ack
                            set_section("summary")
                        else:
                            st.error("Please acknowledge both statements to proceed.")
                with col_buttons[1]:
                    if st.form_submit_button("Go Back"):
                        set_section("appointment_details")

        # --- Section: Summary and Final Submission ---
        elif st.session_state.current_section == "summary":
            st.header("Summary of Your Information")
            st.write("Please review the details you've provided before final submission.")

            # Display collected data for review
            st.json(st.session_state.patient_data)

            col_buttons = st.columns(2)
            with col_buttons[0]:
                if st.button("Submit Final Form"):
                    # Convert collected data to JSON string
                    json_payload = json.dumps(st.session_state.patient_data, indent=4)
                    st.success("Form submitted successfully! Here is the JSON payload:")
                    st.code(json_payload, language='json')

                    st.write("---")
                    st.subheader("Next Steps for Integration:")
                    st.write(
                        "In a real application, you would send this `json_payload` to your backend server "
                        "via an API endpoint (e.g., using a `requests.post` call in Python or `fetch` API in JavaScript)."
                        "Below is a conceptual Python example:"
                    )
                    st.markdown(
                        """
                        ```python
                        # Example of how you might send this payload to a backend (Python, requires 'requests' library)
                        # import requests

                        # backend_url = "YOUR_BACKEND_API_ENDPOINT" # Replace with your actual backend URL, e.g., "[https://api.yourhealthcare.com/patient-appointments](https://api.yourhealthcare.com/patient-appointments)"

                        # try:
                        #     response = requests.post(backend_url, json=payload_data)
                        #     response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                        #     st.success(f"Payload successfully sent to backend! Status Code: {response.status_code}")
                        #     # You can also display the backend's response JSON if available
                        #     # st.json(response.json())
                        # except requests.exceptions.RequestException as e:
                        #     st.error(f"Failed to send payload to backend: {e}")
                        ```
                        """
                    )
                    st.write("---")
                    if st.button("Start Over"):
                        st.session_state.clear()
                        st.rerun()
            with col_buttons[1]:
                if st.button("Go Back to Appointment Details"):
                    set_section("legal_compliance")

# Ensure the app runs when the script is executed
if __name__ == '__main__':
    app()