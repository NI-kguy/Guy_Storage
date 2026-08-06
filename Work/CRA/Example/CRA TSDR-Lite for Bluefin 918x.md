# CRA TSDR-Lite - Test Solution Design Review

> **Based on:** [TSDR v18.0](https://emerson.sharepoint.com/sites/TM-TestEngineering/Template%20Library/TEP%20Required%20Documents/Files/TSDR%20-%20Test%20System%20Design%20Review.pptx)

> **Purpose:** Accelerated TSDR template for CRA-impacted products. Scope is limited to CRA-driven changes only - not a full product TSDR. Present one deck per product family. TEs may merge related product families into a single TSDR when appropriate. Use judgment and coordinate with Phillip Conrad. Owning TE fills out slides; Phillip Conrad reviews for consistency across families.
>
> There will be two reviews:
>   - One that gates Definition Exit - Should be held asynchronously
>   - One that gates Planning Exit - Can be held asynchronously if agreed on by stakeholders
>
> **Ground rules:**
> - No modernization expectations. Slides covering modernization are N/A.
> - If no new hardware is introduced, all hardware-related slides are N/A.
> - If test time delta is ≤ 10% **and** station utilization (per utilization dashboard) is low, capacity analysis (Slide 10) may be skipped. Use judgment; document the decision.
> - Focus areas:
>   - Basic Schedule
>   - Required Test Changes
>   - Test Routing Changes
>   - Debug of "set on first use" Failures
>   - Impact to HW Services (RMA + Cal).
>
> Additionally, a high-level effort estimate (manhours) is required by Definition Exit to support PSG labor cost planning.
>
> *For viewing and editing, use [Visual Studio Code](https://code.visualstudio.com/download): press **Ctrl+Shift+V** for a rendered preview, or **Ctrl+K V** to view side-by-side.*
>
> **Progress tracking:** Each slide heading has a status emoji. Update it as you go: ❌ = not yet complete, ✅ = complete, ☑️ = ignored (internal template slide, no action required).

---

## Slide 1 - Presentation Title [Ignore] ☑️

> *[Internal template slide - no content required]*

---

## Slide 2 - Instructions for Completion [Ignore] ☑️

> *[Internal template slide - no content required]*

---

## Slide 3 - Preparation for TSDR: Timeline & Milestones [Ignore] ☑️

> *[Internal template slide - no content required]*

---

## Slide 4 - Section: "Must Be Presented" Instructions [Ignore] ☑️

> *[Internal template slide - no content required]*

---

## Slide 5 - Title Slide [By Definition Exit] ✅

**Bluefin** - CRA TSDR-Lite

---

## Slide 6 - Product Overview [By Definition Exit] ✅

- Product Family: **Bluefin**
- Owning TE: Gergely Kocsis
- Date: 2026-06-16
- CRA Change Classification *(select one)*:
  - [ ] Drop-in updatable (minimal test impact)
  - [x] Requires some rework, but manageable
  - [ ] Needs new late-stage firmware update FVT step
  - [ ] Problem product - needs special attention

**Product Family Description:**

cDAQ-9183/5/7/9 are part of the Bluefin products, Ethernet cDAQ chassis, both in 4 and 8 slot variants. These are Zynq-based products that run a custom firmware, not LinuxRT.

**Products in this Family:**

| Model Number | Test Set | Notes |
|---|---|---|
| cDAQ-9183 | 539839A-02 (rev 539839A-01) | 142095C-02L — Ethernet cDAQ, 4-slot |
| cDAQ-9185 | 539839A-02 (rev 539839A-01) | 142095C-01L (std) / 142095C-12L (conformal) — Ethernet cDAQ, 4-slot |
| cDAQ-9187 | 539839A-02 (rev 539839A-01) | 142143C-02L — Ethernet cDAQ, 8-slot |
| cDAQ-9189 | 539839A-02 (rev 539839A-01) | 142143C-01L (std) / 142143C-12L (conformal) — Ethernet cDAQ, 8-slot |

**Known Test Challenges:**

None.

> *If no new hardware is introduced, assembly drawings and layout slides are N/A.*

---

## Slide 7 - Project Milestones [By Planning Exit] ❌

- Expected CRA firmware release date: `<fill in>`
- Target Test Solution completion date: `<fill in>`
- Target FVT / TVR / MVR dates: `<fill in>`

> *Call out any known schedule risks*

---

## Slide 8 - Test Routing / Flow [By Definition Exit] ✅

**Impacted BN Test Suites / Routing Steps:**

| Routing Step | BN Test Suite or U2 Path | Notes |
|---|---|---|
| FVT140 | Bluefin cDAQ Test Suite IFT | LinuxRT firmware update + SOFU |
| RMA300 | Bluefin cDAQ Test Suite RIFT | RMA routing |

**Additional Routing Steps Introduced by CRA:**

None.

---

## Slide 9 - Test Design [By Definition Exit] ✅

> *The following slide is detailed and may need to be split into multiple sections. Focus on CRA-driven changes to test design only.*

**See "Software" slide for station image software information.**

> ⚠️ **Note: Bluefin is a Zynq-based product family. The SOFU/LinuxRT approach differs from the x64 Intel products (Fire Eagle, Swordfish, sbCombo). Coordinate with Phillip Conrad before filling in this slide.**

### Firmware Update to Support CRA SOFU

- What test steps update the shipping product firmware?
    - Write * to NAND
- How is the shipping product firmware provisioned?
    - [X] Via JTAG-Bootstrap + TFTP
- Is the shipping product firmware used to test the product?
    - [X] Full Testing (booting into the shipping firmware to run a significant number of tests)
    - [ ] Partial Testing (booting into the shipping firmware to run some critical tests)
    - [ ] Only final verification steps (correct FW, SN, PN, etc.)
- Will changing the shipping product firmware change how the test functions? **Yes**
- Is the update "drop-in" (no test sequence changes required)? **No**
- Will changing the shipping product firmware require additional software/image changes (new driver, new FVT sequence, etc.)? **No**
- Can a firmware update be added at the very end of the IFT/FVT test sequence apart from the existing firmware update procedure? **Yes**

### Firmware Update and DUT Detection / Configuration

- [X] Is MAX / Hardware Manager / System Configuration / SysAPI used to test the product?
    - [X] MAX
    - [ ] Hardware Manager
    - [ ] System Configuration / SysAPI / nisyscfg.*
- Are these tools used for DUT detection? **Yes**
- Are these tools used for DUT configuration? **Yes**
- Will MAX / Hardware Manager / System Configuration require an image update? **Yes**
- Are there alternate methods to detect and configure the DUT other than MAX / Hardware Manager / System Configuration? **Yes**

*Note: System Configuration's 2027 release is not Windows 7 compatible.*

### Set On First Use (SOFU) Impact

- For your product, how will SOFU and password setting be enabled?
  - Will there be a "set password" prompt at login? **Yes**
  - Will the provisioning script set a default password? **No**
- At what TestStand sequence step does the password need to be set?
  - **A new sequence step will be needed at the end to program and validate DUT info.**
- At what TestStand sequence step does the password need to be marked invalid so that the DUT falls back to SOFU?
  - **A new sequence step will be needed at the end to reset SOFU state.**

### Set On First Use (SOFU) and Retest / RMA

- Can the existing test handle RMA units with a password set? **Yes**
- What mechanism exists to force-clear any set password? (Wiping the firmware, etc.) **One will need to be added by SW team as part of GRD.**

### Late-Stage Firmware Update FVT Step

- Is a late-stage firmware update FVT step needed due to the complexity of the test solution? **No**

### Other Test Design Considerations

- No new hardware
- No Unique/EOL/LTB component concerns introduced by CRA

---

## Slide 10 - Test Station Capacity (3-Year) [By Planning Exit] ✅

> **Conditional:** Complete this slide only if the estimated test time delta **exceeds 10%** OR if station utilization is high. If skipping, document the reason here.

Skipped — test times are not expected to change (see Slide 31).

---

## Slide 11 - Cost [By Planning Exit, As Required] ✅

N/A - No new hardware or paid software licenses are introduced.

---

## Slide 12 - Test Solution Validation Plan [By Planning Exit] ✅

- Validation plan for CRA test changes:
    - Repeatability testing: minimum 10 runs per product family
    - TVR and MVR per product family (not required per individual PN)
- No regression testing required — no common code is being modified by CRA changes.
- RMA compatibility is guaranteed: the wipe-first RMA approach ensures pre-CRA units are fully re-provisioned; LinuxRT is guaranteed to be forward-updatable for all affected products.

---

## Slide 13 - RMA Support / MFG Services [By Planning Exit] ✅

- Pre-CRA units can be RMA'd on the updated test station. Units will receive the latest firmware as part of the repair process.
- As-found data is not captured. All products in this family reformat onboard storage during the RMA process — drive contents will be wiped regardless of encryption status. Customers concerned about data security are advised to encrypt their drives prior to return.
- RMA capability at satellite sites (including CSC) is not impacted. Sites that already have the hardware to handle these products can continue to do so.

---

## Slide 14 - Safety / Ergonomics [By Planning Exit, As Required] ✅

N/A - No new hardware is introduced.

---

## Slide 15 - Manufacturing Executive Summary [By Planning Exit] ✅

N/A - MFG Executive Summaries will be rolled up / maintained by master TSDR-Lite document.

---

## Slide 16 - Section: "Only Present If Required" Instructions [Ignore] ☑️

> *[Internal template slide - no content required]*

---

## Slide 17 - Product Spec Coverage [By Planning Exit] ✅

- Are the product specs affected by the CRA firmware update? No
- Are there any specs that cannot be tested due to the CRA change? No

---

## Slide 18 - Coverage Risks and Mitigations [By Planning Exit] ✅

N/A - No specifications are left uncovered as a result of the CRA change.

---

## Slide 19 - Long Lead Items [By Planning Exit, As Required] ✅

N/A - No new hardware is introduced.

---

## Slide 20 - Debug Solution [By Planning Exit] ✅

**"Set on First Use" Failure Debug:**
- Any product that has passed the SOFU/password step and subsequently failed can be rerun through the same test sequence. Nothing CRA or SOFU related is one-time programmable — the SOFU state is fully reversible by wiping the product during a retest.
- Full password reset mechanisms vary by product family. Refer to Slide 9 for the product-specific approach; authoritative details on any temporary passwords used during testing are documented in the product's test specification.

**General CRA Test Debug:**
- The production test solution is used for debug — no separate debug station or fixture is required.
- No additional hardware or software is required beyond what is used for standard production testing.

---

## Slide 21 - Maintenance & Spares [By Planning Exit] ✅

N/A - No new hardware is introduced.

---

## Slide 22 - Modernization [Not Required] ☑️

> **N/A - No modernization expectations for CRA-impacted products.** *However, any test changes made for CRA should be tracked so they can be carried forward into future modernization efforts.*

---

## Slide 23 - High-Cost Spares [By Planning Exit, As Required] ✅

N/A - No new hardware is introduced.

---

## Slide 24 - Test Eng. CapEx & AR (>$1k) Equipment List & Timeline [By Planning Exit, As Required] ✅

N/A - No new hardware is introduced.

---

## Slide 25 - Mfg. CapEx & AR (>$1k) Equipment List & Timeline [By Planning Exit, As Required] ✅

N/A - No new hardware is introduced.

---

## Slide 26 - Safety Risks Matrix [By Planning Exit, As Required] ✅

N/A - No new hardware is introduced.

---

## Slide 27 - Special Considerations [By Planning Exit, As Required] ✅

N/A - No special considerations for this product family.

---

## Slide 28 - Other [By Planning Exit] ✅

N/A

---

## Slide 29 - Section: "Pre-Read Only" Instructions [Ignore] ☑️

> *[Internal template slide - no content required]*

---

## Slide 30 - Required TSDR Invitees [By Definition Exit] ✅

Standard CRA TSDR-Lite invitees (Definition):

| Role | Name |
|---|---|
| R&D Test Engineer / CRA R&D TE Tech Lead | Phillip Conrad |
| Global Director of Mfg Test Engineering | Rasheel Karmacharya |
| Mfg Test Technical Lead | Seth Berry |
| Mfg Test Engineer | Tamas Zoltan Varga |
| HW Project/Program Manager | Trang Nguyen |
| Mfg Product Engineer (per site, NIH or PEN) | Bence Kovacs |

Standard CRA TSDR-Lite invitees (Planning):

| Role | Name |
|---|---|
| R&D Test Engineer / CRA R&D TE Tech Lead | Phillip Conrad |
| Global Director of Mfg Test Engineering | Rasheel Karmacharya |
| Mfg Test Technical Lead | Seth Berry |
| Mfg Test Engineer | Tamas Zoltan Varga |
| Mfg Test Engineer's Manager (per site, NIH or PEN) | Bence Kovacs |
| Mfg Liaison | Tameem Khan (PEN) |
| HW Services rep (for RMA/Cal impact discussion) | `<fill in>` |
| HW Project/Program Manager | Trang Nguyen |
| Mfg Product Engineer (per site, NIH or PEN) | Matyas Abuczki |

---

## Slide 31 - Estimated Test Times [By Planning Exit] ✅

The CRA changes for this product family are not expected to change test times beyond 10%. Capacity analysis (Slide 10) is not required.

---

## Slide 32 - Modernization: Comprehensive Test Asset Summary Table [Not Needed] ☑️

> **N/A - No modernization expectations for CRA-impacted products.**

---

## Slide 33 - Software [By Definition Exit] ✅

- Station Image: `538888F-005` (CONT_005)
- Station OS: Windows 7
- Testing Framework:
  - [X] BlueNITE
  - [ ] Ultimate II
  - [ ] Other
- LabVIEW Version: `2016`
- TestStand Version: `2012`
- System Configuration (NI-RIO) Version: `2016`

**Test Assets:**

| Product(s) | Supported Product List | Test Set | Test Procedure | Test Station | Test Station Description |
|---|---|---|---|---|---|
| cDAQ-9183/9185/9187/9189 | 539839A-02 | 539839A-01 | TP9839-FVT | 534829C-021 (OPT 1) / 534829H-02 (OPT 2) | Controllers-21 Series UTS 2013 / Controllers UTS 2011 |

---

## Slide 34 - Software (Cont'd) [By Definition Exit] ✅

- Station Callback update required? **No**
- Calibration requirements changed due to CRA firmware update? **No**
- MFG pain-points with the updated SW solution (collect feedback from MFG TE): **N/A**

---

## Slide 35 - Knowledge / Best Practices Sharing [By Planning Exit] ✅

- Create training for MFG/RMA technicians on the SOFU process and CRA firmware update procedures.
