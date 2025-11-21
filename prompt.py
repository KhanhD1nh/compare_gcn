SYSTEM_INSTRUCTION_NUMBER_GCN = """
Extract the Land Certificate ID (Số phát hành/Số GCN) located typically in the bottom corners or bottom center of the certificate.

VALID FORMATS (Pattern Matching):
The ID always consists of **1 or 2 Uppercase Letters** followed by a sequence of **6 to 8 Digits**.
* **Standard/Legacy:** 6 or 7 digits (e.g., "BL 687415", "D 0042250", "CH 42992").
* **Extended/New:** 8 digits (e.g., "AA 01555079", "BX 12345678").

INSTRUCTIONS:
1. Look for the pattern: [A-Z]{1,2} [0-9]{6,8}
2. Keep all leading zeros (e.g., "0155..." must stay "0155...").
3. Ignore prefixes like "Số", "No.", "Sổ".

ULTRA IMPORTANT: ONLY response with the ID string. No other text.
"""