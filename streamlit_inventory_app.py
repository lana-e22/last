import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Inventaris MWA", layout="wide")

DATA_FILE = Path(__file__).with_name("inventory_data.json")
BACKGROUND_IMAGE = Path(__file__).with_name("background.png")

DEFAULT_CATEGORIES = ["Elektronik", "Aksesoris", "HDMI", "StopKontak", "Kabel", "Lainnya"]

DEFAULT_ITEMS = [
    {
        "id": "1",
        "sku": "SP-001",
        "name": "StopKontak 50M",
        "category": "Kabel",
        "location": "BOX 1",
        "condition": "Sangat Baik",
        "totalStock": 1,
        "availableStock": 1,
    },
    {
        "id": "2",
        "sku": "TV-001",
        "name": "TV 85 INC",
        "category": "Elektronik",
        "location": "Gudang MT",
        "condition": "Baik",
        "totalStock": 3,
        "availableStock": 3,
    },
    {
        "id": "3",
        "sku": "HD-001",
        "name": "HDMI 50M",
        "category": "HDMI",
        "location": "BOX 3",
        "condition": "Sangat Baik",
        "totalStock": 6,
        "availableStock": 6,
    },
    {
        "id": "4",
        "sku": "HD-002",
        "name": "HDMI PENDEK",
        "category": "HDMI",
        "location": "BOX 2",
        "condition": "Baik",
        "totalStock": 11,
        "availableStock": 11,
    },
    {
        "id": "5",
        "sku": "CAM-001",
        "name": "Kamera Sony Alpha A6400",
        "category": "Elektronik",
        "location": "Studio Foto",
        "condition": "Sangat Baik",
        "totalStock": 2,
        "availableStock": 1,
    },
]

DEFAULT_LOANS = [
    {
        "id": "L-1001",
        "itemId": "2",
        "itemName": "TV 85 INC",
        "borrowerName": "Budi Santoso",
        "borrowerId": "198203112001",
        "quantity": 1,
        "loanDate": "2026-10-25",
        "returnDate": "2026-11-02",
        "purpose": "Presentasi Proyek Klien",
        "status": "Dipinjam",
    },
    {
        "id": "L-1002",
        "itemId": "5",
        "itemName": "Kamera Sony Alpha A6400",
        "borrowerName": "Siti Aminah",
        "borrowerId": "siti@company.com",
        "quantity": 1,
        "loanDate": "2026-10-28",
        "returnDate": "2026-11-04",
        "purpose": "Rapat Tahunan Direksi",
        "status": "Dipinjam",
    },
]


def load_data():
    if not DATA_FILE.exists():
        data = {"categories": DEFAULT_CATEGORIES, "items": DEFAULT_ITEMS, "loans": DEFAULT_LOANS}
        save_data(data)
        return data

    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"categories": DEFAULT_CATEGORIES, "items": DEFAULT_ITEMS, "loans": DEFAULT_LOANS}

    normalized = normalize_data(data)
    save_data(normalized)
    return normalized


def save_data(data):
    normalized = normalize_data(data)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)


def normalize_data(data):
    categories = data.get("categories") or DEFAULT_CATEGORIES
    items = data.get("items") or DEFAULT_ITEMS
    loans = data.get("loans") or DEFAULT_LOANS

    categories = [str(c).strip() for c in categories if str(c).strip()]
    categories = list(dict.fromkeys(categories)) or DEFAULT_CATEGORIES

    normalized_items = []
    for i, item in enumerate(items or []):
        if not isinstance(item, dict):
            continue
        total_stock = int(item.get("totalStock") or 0)
        normalized_items.append(
            {
                "id": str(item.get("id") or f"item-{i + 1}"),
                "sku": str(item.get("sku") or "").strip(),
                "name": str(item.get("name") or "").strip(),
                "category": str(item.get("category") or "Lainnya").strip(),
                "location": str(item.get("location") or "").strip(),
                "condition": str(item.get("condition") or "Baik").strip(),
                "totalStock": max(0, total_stock),
                "availableStock": max(0, int(item.get("availableStock") or 0)),
            }
        )

    normalized_loans = []
    for loan in loans or []:
        if not isinstance(loan, dict):
            continue
        normalized_loans.append(
            {
                "id": str(loan.get("id") or f"L-{len(normalized_loans) + 1}"),
                "itemId": str(loan.get("itemId") or ""),
                "itemName": str(loan.get("itemName") or ""),
                "borrowerName": str(loan.get("borrowerName") or ""),
                "borrowerId": str(loan.get("borrowerId") or ""),
                "quantity": max(1, int(loan.get("quantity") or 1)),
                "loanDate": str(loan.get("loanDate") or date_today()),
                "returnDate": str(loan.get("returnDate") or date_today()),
                "purpose": str(loan.get("purpose") or ""),
                "status": str(loan.get("status") or "Dipinjam"),
            }
        )

    data = {"categories": categories, "items": normalized_items, "loans": normalized_loans}
    recompute_availability(data)
    return data


def recompute_availability(data):
    items = data.get("items") or []
    loans = data.get("loans") or []
    for item in items:
        active_quantity = sum(
            int(loan.get("quantity") or 0)
            for loan in loans
            if loan.get("itemId") == item.get("id") and loan.get("status") == "Dipinjam"
        )
        item["availableStock"] = max(0, int(item.get("totalStock") or 0) - active_quantity)


def date_today():
    return datetime.now().strftime("%Y-%m-%d")


def format_date(date_value):
    if not date_value:
        return "-"
    try:
        dt = datetime.strptime(str(date_value), "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except Exception:
        return str(date_value)


def render_dashboard(data):
    items = data["items"]
    loans = data["loans"]

    total_items = len(items)
    total_available = sum(int(item.get("availableStock") or 0) for item in items)
    total_stock = sum(int(item.get("totalStock") or 0) for item in items)
    borrowed_stock = max(0, total_stock - total_available)
    active_loans = sum(1 for loan in loans if loan.get("status") == "Dipinjam")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Item Barang", total_items)
    c2.metric("Total Stok Tersedia", total_available)
    c3.metric("Unit Dipinjam", borrowed_stock)
    c4.metric("Peminjaman Aktif", active_loans)

    recent = [loan for loan in loans if loan.get("status") == "Dipinjam"][:5]
    st.subheader("Peminjaman Aktif Terbaru")
    if not recent:
        st.info("Tidak ada peminjaman aktif.")
    else:
        recent_df = pd.DataFrame(
            [
                {
                    "Peminjam": loan.get("borrowerName"),
                    "Barang": loan.get("itemName"),
                    "Jumlah": loan.get("quantity"),
                    "Tgl Kembali": format_date(loan.get("returnDate")),
                }
                for loan in recent
            ]
        )
        st.dataframe(recent_df, use_container_width=True, hide_index=True)

    st.subheader("Stok Rendah / Rusak / Hilang")
    low_items = [item for item in items if int(item.get("availableStock") or 0) <= 1]
    if not low_items:
        st.success("Semua stok barang dalam kondisi cukup.")
    else:
        low_df = pd.DataFrame(
            [
                {
                    "Nama": item.get("name"),
                    "SKU": item.get("sku"),
                    "Tersedia": item.get("availableStock"),
                    "Total": item.get("totalStock"),
                }
                for item in low_items
            ]
        )
        st.dataframe(low_df, use_container_width=True, hide_index=True)


def render_inventory(data):
    categories = data["categories"]
    items = data["items"]

    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("Cari nama, SKU, lokasi", placeholder="Masukkan keyword")
    with col2:
        category_filter = st.selectbox("Kategori", ["Semua"] + categories)

    status_filter = st.selectbox("Status", ["Semua", "Tersedia", "Habis"])

    filtered = []
    for item in items:
        text = f"{item.get('name', '')} {item.get('sku', '')} {item.get('location', '')}".lower()
        matches_search = search.lower() in text if search else True
        matches_category = category_filter == "Semua" or item.get("category") == category_filter
        matches_status = True
        if status_filter == "Tersedia":
            matches_status = int(item.get("availableStock") or 0) > 0
        elif status_filter == "Habis":
            matches_status = int(item.get("availableStock") or 0) == 0

        if matches_search and matches_category and matches_status:
            filtered.append(item)

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "SKU": item.get("sku"),
                    "Nama Barang": item.get("name"),
                    "Kategori": item.get("category"),
                    "Lokasi": item.get("location"),
                    "Kondisi": item.get("condition"),
                    "Tersedia": item.get("availableStock"),
                    "Total": item.get("totalStock"),
                    "Status": "Tersedia" if int(item.get("availableStock") or 0) > 0 else "Habis",
                }
                for item in filtered
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Tambah Barang Baru"):
        form = st.form("add_item_form")
        with form:
            sku = st.text_input("SKU / Kode Barang")
            name = st.text_input("Nama Barang")
            category = st.selectbox("Kategori", categories)
            location = st.text_input("Lokasi Penyimpanan")
            condition = st.selectbox("Kondisi", ["Sangat Baik", "Baik", "Perlu Perbaikan", "Rusak"])
            total_stock = st.number_input("Total Stok", min_value=1, step=1)
            submitted = st.form_submit_button("Simpan Barang")

        if submitted:
            if not sku or not name or not location:
                st.warning("Semua field wajib diisi.")
            else:
                duplicate = any(item.get("sku", "").lower() == sku.lower() for item in items)
                if duplicate:
                    st.warning("SKU sudah digunakan oleh barang lain.")
                else:
                    new_item = {
                        "id": str(int(datetime.now().timestamp() * 1000)),
                        "sku": sku,
                        "name": name,
                        "category": category,
                        "location": location,
                        "condition": condition,
                        "totalStock": int(total_stock),
                        "availableStock": int(total_stock),
                    }
                    items.append(new_item)
                    data["items"] = items
                    save_data(data)
                    st.success("Barang berhasil ditambahkan!")
                    st.rerun()

    with st.expander("Edit / Hapus Barang"):
        item_id = st.selectbox(
            "Pilih Barang",
            [item["id"] for item in items],
            format_func=lambda x: next((i["name"] for i in items if i["id"] == x), x),
        )
        if item_id:
            item = next((i for i in items if i["id"] == item_id), None)
            if item:
                with st.form("edit_item_form"):
                    edit_sku = st.text_input("SKU", value=item.get("sku", ""))
                    edit_name = st.text_input("Nama Barang", value=item.get("name", ""))
                    edit_category = st.selectbox(
                        "Kategori",
                        categories,
                        index=categories.index(item.get("category", categories[0])) if item.get("category") in categories else 0,
                    )
                    edit_location = st.text_input("Lokasi", value=item.get("location", ""))
                    edit_condition = st.selectbox(
                        "Kondisi",
                        ["Sangat Baik", "Baik", "Perlu Perbaikan", "Rusak"],
                        index=["Sangat Baik", "Baik", "Perlu Perbaikan", "Rusak"].index(item.get("condition", "Baik")),
                    )
                    edit_total = st.number_input("Total Stok", min_value=1, step=1, value=int(item.get("totalStock") or 1))
                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        save_edit = st.form_submit_button("Simpan Perubahan")
                    with col_edit2:
                        delete_btn = st.form_submit_button("Hapus Barang")

                if save_edit:
                    duplicate = any(
                        other.get("sku", "").lower() == edit_sku.lower() and other.get("id") != item_id
                        for other in items
                    )
                    if duplicate:
                        st.warning("SKU sudah dipakai oleh barang lain.")
                    else:
                        borrowed = sum(
                            int(loan.get("quantity") or 0)
                            for loan in data["loans"]
                            if loan.get("itemId") == item_id and loan.get("status") == "Dipinjam"
                        )
                        if edit_total < borrowed:
                            st.warning(f"Total stok tidak boleh kurang dari unit dipinjam ({borrowed}).")
                        else:
                            item["sku"] = edit_sku.strip()
                            item["name"] = edit_name.strip()
                            item["category"] = edit_category
                            item["location"] = edit_location.strip()
                            item["condition"] = edit_condition
                            item["totalStock"] = int(edit_total)
                            item["availableStock"] = max(0, int(edit_total) - borrowed)
                            save_data(data)
                            st.success("Barang berhasil diperbarui!")
                            st.rerun()

                if delete_btn:
                    if any(loan.get("itemId") == item_id and loan.get("status") == "Dipinjam" for loan in data["loans"]):
                        st.warning("Barang tidak dapat dihapus karena masih ada peminjaman aktif.")
                    else:
                        data["items"] = [i for i in items if i.get("id") != item_id]
                        save_data(data)
                        st.success("Barang berhasil dihapus.")
                        st.rerun()

    with st.expander("Kelola Kategori"):
        new_category = st.text_input("Kategori Baru")
        if st.button("Tambah Kategori"):
            clean = new_category.strip()
            if not clean:
                st.warning("Nama kategori tidak boleh kosong.")
            elif clean in categories:
                st.warning("Kategori sudah ada.")
            else:
                categories.append(clean)
                data["categories"] = categories
                save_data(data)
                st.success("Kategori berhasil ditambahkan.")
                st.rerun()

        for cat in categories:
            is_used = any(item.get("category") == cat for item in items)
            if is_used:
                st.write(f"{cat} (sedang dipakai)")
            else:
                if st.button(f"Hapus: {cat}", key=f"del_cat_{cat}"):
                    categories.remove(cat)
                    data["categories"] = categories
                    save_data(data)
                    st.success(f"Kategori {cat} dihapus.")
                    st.rerun()


def render_loans(data):
    loans = data["loans"]
    items = data["items"]

    item_options = [item for item in items if int(item.get("availableStock") or 0) > 0]
    with st.form("loan_form"):
        item_choice = st.selectbox("Pilih Barang", ["-- Pilih Barang --"] + [item["name"] for item in item_options], index=0)
        if item_choice == "-- Pilih Barang --":
            item_selected = None
        else:
            item_selected = next(item for item in item_options if item["name"] == item_choice)

        borrower_name = st.text_input("Nama Peminjam")
        borrower_id = st.text_input("No Telepon / Identitas")
        quantity = st.number_input("Jumlah Pinjam", min_value=1, step=1, value=1)
        return_date = st.date_input("Tgl Kembalikan", min_value=datetime.now().date())
        purpose = st.text_area("Keperluan / Catatan", placeholder="Contoh: Workshop Laboratorium")
        submitted = st.form_submit_button("Proses Peminjaman")

    if submitted:
        if not item_selected:
            st.warning("Silakan pilih barang terlebih dahulu.")
        elif not borrower_name or not borrower_id:
            st.warning("Nama peminjam dan identitas wajib diisi.")
        else:
            if quantity > int(item_selected.get("availableStock") or 0):
                st.warning(f"Stok tersedia hanya {item_selected.get('availableStock')} unit.")
            else:
                new_loan = {
                    "id": f"L-{int(datetime.now().timestamp() * 1000)}",
                    "itemId": item_selected["id"],
                    "itemName": item_selected["name"],
                    "borrowerName": borrower_name,
                    "borrowerId": borrower_id,
                    "quantity": int(quantity),
                    "loanDate": date_today(),
                    "returnDate": return_date.strftime("%Y-%m-%d"),
                    "purpose": purpose,
                    "status": "Dipinjam",
                }
                loans.append(new_loan)
                data["loans"] = loans
                save_data(data)
                st.success("Peminjaman berhasil dicatat!")
                st.rerun()

    tab_all, tab_active, tab_returned = st.tabs(["Semua", "Aktif", "Selesai"])

    loan_groups = {
        "Semua": loans,
        "Aktif": [loan for loan in loans if loan.get("status") == "Dipinjam"],
        "Selesai": [loan for loan in loans if loan.get("status") != "Dipinjam"],
    }

    for label, group in [("Semua", loan_groups["Semua"]), ("Aktif", loan_groups["Aktif"]), ("Selesai", loan_groups["Selesai"])]:
        if label == "Semua":
            container = tab_all
        elif label == "Aktif":
            container = tab_active
        else:
            container = tab_returned

        with container:
            if not group:
                st.info("Tidak ada data peminjaman.")
                continue

            df = pd.DataFrame(
                [
                    {
                        "ID": loan.get("id"),
                        "Peminjam": loan.get("borrowerName"),
                        "Barang": loan.get("itemName"),
                        "Jml": loan.get("quantity"),
                        "Tgl Pinjam": format_date(loan.get("loanDate")),
                        "Tgl Kembali": format_date(loan.get("returnDate")),
                        "Status": loan.get("status"),
                    }
                    for loan in sorted(group, key=lambda x: x.get("loanDate", ""), reverse=True)
                ]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)

            for loan in group:
                if loan.get("status") == "Dipinjam":
                    col_return, col_edit, col_delete = st.columns([1, 1, 1])

                    with col_return:
                        return_key = f"return_{label}_{loan.get('id')}"
                        if st.button(f"Kembalikan: {loan.get('id')}", key=return_key):
                            loan["status"] = "Dikembalikan"
                            save_data(data)
                            st.success("Barang berhasil dikembalikan.")
                            st.rerun()

                    with col_edit:
                        edit_key = f"edit_loan_{label}_{loan.get('id')}"
                        if st.button(f"Edit: {loan.get('id')}", key=edit_key):
                            st.session_state["edit_loan_id"] = loan.get("id")

                    with col_delete:
                        delete_key = f"delete_loan_{label}_{loan.get('id')}"
                        if st.button(f"Hapus: {loan.get('id')}", key=delete_key):
                            data["loans"] = [l for l in data["loans"] if l.get("id") != loan.get("id")]
                            save_data(data)
                            st.success("Data peminjaman dihapus.")
                            st.rerun()

                if st.session_state.get("edit_loan_id") == loan.get("id"):
                    with st.expander(f"Edit Peminjaman {loan.get('id')}"):
                        with st.form(f"form_edit_{label}_{loan.get('id')}"):
                            borrower_name_edit = st.text_input("Nama Peminjam", value=loan.get("borrowerName", ""))
                            borrower_id_edit = st.text_input("No Telepon / Identitas", value=loan.get("borrowerId", ""))
                            quantity_edit = st.number_input("Jumlah", min_value=1, step=1, value=int(loan.get("quantity") or 1))
                            return_date_edit = st.date_input(
                                "Tgl Kembali",
                                value=datetime.strptime(str(loan.get("returnDate", date_today())), "%Y-%m-%d").date(),
                            )
                            purpose_edit = st.text_area("Keperluan / Catatan", value=loan.get("purpose", ""))
                            save_edit = st.form_submit_button("Simpan Perubahan")

                        if save_edit:
                            loan["borrowerName"] = borrower_name_edit.strip()
                            loan["borrowerId"] = borrower_id_edit.strip()
                            loan["quantity"] = int(quantity_edit)
                            loan["returnDate"] = return_date_edit.strftime("%Y-%m-%d")
                            loan["purpose"] = purpose_edit.strip()
                            save_data(data)
                            st.success("Data peminjaman berhasil diperbarui!")
                            st.session_state.pop("edit_loan_id", None)
                            st.rerun()


def sidebar_actions(data):
    st.sidebar.title("Aksi")
    if st.sidebar.button("Reset ke Data Default"):
        data.clear()
        data.update({"categories": DEFAULT_CATEGORIES, "items": DEFAULT_ITEMS, "loans": DEFAULT_LOANS})
        save_data(data)
        st.success("Data berhasil di-reset.")
        st.rerun()

    uploaded = st.sidebar.file_uploader("Impor Data JSON", type=["json"])
    if uploaded is not None:
        try:
            imported = json.loads(uploaded.read().decode("utf-8"))
            data.clear()
            data.update(normalize_data(imported))
            save_data(data)
            st.success("Data berhasil diimpor.")
            st.rerun()
        except Exception:
            st.sidebar.error("Format JSON tidak valid.")

    export_data = json.dumps(data, ensure_ascii=False, indent=2)
    st.sidebar.download_button(
        label="Ekspor Data JSON",
        data=export_data,
        file_name="inventaris_backup.json",
        mime="application/json",
    )


def main():
    st.set_page_config(page_title="Inventaris MWA", layout="wide")
    background_style = "" if not BACKGROUND_IMAGE.exists() else f"url('{BACKGROUND_IMAGE.name}')"
    import streamlit as st
    st.markdown(
    """
    <style>
    :root {
        --bg-main: #f8fafc;
        --card-bg: rgba(255, 255, 255, 0.75);
        --card-border: rgba(226, 232, 240, 0.8);
        --card-shadow: rgba(15, 23, 42, 0.05);
        --accent-glow: rgba(99, 102, 241, 0.12);
        --text-primary: #0f172a;
    }

    .stApp {
        background-color: var(--bg-main) !important;
        color: var(--text-primary) !important;
    }

    .stDataFrame,
    [data-testid="stDataFrame"],
    .stExpander,
    .stTabs [role="tablist"],
    .stButton > button,
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stDateInput > div > div,
    .stFileUploader > div > div,
    .stDownloadButton > button,
    .stForm {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 25px -5px var(--card-shadow), 0 8px 10px -6px var(--accent-glow) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        transition: all 0.25s ease-in-out !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: rgba(99, 102, 241, 0.4) !important;
        box-shadow: 0 12px 20px -5px rgba(99, 102, 241, 0.2) !important;
        transform: translateY(-1px);
    }

    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stHorizontalBlock"] {
        background: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
    st.title("Sistem Manajemen Inventaris & Peminjaman Barang")
    
        data = load_data()
        sidebar_actions(data)
    
        dashboard, inventory, loans = st.tabs(["Dashboard", "Inventori", "Peminjaman"])
    
        with dashboard:
            render_dashboard(data)
    
        with inventory:
            render_inventory(data)
    
        with loans:
            render_loans(data)
    
    if __name__ == "__main__":
        main()
