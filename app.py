import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 1. SET PAGE CONFIG & TCP THEME DESIGN (CSS)
# ==========================================
st.set_page_config(
    page_title="TCP Inbound Delivery Management",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS เพื่อปรับแต่งธีมให้เป็นสีของ TCP Group (Deep Blue, Red, White)
st.markdown("""
    <style>
    /* แถบด้านบนและสีหลัก */
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #002D62 !important; /* TCP Deep Blue */
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    /* ปุ่ม Submit สีแดง TCP */
    div.stButton > button:first-child {
        background-color: #D22630; /* TCP Red */
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #A01C24;
        color: white;
    }
    /* กล่องข้อความต้อนรับ */
    .welcome-box {
        padding: 15px;
        background-color: #F0F4F8;
        border-left: 5px solid #002D62;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_index=True)

# ==========================================
# 2. STATE MANAGEMENT (จำลองฐานข้อมูล SharePoint)
# ==========================================
# ใช้ Session State ของ Streamlit ในการจำลองฐานข้อมูลชั่วคราวเพื่อให้รันบน Colab/Web ได้ทันที
if 'user_db' not in st.session_state:
    st.session_state.user_db = pd.DataFrame([
        {"email": "admin@tcp.com", "password": "password123", "role": "Admin", "name": "System Administrator"},
        {"email": "wh_staff1@tcp.com", "password": "password123", "role": "Staff", "name": "คลังสินค้า บางบอน (วัตถุดิบ)"},
        {"email": "wh_staff2@tcp.com", "password": "password123", "role": "Staff", "name": "คลังสินค้า ปราจีนบุรี (บรรจุภัณฑ์)"},
        {"email": "supplier_abc@email.com", "password": "password123", "role": "Supplier", "name": "ABC Packaging Co., Ltd."},
        {"email": "supplier_xyz@email.com", "password": "password123", "role": "Supplier", "name": "XYZ Chemical Material"}
    ])

if 'delivery_db' not in st.session_state:
    # สร้างข้อมูลจำลองเริ่มต้นสำหรับแสดงผลบน Dashboard
    st.session_state.delivery_db = pd.DataFrame([
        {
            "id": "TCP-001", "type": "บรรจุภัณฑ์", "supplier": "ABC Packaging Co., Ltd.", 
            "truck_id": "3กง-1234 กทม.", "date": "2026-05-25", "slot": "09:00 - 10:00", 
            "location": "โรงงานบางบอน", "invoice": "INV-2026-001.pdf", "other_doc": "None", 
            "status": "Plan", "updated_by": "supplier_abc@email.com", "timestamp": "2026-05-24 10:00"
        },
        {
            "id": "TCP-002", "type": "วัตถุดิบ", "supplier": "XYZ Chemical Material", 
            "truck_id": "8กข-5678 นนทบุรี", "date": "2026-05-25", "slot": "09:00 - 10:00", 
            "location": "โรงงานบางบอน", "invoice": "INV-XYZ-99.pdf", "other_doc": "COA.pdf", 
            "status": "Confirm", "updated_by": "wh_staff1@tcp.com", "timestamp": "2026-05-24 11:30"
        }
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

# รายชื่อสถานที่จัดส่ง และสล็อตเวลา
LOCATIONS = ["โรงงานบางบอน", "โรงงานปราจีนบุรี", "คลังสินค้าเซ็นทรัล"]
TIME_SLOTS = [f"{str(h).zfill(2)}:00 - {str(h+1).zfill(2)}:00" for h in range(8, 17)] # 08:00 ถึง 17:00

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def check_slot_availability(date_str, slot_str, location_str):
    """ฟังก์ชันตรวจสอบว่าในวัน เวลา และสถานที่นั้นๆ มีรถจองเต็ม 2 คันหรือยัง"""
    df = st.session_state.delivery_db
    # กรองรายการที่ตรงกันและสถานะไม่ได้ถูกยกเลิก
    existing_bookings = df[(df['date'] == date_str) & 
                           (df['slot'] == slot_str) & 
                           (df['location'] == location_str) & 
                           (df['status'] != 'Cancelled')]
    return len(existing_bookings) < 2

# ==========================================
# 4. SIDEBAR LOGOUT & USER INFO
# ==========================================
with st.sidebar:
    # จำลองการใส่โลโก้ TCP (ดึงจาก Placeholder หรือใส่สีข้อความเด่นๆ)
    st.markdown("<h2 style='text-align: center; color: #D22630;'>TCP GROUP</h2>", unsafe_index=True)
    st.markdown("<p style='text-align: center; font-style: italic; font-size: 13px;'>Inbound Delivery Management</p>", unsafe_index=True)
    st.write("---")
    
    if st.session_state.logged_in:
        st.write(f"**ผู้ใช้งาน:** {st.session_state.user_info['name']}")
        st.write(f"**สิทธิ์การใช้งาน:** `{st.session_state.user_info['role']}`")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

# ==========================================
# 5. LOGIN SCREEN
# ==========================================
if not st.session_state.logged_in:
    st.subheader("กรุณาเข้าสู่ระบบ / Please Log In")
    
    with st.form("login_form"):
        email_input = st.text_input("Email Address (อีเมลลงทะเบียน)")
        password_input = st.text_input("Password (รหัสผ่าน)", type="password")
        login_submitted = st.form_submit_button("Sign In")
        
        if login_submitted:
            db = st.session_state.user_db
            user_match = db[(db['email'] == email_input) & (db['password'] == password_input)]
            
            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.user_info = user_match.iloc[0].to_dict()
                st.success(f"ยินดีต้อนรับคุณ {st.session_state.user_info['name']}")
                st.rerun()
            else:
                st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")
                
    st.info("💡 บัญชีทดสอบสำหรับทดลองระบบ:\n- Admin: admin@tcp.com\n- พนักงาน: wh_staff1@tcp.com\n- ซัพพลายเออร์: supplier_abc@email.com\n*(รหัสผ่านเหมือนกันหมด: password123)*")

# ==========================================
# 6. MAIN APPLICATION (LOGGED IN)
# ==========================================
else:
    role = st.session_state.user_info['role']
    
    # แท็บหลักในการแสดงผล แบ่งตามประเภทการใช้งาน
    tab_dash, tab_action, tab_admin = st.tabs(["📊 Real-time Dashboard", "📝 Operation Menu", "⚙️ Admin Center"])
    
    # ------------------------------------------
    # TAB 1: REAL-TIME DASHBOARD (ดูได้ทุกคน)
    # ------------------------------------------
    with tab_dash:
        st.subheader("🚛 สถานะการจัดส่งสินค้าขาเข้า (Inbound Delivery Status)")
        
        df_display = st.session_state.delivery_db.copy()
        
        # ส่วนแสดงสถิติภาพรวม (KPI Cards)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("แผนการจัดส่งทั้งหมด (Plan)", len(df_display[df_display['status'] == 'Plan']))
        c2.metric("ยืนยันแล้ว (Confirm)", len(df_display[df_display['status'] == 'Confirm']))
        c3.metric("รถมาถึงแล้ว (Arrived)", len(df_display[df_display['status'] == 'Arrived']))
        c4.metric("ลงของเสร็จสิ้น (Finished)", len(df_display[df_display['status'] == 'Finished']))
        
        st.write("---")
        
        # ตารางข้อมูลหลัก
        if not df_display.empty:
            # ตกแต่งสีสถานะเพื่อให้ดูง่าย
            def style_status(val):
                color = '#FFDD00' if val == 'Plan' else '#007A33' if val == 'Confirm' else '#002D62' if val == 'Arrived' else '#888888'
                return f'background-color: {color}; color: white; font-weight: bold; border-radius: 4px; padding: 2px 5px;'
            
            # จัดเรียงตามวันและเวลาล่าสุด
            df_display = df_display.sort_values(by=["date", "slot"], ascending=True)
            
            st.dataframe(
                df_display[["id", "type", "supplier", "truck_id", "date", "slot", "location", "status", "timestamp"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ไม่มีข้อมูลแผนการจัดส่งในระบบ")

    # ------------------------------------------
    # TAB 2: OPERATION MENU (Supplier / Staff ทำงานที่นี่)
    # ------------------------------------------
    with tab_action:
        
        # 2.1 สิทธิ์ SUPPLIER: สร้างแผนการจัดส่ง
        if role == "Supplier":
            st.subheader("📝 กรอกแผนการจัดส่งสินค้า (New Delivery Plan)")
            
            # ดึงชื่อ Supplier อัตโนมัติจากโปรไฟล์ผู้ล็อกอิน
            supplier_default_name = st.session_state.user_info['name']
            
            with st.form("supplier_delivery_form"):
                del_type = st.selectbox("1. เลือกชนิดการจัดส่ง", ["วัตถุดิบ (Raw Material)", "บรรจุภัณฑ์ (Packaging)"])
                supplier_name = st.text_input("2. ชื่อ Supplier", value=supplier_default_name, disabled=True)
                truck_id = st.text_input("3. กรอกทะเบียนรถ (และจังหวัด เช่น 3กง-1234 กทม.)")
                
                col_date, col_slot, col_loc = st.columns(3)
                with col_date:
                    del_date = st.date_input("4. เลือกวันจัดส่ง", min_value=datetime.today())
                with col_slot:
                    del_slot = st.selectbox("5. เลือก Slot เวลาจัดส่งรายชั่วโมง", TIME_SLOTS)
                with col_loc:
                    del_loc = st.selectbox("6. เลือกสถานที่ส่ง", LOCATIONS)
                    
                invoice_file = st.file_uploader("7. คลิกแนบเอกสาร Invoice (PDF/Image)", type=["pdf", "jpg", "jpeg", "png"])
                other_file = st.file_uploader("8. คลิกแนบเอกสารอื่นๆ เช่น COA / ใบขับขี่", type=["pdf", "jpg", "jpeg", "png"])
                
                submit_plan = st.form_submit_button("Submit Plan")
                
                if submit_plan:
                    if not truck_id:
                        st.error("⚠️ กรุณากรอกทะเบียนรถยนต์ก่อนทำการส่งข้อมูล")
                    elif not invoice_file:
                        st.error("⚠️ จำเป็นต้องแนบเอกสาร Invoice เพื่อความถูกต้องของระบบคลังสินค้า")
                    else:
                        date_str = del_date.strftime("%Y-%m-%d")
                        
                        # ตรวจสอบเงื่อนไขว่า Slot เต็มหรือยัง (ห้ามเกิน 2 คันต่อชั่วโมงต่อสถานที่)
                        if check_slot_availability(date_str, del_slot, del_loc):
                            # บันทึกข้อมูลลง DataFrame จำลอง
                            new_id = f"TCP-{len(st.session_state.delivery_db) + 1:03d}"
                            new_entry = {
                                "id": new_id,
                                "type": del_type.split(" ")[0],
                                "supplier": supplier_name,
                                "truck_id": truck_id,
                                "date": date_str,
                                "slot": del_slot,
                                "location": del_loc,
                                "invoice": invoice_file.name,
                                "other_doc": other_file.name if other_file else "None",
                                "status": "Plan",
                                "updated_by": st.session_state.user_info['email'],
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            
                            st.session_state.delivery_db = pd.concat([st.session_state.delivery_db, pd.DataFrame([new_entry])], ignore_index=True)
                            
                            st.success(f"🎉 บันทึกแผนการจัดส่งสำเร็จ! หมายเลขอ้างอิงของคุณคือ {new_id} (ส่งอีเมลแจ้งสถานะ Plan ไปยัง {st.session_state.user_info['email']} เรียบร้อย)")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ ขออภัยด้วยครับ! สล็อตเวลา {del_slot} ณ {del_loc} ในวันที่ {date_str} มีรถจองเต็มจำนวนความจุ (2 คัน) แล้ว กรุณาเลือกสล็อตเวลาอื่น")

        # 2.2 สิทธิ์ STAFF (พนักงานคลังสินค้า): จัดการสถานะรถขนส่ง
        elif role == "Staff":
            st.subheader("⚙️ จัดการคิวและอัปเดตสถานะรถขนส่ง")
            st.write("พนักงานสามารถกด Confirm, เลื่อนเวลา, หรืออัปเดตสถานะเมื่อรถมาถึงคลังสินค้าได้ที่นี่")
            
            df_work = st.session_state.delivery_db.copy()
            # กรองเฉพาะรายการที่ยังไม่จบกระบวนการทำงาน
            active_deliveries = df_work[df_work['status'] != 'Finished']
            
            if not active_deliveries.empty:
                for idx, row in active_deliveries.iterrows():
                    with st.expander(f"📦 ID: {row['id']} | {row['supplier']} - ทะเบียน: {row['truck_id']} ({row['status']})"):
                        st.write(f"**ประเภท:** {row['type']} | **สถานที่ส่ง:** {row['location']}")
                        st.write(f"**เวลานัดหมายเดิม:** {row['date']} ช่วงเวลา {row['slot']}")
                        st.write(f"**ไฟล์แนบ:** 📄 Invoice: {row['invoice']} | 📄 อื่นๆ: {row['other_doc']}")
                        
                        # แยกปุ่มกดตามสถานะปัจจุบันเพื่อป้องกันความสับสน
                        if row['status'] == 'Plan':
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button(f"ยืนยันแผนการจัดส่ง (Confirm) ##{row['id']}", key=f"conf_{row['id']}"):
                                    st.session_state.delivery_db.at[idx, 'status'] = 'Confirm'
                                    st.session_state.delivery_db.at[idx, 'timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                    st.success(f"อัปเดตสถานะ {row['id']} เป็น 'Confirm' และส่งเมลแจ้ง Supplier แล้ว")
                                    st.rerun()
                            with col_b:
                                # ฟังก์ชันสำหรับเลื่อนเวลาคิวรถยนต์
                                new_slot = st.selectbox(f"เลื่อนเวลาจัดส่งสำหรับ {row['id']}", TIME_SLOTS, key=f"slot_change_{row['id']}")
                                if st.button(f"บันทึกการเปลี่ยนเวลา ##{row['id']}", key=f"btn_resched_{row['id']}"):
                                    st.session_state.delivery_db.at[idx, 'slot'] = new_slot
                                    st.session_state.delivery_db.at[idx, 'timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                    st.warning(f"เลื่อนเวลา {row['id']} ไปเป็น {new_slot} ระบบทำการแจ้งเตือนผ่านเมลล์แล้ว")
                                    st.rerun()
                                    
                        elif row['status'] == 'Confirm':
                            if st.button(f"🚛 รถมาถึงแล้ว (Arrived) ##{row['id']}", key=f"arr_{row['id']}"):
                                st.session_state.delivery_db.at[idx, 'status'] = 'Arrived'
                                st.session_state.delivery_db.at[idx, 'timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                st.success(f"อัปเดตระบบ: รถทะเบียน {row['truck_id']} เข้าสู่จุดโหลดสินค้า")
                                st.rerun()
                                
                        elif row['status'] == 'Arrived':
                            if st.button(f"✅ ลงของเสร็จสิ้น (Finished) ##{row['id']}", key=f"fin_{row['id']}"):
                                st.session_state.delivery_db.at[idx, 'status'] = 'Finished'
                                st.session_state.delivery_db.at[idx, 'timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                st.success(f"ปิดงานเรียบร้อย บันทึกประวัติลงฐานข้อมูลหลัก")
                                st.rerun()
            else:
                st.info("ไม่มีคิวงานค้างที่ต้องดำเนินการในขณะนี้")
                
        else:
            st.info("เมนูจัดการสถานะนี้เปิดให้ใช้งานเฉพาะยูสเซอร์ที่เป็นพนักงานคลังสินค้า (Staff) เท่านั้น")

    # ------------------------------------------
    # TAB 3: ADMIN CENTER (สิทธิ์ Admin เท่านั้น)
    # ------------------------------------------
    with tab_admin:
        if role == "Admin":
            st.subheader("⚙️ ระบบลงทะเบียนและจัดการผู้ใช้งาน (User Management)")
            
            with st.form("admin_register_user"):
                st.write("**เพิ่มผู้ใช้งานระบบรายใหม่ (ด้วย E-mail)**")
                new_email = st.text_input("ระบุ E-mail สำหรับใช้งาน")
                new_pwd = st.text_input("กำหนดรหัสผ่านเบื้องต้น", type="password")
                new_name = st.text_input("ชื่อ-นามสกุล / ชื่อบริษัทซัพพลายเออร์")
                new_role = st.selectbox("กำหนดสิทธิ์ระบบ (Role)", ["Supplier", "Staff", "Admin"])
                
                add_user_btn = st.form_submit_button("Register & Create User")
                
                if add_user_btn:
                    if not new_email or not new_pwd or not new_name:
                        st.error("กรุณากรอกข้อมูลให้ครบทุกช่องสำหรับการลงทะเบียน")
                    elif "@" not in new_email:
                        st.error("กรุณาระบุรูปแบบอีเมลให้ถูกต้อง")
                    else:
                        # บันทึกผู้ใช้ใหม่เข้าไปใน session state
                        new_user = {
                            "email": new_email,
                            "password": new_pwd,
                            "role": new_role,
                            "name": new_name
                        }
                        st.session_state.user_db = pd.concat([st.session_state.user_db, pd.DataFrame([new_user])], ignore_index=True)
                        st.success(f"ลงทะเบียนคุณ {new_name} สิทธิ์ `{new_role}` ในระบบเรียบร้อยแล้ว!")
            
            st.write("---")
            st.write("**รายชื่อผู้ใช้งานทั้งหมดในระบบปัจจุบัน**")
            st.dataframe(st.session_state.user_db[["name", "email", "role"]], use_container_width=True)
        else:
            st.error("🔒 เฉพาะผู้ดูแลระบบ (Admin) เท่านั้นที่สามารถเข้าถึงเมนูการสร้างและแก้ไขบัญชีผู้ใช้ได้")
