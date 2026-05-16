SYS_DELIMITERS = [",", "|", "\t", ";"]
STATEMENT_FORMATS = {
    "chase-bank-v1": {
        "name": "Chase Bank v1",
        "common_name": "Chase Bank",
        "headers" : [
            "Details",
            "Posting Date",
            "Description",
            "Amount",
            "Type",
            "Balance",
            "Check of Slip #"
        ],
        "dtype_map": {
            "Details": str,
            "Posting Date": str,
            "Description": str,
            "Amount": float,
            "Type": str,
            "Balance": float,
            "Check or Slip #": str
        }
    }
}