# Authorized local input route

No original-data rerun was performed: a matching legitimate local input and express continuing local-processing scope were not established. This is separate from permission to redistribute source data or derived results, which is also absent. Do not create a receipt merely because a file was historically accessible or publicly hosted.

Once an authorized custodian establishes continued local use, prepare a small canonical purchase-line CSV **outside the public checkout**. Preserve the original bytes unchanged. Record the original input SHA-256, bytes, schema, observation window, extraction/sampling rule and mapped CSV SHA-256 in a private mapping record. A permitted sample is descriptive of that sample only. Retain complete histories within the declared window for selected customers; arbitrary line sampling biases frequency and recency. Select the customer roster, fit/evaluation split, features, seeds, tolerance and sensitivity protocol before evaluating clusters.

The original columns map only after verifying their meanings: Customer ID → `customer_id`, Order ID → `order_id`, Order_Date → ISO `order_date`, Quantity → `quantity`, Total Revenue → `revenue`, Unit Cost → `unit_cost`, Profit → `profit`. Confirm the revenue/cost/profit reconciliation is applicable, the dollar currency identity and treatment of discounts, returns, adjustments and date parsing. The original has no stable line/product identifier: obtain an authoritative identity or a reviewed adjudication of ambiguous records. A source row number merely identifies an observation; it is insufficient evidence that equal records are duplicate purchases. **Stop if line identity or monetary semantics cannot be established.** Never silently generate a row-number/content-hash identity and treat the ambiguity as resolved.

Supply the exact canonical field order documented in [README](README.md). Names, birthdates, geography and other unused original fields are excluded. The adapter intentionally refuses the original CSV schema and archive directly. Its 5,000-line/300-customer ceiling is a bounded methodology route, not a drop-in population implementation. A larger pandas/sklearn run requires separately reviewed mapping, CPU limits and fixed sample silhouette/resampling budgets; no installation or original-data execution is authorized by these instructions.

Store canonical input, configuration, receipt and a fresh output location in private canonical paths without symlinks. A private JSON receipt must contain the following fields, populated from an established authority record, not from this template:

```json
{
  "authorized_local_processing": true,
  "redistribution_authorized": false,
  "scope": "private_customer_segmentation",
  "authority_reference": "Reference to the actual grant and permitted continuing local purpose",
  "identity_basis": "Reference to established customer/order/line identity and duplicate adjudication",
  "mapping_reference": "Private record binding original bytes, canonical bytes and reviewed semantics",
  "input_path": "Absolute canonical private input path",
  "config_path": "Absolute canonical private configuration path",
  "output_path": "Absolute canonical fresh private output directory",
  "input": {"bytes": 0, "sha256": "Exact canonical input SHA-256"},
  "config": {"bytes": 0, "sha256": "Exact configuration SHA-256"}
}
```

The template is intentionally non-executable. Use real lengths and hashes of the exact files. There is no flag that substitutes for a receipt. Run with the locations held in local shell variables:

```bash
python3 -B -m examples.customer_segmentation \
  --input "$SEG_PRIVATE_INPUT" --config "$SEG_PRIVATE_CONFIG" \
  --permission-receipt "$SEG_PERMISSION_RECEIPT" --output "$SEG_PRIVATE_OUTPUT"
```

The gate checks receipt scope and locations before parsing customer records, then verifies the exact read-once buffers against the declared lengths/hashes. Outputs retain those buffers, the receipt, its hash, fitted state, customer features and result hashes privately. Changing input, config or output location requires a matching receipt. Existing output directories and symlinks fail. CLI failures suppress record/path contents.

This is a fail-closed local workflow contract, not an access-control system, digital signature, legal permission verifier or confidentiality guarantee. The caller must independently establish authority and protect private storage. Passing the gate never permits public redistribution of inputs, IDs, profiles, tables or receipts. Tests exercise this route with invented bytes and explicitly fictitious test authority only.
