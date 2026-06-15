# NI9305 Code Review

**Reviewer:** (your name)
**Date:** 2026-06-15
**Subject:** TestStand Sequence — Setup Section

---

## Review #1 — Setup: Import NISE Virtual Devices

![Setup - Import NISE Virtual Devices](./review_01_setup_import_nise.PNG)

### Flow Description

1. **Log Socket Index** — Logs the current socket index before any import begins.
2. **Import Switch Matrix** — If not yet imported for this socket, calls NISE Import Config.vi and sets a flag to prevent re-importing.
3. **Import Coax Switch (Sockets 0 & 1)** — If socket index is 0 or 1, acquires lock `Shared_A`, imports the Coax config if not already done, then releases the lock.
4. **Import Coax Switch (Sockets 2 & 3)** — Same as above for socket index 2 or 3, using lock `Shared_B`.

### Recommendation

Add a comment to each step and group describing what it does at runtime, so the sequence is self-explanatory without tracing the logic.

---

---

## Review #2 — SDI Controls: Use `te-standard-data-types` Component

![SDI Controls - te-standard-data-types](./review_02_SDI.PNG)

### Flow Description

All SDI controls in the sequence should reference the shared `te-standard-data-types` component rather than defining their own data types individually.

### Recommendation

Use the `te-standard-data-types` component for all SDI controls, and link each control directly to the component.

> **Note:** Apply this change to **all related VIs**, not just the one shown above.

Reference: [te-standard-data-types](https://dev.azure.com/ni/DevCentral/_git/te-hwtest?path=/source/common/data/te-standard-data-types)

---

## Review #3 — Digital PFI0

### Status: All good

No issues found with the Digital PFI0 configuration.

> **Note:** Double confirm the PWM threshold value with the HW engineer.

---

## Review #4 — Initial Accuracy and Range Test

![Initial Accuracy and Range Test](./Review4_Initial.PNG)

### Flow Description

The VI acquires DMM and DUT measurements: it sets the PS voltage, waits for a delay, then triggers the NI9305 ADC acquisition. Afterwards, it performs a sanity check on the DMM reading and converts the DUT ADC output to millivolts using the nominal LSB weight.

### Current — Sanity Check Must Run Before the Actual Test

The sanity check (comparing the DMM measured voltage against the expected percentage range) currently runs **after** the NI9305 acquisition. Its error output (`Stimulus check failed!`) is not wired into the error line that feeds into the acquisition block.

**Recommendation:** Connect the sanity check error wire **upstream** of the NI9305 ADC acquisition node. This ensures the test aborts immediately if the stimulus is out of range, rather than proceeding with a bad measurement. All error terminals in this section should be chained in sequence — no dangling or parallel error lines.


---

## Review #5 — Initial Accuracy and Range Test (SDI)

![Initial Accuracy and Range Test - SDI](./Review_5_Initial2.PNG)

### Recommendation

1. **DMM Measurement label** — Rename the SDI label from `DMM Measurement` to `DMM Measurement (Sanity Check)` to make its purpose explicit at a glance.

2. **Add test limits** — Add a test limit to the DMM Measurement (Sanity Check) SDI entry so the sanity check has a defined pass/fail boundary, rather than relying solely on the percentage check in the block diagram.

---

<!-- Add next review below this line -->
