import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import cv2
import numpy as np

#Created By Aayushi Gavhane 
# First Year 624
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Visibility of the interface
def apply_custom_css():
    st.markdown("""
    <style>
    /* We are keeping the header visible now so the sidebar arrow (>) appears! */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    div.stButton > button:first-child {
        background-color: #0068c9;
        color: white; border-radius: 8px; border: none;
        padding: 10px 24px; font-weight: bold; transition: 0.3s;
    }
    div.stButton > button:first-child:hover { background-color: #0052a3; }
    </style>
    """, unsafe_allow_html=True)
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Setting up database!! 
def init_db():
    conn = sqlite3.connect('hospital.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Patients (patient_id TEXT PRIMARY KEY, name TEXT, age INTEGER, gender TEXT, bed_number TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Prescriptions (id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, medicine TEXT, status TEXT, cost REAL, payment_status TEXT, timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Canteen_Logs (id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, meal_type TEXT, amount REAL, payment_status TEXT, timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Billing (patient_id TEXT PRIMARY KEY, canteen_total REAL, medicine_charges REAL, room_charges REAL, grand_total REAL, payment_status TEXT)''')
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect('hospital.db')
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# SMART QR SCANNER (NOW WITH AUTO-CLOSE CAMERA AND RESET BUTTON!)
def scan_or_enter_id(key_prefix):
    """Handles camera QR scanning, manual fallback, and auto-closes camera on success."""
    state_key = f"saved_id_{key_prefix}"
    cam_state = f"cam_open_{key_prefix}"

    # Setup memory for this specific tab
    if state_key not in st.session_state:
        st.session_state[state_key] = None
    if cam_state not in st.session_state:
        st.session_state[cam_state] = True # Camera is open by default

    # IF AN ID IS ALREADY SCANNED: Hide camera and show the ID!
    if st.session_state[state_key]:
        st.success(f" Active Patient ID: {st.session_state[state_key]}")
        # Button to clear the memory and scan the next patient
        if st.button("Scan Different Patient", key=f"reset_{key_prefix}"):
            st.session_state[state_key] = None
            st.session_state[cam_state] = True
            st.rerun() # Refresh the page instantly
        return st.session_state[state_key]

    # IF NO ID IS SCANNED YET: Show the manual box and camera
    col1, col2 = st.columns([3, 1])
    with col1:
        manual_id = st.text_input("Manual ID Entry (Fallback)", key=f"text_{key_prefix}")
    with col2:
        st.write("")
        st.write("")
        if st.button("Submit ID", key=f"btn_{key_prefix}"):
            if manual_id.strip() != "":
                st.session_state[state_key] = manual_id.strip()
                st.session_state[cam_state] = False
                st.rerun()
            else:
                st.warning("Please type an ID first.")

    # Only show camera if the state says it should be open
    if st.session_state[cam_state]:
        camera_image = st.camera_input("Or Scan QR Card here:", key=f"cam_{key_prefix}")
        
        if camera_image is not None:
            bytes_data = camera_image.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            val, _, _ = detector.detectAndDecode(cv2_img)
            
            if val: # IF QR IS FOUND!
                st.session_state[state_key] = val
                st.session_state[cam_state] = False # Turn off the camera!
                st.rerun() # Refresh the screen to hide it
            else:
                st.error("No QR detected in image. Please hold it steady.")
            
    return st.session_state[state_key]
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# INITIALIZATION the app
st.set_page_config(page_title="Smart Hospital System", layout="wide")
apply_custom_css()
init_db()

st.title(" Aarogya Digiward Hospital Management System")
role = st.sidebar.selectbox("Select Access Role", ["Patient", "Hospital Staff"])
conn = get_db_connection()
c = conn.cursor()
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# HOSPITAL STAFF INTERFACE:)

if role == "Hospital Staff":
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.subheader("Staff Login")
        pin = st.text_input("Enter Staff PIN (Type 1234)", type="password")
        if st.button("Login"):
            if pin == "1234":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect PIN:()")
    
    if st.session_state.authenticated:
        st.sidebar.success("Logged in as Staff:)")
        menu = st.sidebar.radio("Staff Portals", ["1. Registration", "2. Doctor's Tab", "3. Pharmacy", "4. Nurse's Tab", "5. Canteen", "6. Discharge"])
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------      
        # 1. REGISTRATION
        if menu == "1. Registration":
            st.header("Admit or Re-Admit a Patient")
            col1, col2 = st.columns(2)
            with col1:
                patient_id = st.text_input("Patient ID (for eg- P001)")
                name = st.text_input("Patient Name")
                age = st.number_input("Age", min_value=0, max_value=120, step=1)
            with col2:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                bed_number = st.text_input("Bed Number (e.g- Ward A - Bed 04)")
            
            if st.button("Admit / Re-Admit Patient"):
                if patient_id.strip() != "":
                    c.execute("SELECT status FROM Patients WHERE patient_id=?", (patient_id,))
                    existing_patient = c.fetchone()
                    
                    if existing_patient:
                        if existing_patient[0] == 'Discharged':
                            c.execute("UPDATE Patients SET status='Active', bed_number=? WHERE patient_id=?", (bed_number, patient_id))
                            conn.commit()
                            st.success(f"Welcome back! Patient {patient_id} has been re-admitted to {bed_number}. Old records saved to history!")
                        else:
                            st.error("This Patient ID is already active in the hospital!")
                    else:
                        c.execute("INSERT INTO Patients (patient_id, name, age, gender, bed_number, status) VALUES (?, ?, ?, ?, ?, 'Active')", 
                                  (patient_id, name, age, gender, bed_number))
                        conn.commit()
                        st.success(f"Patient admitted! You can now generate a QR code for ID: {patient_id}.")
                else:
                    st.warning("Please enter a Patient ID.")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # 2. DOCTOR'S TAB:)
        elif menu == "2. Doctor's Tab":
            st.header("Doctor's Portal: Digital Prescriptions")
            patient_id = scan_or_enter_id("doc")
            
            if patient_id:
                c.execute("SELECT name, bed_number, status FROM Patients WHERE patient_id=?", (patient_id,))
                patient = c.fetchone()
                if patient and patient[2] == 'Active':
                    st.info(f"**Patient:** {patient[0]} | **Bed:** {patient[1]}")
                    medicine = st.text_area("Prescribe Medicines & Dosage Instructions")
                    if st.button("Submit Prescription"):
                        if medicine.strip() == "":
                            st.warning("Please type a medicine before submitting!")
                        else:
                            timestamp = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("INSERT INTO Prescriptions (patient_id, medicine, status, cost, payment_status, timestamp) VALUES (?, ?, 'Pending at Pharmacy', 0.0, 'Unpaid', ?)", 
                                      (patient_id, medicine, timestamp))
                            conn.commit()
                            st.success("Prescription sent directly to Pharmacy.")
                else:
                    st.error("Patient not found or already discharged.")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # 3. PHARMACY TAB 
        elif menu == "3. Pharmacy":
            st.header("Pharmacy Portal")
            df = pd.read_sql_query("SELECT id, patient_id, medicine, timestamp FROM Prescriptions WHERE status='Pending at Pharmacy'", conn)
            if df.empty:
                st.success("No pending prescriptions.")
            else:
                st.dataframe(df, use_container_width=True)
                presc_id = st.number_input("Enter Prescription ID to mark as Ready", min_value=0, step=1)
                med_cost = st.number_input("Enter Medicine Cost (in Rs) to add to Bill", min_value=0.0, step=10.0)
                
                if st.button("Mark as Dispensed & Add to Bill"):
                    if presc_id in df['id'].values:
                        c.execute("UPDATE Prescriptions SET status='Dispensed to Ward', cost=? WHERE id=?", (med_cost, presc_id))
                        conn.commit()
                        st.success(f"Prescription #{presc_id} ready for nurses. Rs {med_cost} added to patient bill!")
                    else:
                        st.error("Invalid ID! Please enter an ID from the table above.")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # 4. NURSE'S TAB
        elif menu == "4. Nurse's Tab":
            st.header("Nurse's Station Dashboard")
            st.subheader(" THe Live IV Saline Drops Monitoring;)")
            st.warning(" **Hardware Alert from Bed 04:** Saline Level Low! Immediate replacement required.")
            st.divider()
            
            st.subheader("Administer Medications")
            patient_id = scan_or_enter_id("nurse")
            
            if patient_id:
                df = pd.read_sql_query(f"SELECT id, medicine, status, timestamp FROM Prescriptions WHERE patient_id='{patient_id}' AND status='Dispensed to Ward'", conn)
                if df.empty:
                    st.success("No pending medications for this patient.")
                else:
                    st.dataframe(df, use_container_width=True)
                    presc_id = st.number_input("Enter Prescription ID to administer", min_value=0, step=1)
                    if st.button("Mark Medicine as Given"):
                        if presc_id in df['id'].values:
                            c.execute("UPDATE Prescriptions SET status='Given' WHERE id=?", (presc_id,))
                            conn.commit()
                            st.success("Medication successfully administered.")
                        else:
                            st.error("Invalid ID! Please enter an ID from the table above.")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # 5. CANTEEN TAB
        elif menu == "5. Canteen":
            st.header("Canteen Portal")
            patient_id = scan_or_enter_id("canteen")
            if patient_id:
                c.execute("SELECT status FROM Patients WHERE patient_id=?", (patient_id,))
                status = c.fetchone()
                if status and status[0] == 'Active':
                    meal_type = st.selectbox("Meal Type", ["Morning", "Afternoon", "Night", "Snacks:)"])
                    amount = st.number_input("Amount (in Rs)", min_value=0.0, step=10.0)
                    if st.button("Add to Running Tab"):
                        timestamp = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("INSERT INTO Canteen_Logs (patient_id, meal_type, amount, payment_status, timestamp) VALUES (?, ?, ?, 'Unpaid', ?)", 
                                  (patient_id, meal_type, amount, timestamp))
                        conn.commit()
                        st.success("Meal logged and added to bill.")
                else:
                    st.error("Cannot add food. Patient is discharged or invalid.")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # 6. DISCHARGE TAB 
        elif menu == "6. Discharge":
            st.header("Discharge & Final Billing")
            patient_id = scan_or_enter_id("discharge")
            if patient_id:
                c.execute("SELECT status FROM Patients WHERE patient_id=?", (patient_id,))
                status = c.fetchone()
                if status and status[0] == 'Active':
                    
                    # Fetching only UNPAID logs for the current visit
                    c.execute("SELECT SUM(amount) FROM Canteen_Logs WHERE patient_id=? AND payment_status='Unpaid'", (patient_id,))
                    canteen_total = c.fetchone()[0] or 0.0
                    
                    c.execute("SELECT SUM(cost) FROM Prescriptions WHERE patient_id=? AND payment_status='Unpaid'", (patient_id,))
                    medicine_charges = c.fetchone()[0] or 0.0
                    
                    st.write(f"**Automated Pharmacy Charges:** Rs {medicine_charges}")
                    st.write(f"**Automated Canteen Charges:** Rs {canteen_total}")
                    
                    room_charges = st.number_input("Room & Consultation Charges (Rs)", min_value=0.0, step=100.0)
                    grand_total = canteen_total + medicine_charges + room_charges
                    
                    st.error(f"### Grand Total Due: Rs {grand_total}")
                    if st.button("Process Payment & Discharge"):
                        c.execute('''INSERT OR REPLACE INTO Billing (patient_id, canteen_total, medicine_charges, room_charges, grand_total, payment_status) VALUES (?, ?, ?, ?, ?, 'Paid')''', (patient_id, canteen_total, medicine_charges, room_charges, grand_total))
                        c.execute("UPDATE Patients SET status='Discharged' WHERE patient_id=?", (patient_id,))
                        
                        # Mark all current items as paid so they go to history
                        c.execute("UPDATE Canteen_Logs SET payment_status='Paid' WHERE patient_id=?", (patient_id,))
                        c.execute("UPDATE Prescriptions SET payment_status='Paid' WHERE patient_id=?", (patient_id,))
                        
                        conn.commit()
                        st.success("Patient successfully discharged!:)")
                else:
                    st.info("This patient has already been discharged.")
            else:
                st.error("Patient not found.")
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# PATIENT INTERFACE

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
elif role == "Patient":
    st.header("Digital Patient Card")
    patient_id = scan_or_enter_id("patient")
    
    if patient_id:
        c.execute("SELECT name, bed_number, status FROM Patients WHERE patient_id=?", (patient_id,))
        patient = c.fetchone()
        
        if patient:
            st.subheader(f"Welcome, {patient[0]}")
            st.caption(f"Status: {patient[2]}")
            st.divider()
            
            if patient[2] == 'Discharged':
                st.error("## Discharge Complete:)")
                bill_df = pd.read_sql_query("SELECT * FROM Billing WHERE patient_id=?", conn, params=(patient_id,))
                if not bill_df.empty:
                    bill = bill_df.iloc[0]
                    st.markdown(f"""
                    * Room & Consultations: Rs {bill['room_charges']}
                    * Pharmacy & Labs: Rs {bill['medicine_charges']}
                    * Canteen: Rs {bill['canteen_total']}
                    ### **Total Paid: Rs {bill['grand_total']}**
                    """)
                st.divider()
            
            tab1, tab2, tab3 = st.tabs(["Current Medications", "Visit History", "Current Canteen Tab"])
            
            with tab1:
                st.write("### Active Visit Medicines")
                med_df = pd.read_sql_query("SELECT medicine, status, cost, timestamp FROM Prescriptions WHERE patient_id=? AND payment_status='Unpaid'", conn, params=(patient_id,))
                if med_df.empty:
                    st.success("No active prescriptions.")
                else:
                    st.dataframe(med_df, use_container_width=True)
                    
            with tab2:
                st.write("### Past Visit History (Secure EHR)")
                past_meds = pd.read_sql_query("SELECT medicine, timestamp FROM Prescriptions WHERE patient_id=? AND payment_status='Paid'", conn, params=(patient_id,))
                if not past_meds.empty:
                    st.write("**Past Medications:**")
                    st.dataframe(past_meds, use_container_width=True)
                else:
                    st.write("No previous medical history on file.")
                    
            with tab3:
                st.write("### Active Visit Canteen")
                canteen_df = pd.read_sql_query("SELECT meal_type, amount, timestamp FROM Canteen_Logs WHERE patient_id=? AND payment_status='Unpaid'", conn, params=(patient_id,))
                st.dataframe(canteen_df, use_container_width=True)
                if not canteen_df.empty and patient[2] == 'Active':
                    st.warning(f"**Current Canteen Due: Rs {canteen_df['amount'].sum()}**")
        else:
            st.error("Patient ID not found.")

conn.close()