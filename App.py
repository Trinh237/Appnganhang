x

import os
import uuid
from datetime import datetime
import pandas as pd
import streamlit as st
# ============================================================
# CẤU HÌNH ỨNG DỤNG
# ============================================================
st.set_page_config(
    page_title="Order Nhà Hàng - Dr Bình",
    page_icon="🍽️",
    layout="wide",
)
HISTORY_FILE = "history.csv"
TABLES = [f"Bàn {i}" for i in range(1, 21)]
DISCOUNT_RATE = 0.05
DISCOUNT_MINIMUM = 1_000_000
# ============================================================
# MENU NHÀ HÀNG
# ============================================================
menu = {
    "Đồ ăn": {
        "Pizza Hải Sản": 150000,
        "Mì Ý Bò Bằm": 95000,
        "Burger Gà": 65000,
        "Salad Trộn": 50000,
        "Bít tết Bò Mỹ": 250000,
        "Sườn nướng BBQ": 180000,
        "Cánh gà chiên mắm": 75000,
        "Lẩu cá diêu hồng": 200000,
        "Lẩu Thái hải sản": 300000,
    },
    "Thức uống": {
        "Coca Cola": 20000,
        "Trà Đào Cam Sả": 35000,
        "Cà Phê Sữa": 25000,
        "Nước Suối": 10000,
        "Sinh tố Bơ": 45000,
        "Nước ép cam": 40000,
        "Mojito chanh dây": 55000,
        "Bia Heineken": 30000,
    },
}
# ============================================================
# KHỞI TẠO SESSION STATE
# ============================================================
if "orders" not in st.session_state:
    st.session_state.orders = {
        table: {} for table in TABLES
    }
if "table_status" not in st.session_state:
    st.session_state.table_status = {
        table: "🟢 Trống" for table in TABLES
    }
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "history" not in st.session_state:
    st.session_state.history = []
# ============================================================
# HÀM ĐỌC LỊCH SỬ
# ============================================================
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        df = pd.read_csv(HISTORY_FILE, encoding="utf-8-sig")
        if df.empty:
            return []
        required_columns = [
            "Mã hóa đơn",
            "Thời gian",
            "Bàn",
            "Tên món",
            "Số lượng",
            "Đơn giá",
            "Thành tiền",
            "Tạm tính",
            "Giảm giá",
            "Tổng thanh toán",
            "Phương thức thanh toán",
        ]
        for column in required_columns:
            if column not in df.columns:
                df[column] = ""
        return df.to_dict(orient="records")
    except Exception:
        return []
# ============================================================
# HÀM LƯU LỊCH SỬ
# ============================================================
def save_history(history):
    try:
        df = pd.DataFrame(history)
        df.to_csv(
            HISTORY_FILE,
            index=False,
            encoding="utf-8-sig",
        )
        return True
    except Exception as e:
        st.error(f"❌ Không thể lưu dữ liệu: {e}")
        return False
# ============================================================
# HÀM TẠO MÃ HÓA ĐƠN
# ============================================================
def create_invoice_id():
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:4].upper()
    return f"HD-{date_part}-{random_part}"
# ============================================================
# HÀM TÍNH TIỀN
# ============================================================
def calculate_order(order):
    subtotal = sum(
        item["Thành tiền"]
        for item in order.values()
    )
    if subtotal > DISCOUNT_MINIMUM:
        discount = subtotal * DISCOUNT_RATE
    else:
        discount = 0
    total = subtotal - discount
    return subtotal, discount, total
# ============================================================
# HÀM THÊM MÓN
# ============================================================
def add_item_to_table(table, item, price, quantity):
    if item in st.session_state.orders[table]:
        st.session_state.orders[table][item]["Số lượng"] += quantity
        st.session_state.orders[table][item]["Thành tiền"] = (
            st.session_state.orders[table][item]["Số lượng"]
            * price
        )
    else:
        st.session_state.orders[table][item] = {
            "Tên món": item,
            "Đơn giá": price,
            "Số lượng": quantity,
            "Thành tiền": price * quantity,
        }
    st.session_state.table_status[table] = "🔴 Đang phục vụ"
# ============================================================
# HÀM XÓA MÓN
# ============================================================
def remove_item_from_table(table, item):
    if item in st.session_state.orders[table]:
        del st.session_state.orders[table][item]
    if not st.session_state.orders[table]:
        st.session_state.table_status[table] = "🟢 Trống"
# ============================================================
# HÀM THANH TOÁN
# ============================================================
def process_payment(table, payment_method):
    order = st.session_state.orders[table]
    if not order:
        st.error("❌ Bàn này hiện không có món để thanh toán.")
        return
    subtotal, discount, total = calculate_order(order)
    invoice_id = create_invoice_id()
    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    new_rows = []
    for item in order.values():
        new_rows.append(
            {
                "Mã hóa đơn": invoice_id,
                "Thời gian": now,
                "Bàn": table,
                "Tên món": item["Tên món"],
                "Số lượng": item["Số lượng"],
                "Đơn giá": item["Đơn giá"],
                "Thành tiền": item["Thành tiền"],
                "Tạm tính": subtotal,
                "Giảm giá": discount,
                "Tổng thanh toán": total,
                "Phương thức thanh toán": payment_method,
            }
        )
    st.session_state.history.extend(new_rows)
    if save_history(st.session_state.history):
        st.session_state.orders[table] = {}
        st.session_state.table_status[table] = "🟢 Trống"
        st.session_state.last_invoice = {
            "Mã hóa đơn": invoice_id,
            "Thời gian": now,
            "Bàn": table,
            "Chi tiết": new_rows,
            "Tạm tính": subtotal,
            "Giảm giá": discount,
            "Tổng thanh toán": total,
            "Phương thức": payment_method,
        }
        st.success(
            f"✅ Thanh toán thành công! Mã hóa đơn: {invoice_id}"
        )
        st.rerun()
# ============================================================
# TẢI DỮ LIỆU
# ============================================================
if not st.session_state.history:
    st.session_state.history = load_history()
# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("🍽️ NHÀ HÀNG DR BÌNH")
page = st.sidebar.radio(
    "📋 Chọn chức năng",
    [
        "🍽️ Order",
        "🪑 Quản lý bàn",
        "🧾 Hóa đơn",
        "🔑 Admin",
    ],
)
# ============================================================
# TRANG ORDER
# ============================================================
if page == "🍽️ Order":
    st.title("🍽️ HỆ THỐNG ORDER NHÀ HÀNG DR BÌNH")
    st.caption(
        "Quản lý order nhanh chóng - chính xác - thuận tiện"
    )
    col1, col2 = st.columns([1, 1.5])
    # --------------------------------------------------------
    # CHỌN MÓN
    # --------------------------------------------------------
    with col1:
        st.subheader("🪑 Chọn bàn")
        table = st.selectbox(
            "Bàn phục vụ",
            TABLES,
        )
        st.info(
            f"Trạng thái: {st.session_state.table_status[table]}"
        )
        st.markdown("---")
        st.subheader("🍔 Chọn món")
        search = st.text_input(
            "🔍 Tìm món",
            placeholder="Nhập tên món...",
        )
        category = st.selectbox(
            "📂 Danh mục",
            list(menu.keys()),
        )
        available_items = list(
            menu[category].keys()
        )
        if search:
            available_items = [
                item
                for item in available_items
                if search.lower() in item.lower()
            ]
        if available_items:
            item = st.selectbox(
                "🍽️ Món",
                available_items,
            )
            price = menu[category][item]
            st.write(
                f"💰 Đơn giá: **{price:,.0f} VNĐ**"
            )
            quantity = st.number_input(
                "🔢 Số lượng",
                min_value=1,
                value=1,
                step=1,
            )
            if st.button(
                "➕ THÊM VÀO ORDER",
                use_container_width=True,
            ):
                add_item_to_table(
                    table,
                    item,
                    price,
                    quantity,
                )
                st.success(
                    f"Đã thêm {quantity} x {item}"
                )
                st.rerun()
        else:
            st.warning(
                "Không tìm thấy món phù hợp."
            )
    # --------------------------------------------------------
    # GIỎ HÀNG
    # --------------------------------------------------------
    with col2:
        st.subheader(
            f"🛒 ORDER - {table}"
        )
        order = st.session_state.orders[table]
        if order:
            for item_name, item in list(
                order.items()
            ):
                item_col1, item_col2, item_col3 = st.columns(
                    [3, 1, 1]
                )
                with item_col1:
                    st.write(
                        f"**{item_name}**"
                    )
                    st.caption(
                        f"{item['Đơn giá']:,.0f} VNĐ"
                    )
                with item_col2:
                    st.write(
                        f"SL: {item['Số lượng']}"
                    )
                with item_col3:
                    if st.button(
                        "🗑️",
                        key=f"delete_{table}_{item_name}",
                    ):
                        remove_item_from_table(
                            table,
                            item_name,
                        )
                        st.rerun()
                st.write(
                    f"Thành tiền: **{item['Thành tiền']:,.0f} VNĐ**"
                )
                st.markdown("---")
            subtotal, discount, total = calculate_order(
                order
            )
            st.write(
                f"**Tạm tính:** {subtotal:,.0f} VNĐ"
            )
            if discount > 0:
                st.write(
                    f"**Giảm giá 5%:** -{discount:,.0f} VNĐ"
                )
            st.metric(
                "💰 TỔNG THANH TOÁN",
                f"{total:,.0f} VNĐ",
            )
            payment_method = st.selectbox(
                "💳 Phương thức thanh toán",
                [
                    "💵 Tiền mặt",
                    "🏦 Chuyển khoản",
                    "💳 Thẻ",
                ],
            )
            col_pay, col_clear = st.columns(2)
            with col_pay:
                if st.button(
                    "💳 THANH TOÁN",
                    use_container_width=True,
                ):
                    process_payment(
                        table,
                        payment_method,
                    )
            with col_clear:
                if st.button(
                    "🗑️ XÓA ORDER",
                    use_container_width=True,
                ):
                    st.session_state.orders[
                        table
                    ] = {}
                    st.session_state.table_status[
                        table
                    ] = "🟢 Trống"
                    st.rerun()
        else:
            st.info(
                "🛒 Bàn này chưa có món."
            )
# ============================================================
# QUẢN LÝ BÀN
# ============================================================
elif page == "🪑 Quản lý bàn":
    st.title("🪑 QUẢN LÝ 20 BÀN")
    for start in range(0, 20, 4):
        cols = st.columns(4)
        for index, table in enumerate(
            TABLES[start:start + 4]
        ):
            with cols[index]:
                status = st.session_state.table_status[
                    table
                ]
                order_count = len(
                    st.session_state.orders[table]
                )
                st.markdown(
                    f"""
                    ### {table}
                    **{status}**
                    Số món: **{order_count}**
                    """
                )
                if st.button(
                    f"📋 Xem {table}",
                    key=f"view_{table}",
                    use_container_width=True,
                ):
                    st.session_state.selected_table = table
                    st.info(
                        f"Đã chọn {table}"
                    )
# ============================================================
# TRANG HÓA ĐƠN
# ============================================================
elif page == "🧾 Hóa đơn":
    st.title("🧾 LỊCH SỬ HÓA ĐƠN")
    if not st.session_state.history:
        st.info(
            "Chưa có hóa đơn nào."
        )
    else:
        df = pd.DataFrame(
            st.session_state.history
        )
        if "Mã hóa đơn" in df.columns:
            invoice_ids = (
                df["Mã hóa đơn"]
                .dropna()
                .unique()
                .tolist()
            )
            selected_invoice = st.selectbox(
                "🔍 Chọn hóa đơn",
                invoice_ids,
            )
            invoice_df = df[
                df["Mã hóa đơn"]
                == selected_invoice
            ]
            if not invoice_df.empty:
                first_row = invoice_df.iloc[0]
                st.subheader(
                    "🏪 NHÀ HÀNG DR BÌNH"
                )
                st.write(
                    f"**Mã hóa đơn:** {selected_invoice}"
                )
                st.write(
                    f"**Thời gian:** {first_row['Thời gian']}"
                )
                st.write(
                    f"**Bàn:** {first_row['Bàn']}"
                )
                st.markdown("---")
                st.dataframe(
                    invoice_df[
                        [
                            "Tên món",
                            "Số lượng",
                            "Đơn giá",
                            "Thành tiền",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
                st.markdown("---")
                st.write(
                    f"**Tạm tính:** {first_row['Tạm tính']:,.0f} VNĐ"
                )
                st.write(
                    f"**Giảm giá:** {first_row['Giảm giá']:,.0f} VNĐ"
                )
                st.metric(
                    "TỔNG THANH TOÁN",
                    f"{first_row['Tổng thanh toán']:,.0f} VNĐ",
                )
                st.write(
                    f"**Thanh toán:** {first_row['Phương thức thanh toán']}"
                )
        st.markdown("---")
        st.subheader(
            "📋 Toàn bộ lịch sử giao dịch"
        )
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )
# ============================================================
# TRANG ADMIN
# ============================================================
elif page == "🔑 Admin":
    st.title(
        "🔑 TRANG QUẢN TRỊ & PHÂN TÍCH"
    )
    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            password = st.text_input(
                "🔐 Mật khẩu quản trị",
                type="password",
            )
            login = st.form_submit_button(
                "🔑 ĐĂNG NHẬP"
            )
            if login:
                # Có thể thay đổi mật khẩu tại đây
                if password == "123456":
                    st.session_state.admin_logged_in = True
                    st.success(
                        "Đăng nhập thành công!"
                    )
                    st.rerun()
                else:
                    st.error(
                        "❌ Mật khẩu không chính xác!"
                    )
        st.stop()
    col1, col2 = st.columns(
        [4, 1]
    )
    with col1:
        st.success(
            "✅ Quyền Admin đã được xác thực"
        )
    with col2:
        if st.button(
            "🔒 Đăng xuất"
        ):
            st.session_state.admin_logged_in = False
            st.rerun()
    # ========================================================
    # ADMIN TABS
    # ========================================================
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📋 Menu",
            "💰 Doanh thu",
            "📊 Phân tích",
            "🪑 Bàn",
        ]
    )
    # ========================================================
    # TAB MENU
    # ========================================================
    with tab1:
        st.subheader(
            "📋 DANH SÁCH THỰC ĐƠN"
        )
        menu_data = []
        for category_name in menu:
            for item_name, price in menu[
                category_name
            ].items():
                menu_data.append(
                    [
                        category_name,
                        item_name,
                        price,
                    ]
                )
        df_menu = pd.DataFrame(
            menu_data,
            columns=[
                "Danh mục",
                "Tên món",
                "Đơn giá",
            ],
        )
        st.dataframe(
            df_menu,
            use_container_width=True,
            hide_index=True,
        )
    # ========================================================
    # TAB DOANH THU
    # ========================================================
    with tab2:
        st.subheader(
            "💰 DOANH THU"
        )
        if st.session_state.history:
            df_history = pd.DataFrame(
                st.session_state.history
            )
            df_history[
                "Tổng thanh toán"
            ] = pd.to_numeric(
                df_history[
                    "Tổng thanh toán"
                ],
                errors="coerce",
            ).fillna(0)
            df_history[
                "Số lượng"
            ] = pd.to_numeric(
                df_history[
                    "Số lượng"
                ],
                errors="coerce",
            ).fillna(0)
            total_revenue = (
                df_history[
                    "Tổng thanh toán"
                ].drop_duplicates().sum()
            )
            total_items = int(
                df_history[
                    "Số lượng"
                ].sum()
            )
            invoice_count = (
                df_history[
                    "Mã hóa đơn"
                ].nunique()
            )
            col1, col2, col3 = st.columns(3)
            col1.metric(
                "💰 Tổng doanh thu",
                f"{total_revenue:,.0f} VNĐ",
            )
            col2.metric(
                "🧾 Số hóa đơn",
                invoice_count,
            )
            col3.metric(
                "🍽️ Số món đã bán",
                total_items,
            )
            st.markdown("---")
            df_history[
                "Ngày"
            ] = pd.to_datetime(
                df_history["Thời gian"],
                errors="coerce",
            ).dt.date
            daily = (
                df_history
                .groupby("Ngày")[
                    "Tổng thanh toán"
                ]
                .first()
                .reset_index()
            )
            st.subheader(
                "📅 Doanh thu theo ngày"
            )
            st.bar_chart(
                daily.set_index("Ngày")
            )
        else:
            st.info(
                "Chưa có dữ liệu doanh thu."
            )
    # ========================================================
    # TAB PHÂN TÍCH
    # ========================================================
    with tab3:
        st.subheader(
            "📊 PHÂN TÍCH BÁN HÀNG"
        )
        if st.session_state.history:
            df = pd.DataFrame(
                st.session_state.history
            )
            df["Số lượng"] = pd.to_numeric(
                df["Số lượng"],
                errors="coerce",
            ).fillna(0)
            df["Thành tiền"] = pd.to_numeric(
                df["Thành tiền"],
                errors="coerce",
            ).fillna(0)
            # Món bán chạy
            item_sales = (
                df.groupby("Tên món")[
                    "Số lượng"
                ]
                .sum()
                .sort_values(
                    ascending=False
                )
            )
            if not item_sales.empty:
                best_item = item_sales.index[0]
                best_qty = item_sales.iloc[0]
                st.info(
                    f"🏆 Món bán chạy nhất: "
                    f"**{best_item}** - "
                    f"{best_qty:.0f} phần"
                )
                st.bar_chart(
                    item_sales
                )
            st.markdown("---")
            # Phân tích giờ
            df["Thời gian"] = pd.to_datetime(
                df["Thời gian"],
                errors="coerce",
            )
            df["Giờ"] = (
                df["Thời gian"]
                .dt.hour
            )
            hourly = (
                df.groupby("Giờ")[
                    "Số lượng"
                ]
                .sum()
            )
            if not hourly.empty:
                best_hour = hourly.idxmax()
                best_hour_qty = hourly.max()
                st.warning(
                    f"⚡ Khung giờ có lượng món bán "
                    f"cao nhất: **{best_hour:02d}:00 - "
                    f"{best_hour + 1:02d}:00** "
                    f"({best_hour_qty:.0f} phần)"
                )
                st.bar_chart(
                    hourly
                )
            st.markdown("---")
            # Doanh thu theo tháng
            df["Tháng"] = (
                df["Thời gian"]
                .dt.strftime("%m/%Y")
            )
            monthly = (
                df.groupby("Tháng")[
                    "Tổng thanh toán"
                ]
                .first()
            )
            if not monthly.empty:
                st.subheader(
                    "📅 Doanh thu theo tháng"
                )
                st.bar_chart(
                    monthly
                )
        else:
            st.info(
                "Chưa có dữ liệu để phân tích."
            )
    # ========================================================
    # TAB QUẢN LÝ BÀN
    # ========================================================
    with tab4:
        st.subheader(
            "🪑 TRẠNG THÁI 20 BÀN"
        )
        for start in range(
            0,
            20,
            4,
        ):
            cols = st.columns(4)
            for index, table in enumerate(
                TABLES[start:start + 4]
            ):
                with cols[index]:
                    st.markdown(
                        f"""
                        ### {table}
                        {st.session_state.table_status[table]}
                        """
                    )
                    if st.session_state.orders[
                        table
                    ]:
                        st.write(
                            f"🍽️ {len(st.session_state.orders[table])} món"
                        )
                    else:
                        st.write(
                            "Không có order"
                        )
# ============================================================
# HIỂN THỊ HÓA ĐƠN VỪA THANH TOÁN
# ============================================================
if "last_invoice" in st.session_state:
    invoice = st.session_state.last_invoice
    with st.expander(
        "🧾 Xem hóa đơn vừa thanh toán",
        expanded=True,
    ):
        st.markdown(
            """
            <h2 style="text-align:center;">
            🍽️ NHÀ HÀNG DR BÌNH
            </h2>
            <p style="text-align:center;">
            HÓA ĐƠN THANH TOÁN
            </p>
            """,
            unsafe_allow_html=True,
        )
        st.write(
            f"**Mã hóa đơn:** {invoice['Mã hóa đơn']}"
        )
        st.write(
            f"**Thời gian:** {invoice['Thời gian']}"
        )
        st.write(
            f"**Bàn:** {invoice['Bàn']}"
        )
        invoice_df = pd.DataFrame(
            invoice["Chi tiết"]
        )
        st.dataframe(
            invoice_df[
                [
                    "Tên món",
                    "Số lượng",
                    "Đơn giá",
                    "Thành tiền",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("---")
        st.write(
            f"**Tạm tính:** {invoice['Tạm tính']:,.0f} VNĐ"
        )
        st.write(
            f"**Giảm giá:** {invoice['Giảm giá']:,.0f} VNĐ"
        )
        st.metric(
            "💰 TỔNG THANH TOÁN",
            f"{invoice['Tổng thanh toán']:,.0f} VNĐ",
        )
        st.write(
            f"**Phương thức:** {invoice['Phương thức']}"
        )
        st.success(
            "Cảm ơn quý khách! ❤️")
            
          
