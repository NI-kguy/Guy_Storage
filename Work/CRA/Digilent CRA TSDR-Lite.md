# CRA TSDR-Lite - Test Solution Design Review Template

> **Based on:** [TSDR v18.0](https://emerson.sharepoint.com/sites/TM-TestEngineering/Template Library/TEP Required Documents/Files/TSDR - Test System Design Review.pptx)

> **Purpose:** Accelerated TSDR template for CRA-impacted products. Scope is limited to CRA-driven changes only - not a full product TSDR. Present one deck per product family. TEs may merge related product families into a single TSDR when appropriate (e.g., related controllers or chassis within the same manufacturing unit). Use judgment and coordinate with Phillip Conrad. Owning TE fills out slides; Phillip Conrad reviews for consistency across families.
>
> There will be two reviews:
>
> - One that gates Definition Exit - Should be held asynchronously
> - One that gates Planning Exit - Can be held asynchronously if agreed on by stakeholders
>
> **Ground rules:**
>
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
> Additionally, a high-level effort estimate (manhours) is required by Definition Exit to support PSG labor cost planning. A detailed project plan with granular timeline is not required here, but should be maintained separately for Level Up activities.
>
> *For viewing and editing, use [Visual Studio Code](https://code.visualstudio.com/download): press **Ctrl+Shift+V** for a rendered preview, or **Ctrl+K V** to view side-by-side. Non-programmers can use [Obsidian](https://obsidian.md/) as an alternative. MFG TEs without either tool can drag the file into a browser for read-only viewing.*
>
> **Progress tracking:** Each slide heading has a status emoji. Update it as you go: ❌ = not yet complete, ✅ = complete.

---

## Slide 1 - Presentation Title [Ignore]  ☑️

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

**Digilent MCC** - CRA TSDR-Lite

---

## Slide 6 - Product Overview [By Definition Exit] ✅

- Product Family: **Digilent MCC**
- Owning TE:  Guy Kang Guan
- Date: 2026-08-05
- CRA Change Classification *(select one)*:
  - [ ] Drop-in updatable (minimal test impact)
  - [X] Requires some rework, but manageable
  - [ ] Needs new late-stage firmware update FVT step
  - [ ] Problem product - needs special attention

**Product Family Description:**

The Digilent MCC (Measurement Computing Corporation) product family consists of data acquisition (DAQ) and measurement devices offered in a range of connectivity options, including USB, Ethernet, and Wi-Fi. The family covers multifunction DAQ boards, analog and digital I/O modules, temperature and voltage measurement devices, and counter/timer products.

These products serve test, measurement, and control applications across industrial, laboratory, and OEM environments. Depending on the connectivity option, they interface with a host either directly over USB or over a network connection.

CRA primarily impacts the network-connected Ethernet modules, as these devices expose a network interface and therefore fall within the scope of the CRA cybersecurity requirements. USB-only devices are not affected by the network-facing requirements.

**Products impacted in this Family:**

| Model Number      | Test Set   | Notes                                                           |
| ----------------- | ---------- | --------------------------------------------------------------- |
| E-1608/E-1608-OEM | 537650A-42 | 156715C-01L, 156715C-02L (OEM) -<br />Ethernet analog input DAQ |
| E-DIO24           | 537650A-52 | 140476B-01L - Ethernet digital I/O                              |
| E-TC              | 537653A-01 | 159078A-01L - Ethernet thermocouple input                      |
| E-TC-32           | 539426A-02 | 157715C-01L - Ethernet 32-channel thermocouple input            |

**Known Test Challenges:**

- None

---

## Slide 7 - Project Milestones [By Planning Exit] ❌

> *Provide the schedule. This is a primary focus of the CRA TSDR-Lite.*

- Expected CRA firmware release date: `<fill in>`
- Target Test Solution completion date: `<fill in>`
- Target FVT / TVR / MVR dates: `<fill in>`

> *Call out any known schedule risks*

---

## Slide 8 - Test Routing / Flow [By Definition Exit] ✅

**Impacted BN Test Suites / Routing Steps:**

| Routing Step | BN Test Suite or U2 Path                                     | Notes                             |
| ------------ | ------------------------------------------------------------ | --------------------------------- |
| FVT140       | U2:`T:\Ultimate II\U2Products\MCC\Sequences\<product>.seq` | Program unique passcode to EEPROM |
| RMA300       | U2:`T:\Ultimate II\U2Products\MCC\Sequences\<product>.seq` | RMA routing                       |

> *`<product>` = E-1608, E-DIO24, E-TC, or TC-32*

**Additional Routing Steps Introduced by CRA:**

None.

---

## Slide 9 - Test Design [By Definition Exit] ✅

> *The following slide is detailed and may need to be split into multiple sections. Focus on CRA-driven changes to test design only.*

**See "Software" slide for station image software information.**

### Program Unique Passcode to EEPROM

Digilent MCC Ethernet products provide a passcode that is stored in the EEPROM. The default value is currently "0" (all-zero). With CRA, each device will be configured with a unique internal password during the FVT test, ensuring that no unit is shipped with the default all-zero password.

Customers will not be provided with an initial password. Instead, upon first use, they will be instructed to use the reset button on the rear of the device to reset the credentials and establish their own password. This solution leverages existing product functionality, provides a simple and intuitive customer experience, and avoids the need for more complex manufacturing processes while maintaining a secure out-of-box configuration.

- What test steps to program the inique passcode?

  - FVT-140/RMA-300 - Program a unique internal password to EEPROM
- How to program the unique passcode?

  - [X] Via Ethernet/USB.
- Will changing the shipping product firmware change how the test functions?

  - No firmware change, the product function will not change.
- Is the update "drop-in" (no test sequence changes required)?

  - No — need to add a step to reset the passcode at the beginning of the sequence, and a step to program the passcode after all tests complete.
- Will changing the shipping product firmware require additional software/image changes (new driver, new FVT sequence, etc.)?

  - New driver - **No**
  - New FVT Sequence - **No**

### Firmware Update and DUT Detection / Configuration

* Is MAX / Hardware Manager / System Configuration / SysAPI used to test the product?
  * Digilent MCC does not use any of the tools listed.

*Note: System Configuration's 2027 release is not Windows 7 compatible.*

### Program Unique Passcode Impact

* For your product, how will the passcode need to be programmed?
  * FVT-140: the Program Passcode to EEPROM step will be added to the sequence after all the tests is completed.

### Program Unique Passcode - Retest / RMA

- Can the existing test handle RMA units with a passcode set?
  - Yes, but operator need to press reset button manually.
- What mechanism exists to force-clear any set password? (Wiping the firmware, etc.)
  - A reset-passcode step will be added at the beginning of the test sequence.

### Late-Stage Firmware Update FVT Step

- Is a late-stage firmware update FVT step needed due to the complexity of the test solution? If so, describe approach.
  - No

### Other Test Design Considerations

- No new hardware
- No Unique/EOL/LTB component concerns introduced by CRA

---

## Slide 10 - Test Station Capacity (3-Year) [By Planning Exit] ✅

> **Conditional:** Complete this slide only if the estimated test time delta **exceeds 10%** OR if station utilization (per utilization dashboard) is high enough that even a small delta is a concern. If skipping, document the reason here.

N/A - Not needed.

---

## Slide 11 - Cost [By Planning Exit, As Required] ✅

> **N/A if no new hardware or paid software licenses are introduced.** *If new hardware or software licenses are required to complete the CRA change, complete per standard TSDR guidance.*

 N/A - No new hardware or paid software licenses are introduced.

---

## Slide 12 - Test Solution Validation Plan [By Planning Exit] ✅

- Validation plan for CRA test changes:
  - Repeatability testing: minimum 10 runs per product family
  - TVR and MVR per model. (They use different test seq)
- No regression testing required — no common code is being modified by CRA changes.
- RMA share the FVT test seq, no additional validation needed.

---

## Slide 13 - RMA Support / MFG Services [By Planning Exit] ✅

- Can pre-CRA units be RMA'd on the updated test station? (backwards compatibility)

  - Yes, Reset Passcode step can also apply to pre-CRA units and program unique passcode to be run as well.
- Special RMA instructions related to CRA (e.g., password/credential handling on returned units)

  - No.
- RMA capability at satellite sites - upgrade plan required?

  - No upgrade required.

---

## Slide 14 - Safety / Ergonomics [By Planning Exit, As Required] ✅

> **N/A if no new hardware is introduced.** *If new hardware is required to complete the CRA change, complete per standard TSDR guidance.*

N/A - No new hardware is introduced.

---

## Slide 15 - Manufacturing Executive Summary [By Planning Exit] ✅

> *Executive Summaries will be rolled up / maintained by master TSDR-Lite document*

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

**"Unique Passcode" Failure Debug:**

- Skip the "Program Passcode to EEPROM" step If any tests fail in test seq. Debug Engineer can debug the module as previous.

**General CRA Test Debug:**

- The production test solution is used for debug — no separate debug station or fixture is required.
- No additional hardware or software is required beyond what is used for standard production testing.

---

## Slide 21 - Maintenance & Spares [By Planning Exit] ✅

N/A - No new hardware is introduced.

---

## Slide 22 - Modernization [Not Required] ☑️

> **N/A - No modernization expectations for CRA-impacted products.** *However, any test changes made for CRA should be tracked so they can be carried forward into future modernization efforts. If an active modernization project already exists for this product family, coordinate with the modernization TE to ensure CRA changes are not in conflict.*

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

- N/A

---

## Slide 29 - Section: "Pre-Read Only" Instructions [Ignore] ☑️

> *[Internal template slide - no content required]*

---

## Slide 30 - Required TSDR Invitees [By Definition Exit] ✅

Standard CRA TSDR-Lite invitees (Definition):

| Role                                        | Name                |
| ------------------------------------------- | ------------------- |
| R&D Test Engineer / CRA R&D TE Tech Lead    | Phillip Conrad      |
| Global Director of Mfg Test Engineering     | Rasheel Karmacharya |
| Mfg Test Technical Lead                     | Seth Berry          |
| Mfg Test Engineer                           | Csorvasi, Sandor    |
| HW Project/Program Manager                  | Kovacs, Benc        |
| Mfg Product Engineer (per site, NIH or PEN) | Abuczki, Matyas     |

Standard CRA TSDR-Lite invitees (Planning):

| Role                                               | Name                |
| -------------------------------------------------- | ------------------- |
| R&D Test Engineer / CRA R&D TE Tech Lead           | Phillip Conrad      |
| Global Director of Mfg Test Engineering            | Rasheel Karmacharya |
| Mfg Test Technical Lead                            | Seth Berry          |
| Mfg Test Engineer                                  | Csorvasi, Sandor    |
| Mfg Test Engineer's Manager (per site, NIH or PEN) | Kovacs, Benc        |
| Mfg Liaison                                        | Tameem Khan (PEN)   |
| HW Services rep (for RMA/Cal impact discussion)    | N/A                 |
| HW Project/Program Manager                         | Francis, Danya      |
| Mfg Product Engineer (per site, NIH or PEN)        | Abuczki, Matyas     |

---

## Slide 31 - Estimated Test Times [By Planning Exit] ✅

The CRA changes for this product family are not expected to change test times beyond 10%. Capacity analysis (Slide 10) is not required.

---

## Slide 32 - Modernization: Comprehensive Test Asset Summary Table [Not Needed] ☑️

> **N/A - No modernization expectations for CRA-impacted products.**

---

## Slide 33 - Software [By Definition Exit] ✅

- Station Image:  `<fill in>`
- Station OS: `Windows 7 32-bit`
- Testing Framework:
  - [ ] BlueNITE
  - [X] Ultimate II
  - [ ] Other
- LabVIEW Version: `LabVIEW 2013`
- TestStand Version: `Teststand 2010`
- System Configuration Version: `14.0`

**Test Assets:**

| Product(s)       | Supported Product List | Test Set   | Test Procedure | Test Station             | Test Station Description                    |
| ---------------- | ---------------------- | ---------- | -------------- | ------------------------ | ------------------------------------------- |
| TC-32            | 539426A-02             | 539426A-01 | TP2576-FVT1    | 533486E-00 & 533486C-001 | STATION TYPE FOR CRIO MODULES AND WSN NODES |
| E-TC             | 537653A-01             | 537653A-00 | TP2613-FVT1    | 533486E-00 & 533486C-001 | STATION TYPE FOR CRIO MODULES AND WSN NODES |
| E-1608/E1608-OEM | 537650A-42             | 537650A-40 | TP2531-FVT1    | 533486E-00 & 533486C-001 | STATION TYPE FOR CRIO MODULES AND WSN NODES |
| E-DIO24          | 537650A-52             | 537650A-50 | TP2586-FVT1    | 533486E-00 & 533486C-001 | STATION TYPE FOR CRIO MODULES AND WSN NODES |

---

## Slide 34 - Software (Cont'd) [By Definition Exit] ✅

- Station Callback update required?  **No**
- Calibration requirements changed due to CRA firmware update?  **No**
- MFG pain-points with the updated SW solution (collect feedback from MFG TE) **N/A**

---

## Slide 35 - Knowledge / Best Practices Sharing [By Planning Exit] ✅

- No change on the FVT & RMA. However, TE can provide a session to teach MFG/RMA Engineer to reset the passcode.
