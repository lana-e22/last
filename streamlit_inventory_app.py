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
