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

## Slide 5 - Title Slide [By Definition Exit] ❌

`<Product Family>` CRA TSDR-Lite

---

## Slide 6 - Product Overview [By Definition Exit] ❌

- Product Family: `<fill in>`
- Owning TE: `<fill in>`
- Date: `<fill in>`
- CRA Change Classification *(select one)*:
  - [ ] Drop-in updatable (minimal test impact)
  - [ ] Requires some rework, but manageable
  - [ ] Needs new late-stage firmware update FVT step
  - [ ] Problem product - needs special attention

**Product Family Description:**

> *Provide only basic product information. Full product design detail is not required for CRA TSDR-Lite.*

`<Describe the product family - what it is, its general test approach, and how it is impacted by CRA>`

**Products in this Family:**

> *List product name(s) / model numbers in this family.*

| Model Number  | Test Set | Notes |
| ------------- | -------- | ----- |
| `<fill in>` |          |       |

**Known Test Challenges:**

> *Any known test challenges specific to this product family and the CRA change.*

- `<fill in>`

> *If no new hardware is introduced, assembly drawings and layout slides are N/A.*

---

## Slide 7 - Project Milestones [By Planning Exit] ❌

> *Provide the schedule. This is a primary focus of the CRA TSDR-Lite.*

- Expected CRA firmware release date: `<fill in>`
- Target Test Solution completion date: `<fill in>`
- Target FVT / TVR / MVR dates: `<fill in>`

> *Call out any known schedule risks*

---

## Slide 8 - Test Routing / Flow [By Definition Exit] ❌

> *Show the full test routing for this product family, highlighting CRA-impacted steps. Full routing detail is not required - delta from current routing is sufficient.*

**Impacted BN Test Suites / Routing Steps:**

| Routing Step  | BN Test Suite or U2 Path | Notes |
| ------------- | ------------------------ | ----- |
| `<fill in>` |                          |       |

> *For each impacted routing step, describe how the CRA change affects it (e.g., routing step modified, routing step removed, password/credential now set here).*

**Additional Routing Steps Introduced by CRA:**

| Routing Step  | Test Suite or U2 Path | Notes |
| ------------- | --------------------- | ----- |
| `<fill in>` |                       |       |

> *Highlight where in the routing the CRA password/credential is set. Call out any impact to the RMA routing flow.*

---

## Slide 9 - Test Design [By Definition Exit] ❌

> *The following slide is detailed and may need to be split into multiple sections. Focus on CRA-driven changes to test design only. I have tried to add enough leading questions to assist a TE in making critical evaluations of their product's current setup and how it relates to CRA. However, the TE should not limit themselves to just these questions and think critically about the problem.*

**See "Software" slide for station image software information.**

### Firmware Update to Support CRA SOFU

> *List required information to scope the firmware update.*

- What test steps update the shipping product firmware?
- How is the shipping product firmware provisioned?
  - [ ] Via provisioning script (possibly on removable media)
  - [ ] Via FTP or SCP (or other transfer protocol)
  - [ ] Via JTAG-Bootstrap + TFTP
  - [ ] Via ICT direct programming
  - [ ] Via preprogrammed parts
  - [ ] Via MAX / Hardware Manager / System Configuration
  - [ ] Via auto-update mechanism (i.e. "click update button")
  - [ ] Via other mechanism: __________
- Is the shipping product firmware used to test the product?
  - [ ] Full Testing (booting into the shipping firmware to run a significant number of tests)
  - [ ] Partial Testing (booting into the shipping firmware to run some critical tests)
  - [ ] Only final verification steps (correct FW, SN, PN, etc.)
- Will changing the shipping product firmware change how the test functions?
- Is the update "drop-in" (no test sequence changes required)?
- Will changing the shipping product firmware require additional software/image changes (new driver, new FVT sequence, etc.)?
- Can a firmware update be added at the very end of the IFT/FVT test sequence apart from the existing firmware update procedure?

### Firmware Update and DUT Detection / Configuration

> *List required information to scope the DUT detection and configuration.*

- [ ] Is MAX / Hardware Manager / System Configuration / SysAPI used to test the product?
  - [ ] MAX
  - [ ] Hardware Manager
  - [ ] System Configuration / SysAPI / nisyscfg.*

- Are these tools used for DUT detection?
- Are these tools used for DUT configuration?
- Will MAX / Hardware Manager / System Configuration require an image update?
- Are there alternate methods to detect and configure the DUT other than MAX / Hardware Manager / System Configuration?

*Note: System Configuration's 2027 release is not Windows 7 compatible.*

### Set On First Use (SOFU) Impact

> *List required information to scope the SOFU impact of setting a password and clearing the password before shipping out to the customer.*

- For your product, how will SOFU and password setting be enabled?
  - Will there be a "set password" prompt at login?
  - Will the provisioning script set a default password?
- At what TestStand sequence step does the password need to be set?
- At what TestStand sequence step does the password need to be marked invalid so that the DUT falls back to the out-of-box experience (SOFU)?

### Set On First Use (SOFU) and Retest / RMA

> *List required information to scope the SOFU impact of retesting a unit, including cases where the customer has set a unique password.*

- Can the existing test handle RMA units with a password set?
  - If no, how can the existing test be modified to support this?
- What mechanism exists to force-clear any set password? (Wiping the firmware, etc.)

### Late-Stage Firmware Update FVT Step

- Is a late-stage firmware update FVT step needed due to the complexity of the test solution? If so, describe approach.

### Other Test Design Considerations

- Any new test equipment required? *(If none, state "No new hardware")*
- Any Unique/EOL/LTB component concerns introduced by CRA

---

## Slide 10 - Test Station Capacity (3-Year) [By Planning Exit] ❌

> **Conditional:** Complete this slide only if the estimated test time delta **exceeds 10%** OR if station utilization (per utilization dashboard) is high enough that even a small delta is a concern. If skipping, document the reason here.

If completing:

- Test station name and description
- Current test time vs. new estimated test time (delta %)
- Station utilization (check utilization dashboard)
- Three-year capacity vs. forecast (5-day, 2-shift model)
- Duplication plan if capacity is at risk

---

## Slide 11 - Cost [By Planning Exit, As Required] ❌

> **N/A if no new hardware or paid software licenses are introduced.** *If new hardware or software licenses are required to complete the CRA change, complete per standard TSDR guidance.*

 N/A - No new hardware or paid software licenses are introduced.

---

## Slide 12 - Test Solution Validation Plan [By Planning Exit] ❌

- What validation is planned for the CRA test changes?
- Regression testing scope for existing test steps
- How will compatibility with pre-CRA RMA units be verified?
- Are MVR/PRT units available for validation?
- List any known risks and mitigations.

---

## Slide 13 - RMA Support / MFG Services [By Planning Exit] ❌

> *This is a primary focus area. Address fully.*

- Test routing for RMA of CRA-impacted products
- Can pre-CRA units be RMA'd on the updated test station? (backwards compatibility)
- Special RMA instructions related to CRA (e.g., password/credential handling on returned units)
- Do we want to capture as-found data for CRA-impacted returns?
- RMA capability at satellite sites - upgrade plan required?
- CSC support implications
- Work with HW Services to determine ramp-up plan based on forecast
- What happens when a customer RMAs a product - how is the product wiped?

---

## Slide 14 - Safety / Ergonomics [By Planning Exit, As Required] ❌

> **N/A if no new hardware is introduced.** *If new hardware is required to complete the CRA change, complete per standard TSDR guidance.*

N/A - No new hardware is introduced.

---

## Slide 15 - Manufacturing Executive Summary [By Planning Exit] ❌

> *Executive Summaries will be rolled up / maintained by master TSDR-Lite document*

N/A - MFG Executive Summaries will be rolled up / maintained by master TSDR-Lite document.

---

## Slide 16 - Section: "Only Present If Required" Instructions [Ignore] ☑️

> *[Internal template slide - no content required]*

---

## Slide 17 - Product Spec Coverage [By Planning Exit] ❌

> **Simplified for CRA TSDR-Lite.** *Address only specs impacted by the CRA change.*

- Are the product specs affected by the CRA firmware update? `<yes/no>`
- Are there any specs that cannot be tested due to the CRA change? `<yes/no>`

---

## Slide 18 - Coverage Risks and Mitigations [By Planning Exit] ❌

> *List any product specifications that will **NOT** be covered as a result of the CRA change, along with mitigation plans.*

---

## Slide 19 - Long Lead Items [By Planning Exit, As Required] ❌

> **N/A if no new hardware is introduced.** *If new hardware is required, list long lead items here.*

---

## Slide 20 - Debug Solution [By Planning Exit] ❌

> *This is a primary focus area. Address fully.*

**"Set on First Use" Failure Debug:**

- What is the debug process if a product fails after the CRA "set on first use" step has been triggered?
- Can the credential/password be reset for debug purposes? What is the process?
- What tools, VIs, or procedures are needed to debug a failed unit in this state?
- Who owns this debug process at the factory?
- Is there a separate debug station/fixture required?

**General CRA Test Debug:**

- Leveraging production test solution for debug?
- Any special equipment needed for CRA-related failures?

---

## Slide 21 - Maintenance & Spares [By Planning Exit] ❌

> **N/A if no new hardware is introduced.** *If new hardware is required to complete the CRA change, complete per standard TSDR guidance.*

N/A - No new hardware is introduced.

---

## Slide 22 - Modernization [Not Required] ☑️

> **N/A - No modernization expectations for CRA-impacted products.** *However, any test changes made for CRA should be tracked so they can be carried forward into future modernization efforts. If an active modernization project already exists for this product family, coordinate with the modernization TE to ensure CRA changes are not in conflict.*

---

## Slide 23 - High-Cost Spares [By Planning Exit, As Required] ❌

> **N/A if no new hardware is introduced.** *If new hardware is required to complete the CRA change, complete per standard TSDR guidance.*

N/A - No new hardware is introduced.

---

## Slide 24 - Test Eng. CapEx & AR (>$1k) Equipment List & Timeline [By Planning Exit, As Required] ❌

> **N/A if no new hardware is introduced.** *If new hardware is required to complete the CRA change, complete per standard TSDR guidance.*

N/A - No new hardware is introduced.

---

## Slide 25 - Mfg. CapEx & AR (>$1k) Equipment List & Timeline [By Planning Exit, As Required] ❌

> **N/A if no new hardware is introduced.** *If new hardware is required to complete the CRA change, complete per standard TSDR guidance.*

N/A - No new hardware is introduced.

---

## Slide 26 - Safety Risks Matrix [By Planning Exit, As Required] ❌

> **N/A if no new hardware is introduced.** *If new hardware is required to complete the CRA change, complete per standard TSDR guidance.*

N/A - No new hardware is introduced.

---

## Slide 27 - Special Considerations [By Planning Exit, As Required] ❌

> **Conditional:** *Complete this slide only if there are other considerations that need mentioning.*

Address any CRA-specific considerations not covered elsewhere:

- Any products in this family that deviate from the family-level approach and need individual attention
- Environmental or facility concerns introduced by CRA changes

---

## Slide 28 - Other [By Planning Exit] ❌

- Any CRA-specific licensed items or controlled functionality
- Any additional debug solution details not captured in Slide 20

---

## Slide 29 - Section: "Pre-Read Only" Instructions [Ignore] ☑️

> *[Internal template slide - no content required]*

---

## Slide 30 - Required TSDR Invitees [By Definition Exit] ❌

Standard CRA TSDR-Lite invitees (Definition):

- R&D Test Engineer: `<fill in>`
- CRA R&D TE Tech Lead: Phillip Conrad
- Global Director of Mfg Test Engineering: Rasheel Karmacharya
- Mfg Test Technical Lead: Seth Berry
- Mfg Test Engineer: `<fill in>`
- HW Project/Program Manager: `<fill in>`
- Mfg Product Engineer (per site, NIH or PEN)

Standard CRA TSDR-Lite invitees (Planning):

- R&D Test Engineer: `<fill in>`
- CRA R&D TE Tech Lead: Phillip Conrad
- Global Director of Mfg Test Engineering: Rasheel Karmacharya
- Mfg Test Technical Lead: Seth Berry
- Mfg Test Engineer: `<fill in>`
- Mfg Test Engineer's Manager (per site, NIH or PEN)
- Mfg Liaison: Peter Veres (NIH), Tameem Khan (PEN)
- HW Services rep (for RMA/Cal impact discussion): `<fill in>`
- HW Project/Program Manager: `<fill in>`
- Mfg Product Engineer (per site, NIH or PEN)

---

## Slide 31 - Estimated Test Times [By Planning Exit] ❌

Provide current vs. estimated new test times - this drives the Slide 10 capacity analysis decision.

| Routing Step | Current Test Time | Estimated New Test Time | Delta | Delta % |
| ------------ | ----------------- | ----------------------- | ----- | ------- |
|              |                   |                         |       |         |

> If total delta is ≤ 10% **and** station utilization is low, capacity analysis (Slide 10) may be skipped. Document the decision.

---

## Slide 32 - Modernization: Comprehensive Test Asset Summary Table [Not Needed] ☑️

> **N/A - No modernization expectations for CRA-impacted products.**

---

## Slide 33 - Software [By Definition Exit] ❌

> *Focus on CRA-driven software changes only.*

- Station Image:  `<fill in>`
- Station OS: `<fill in>`
- Testing Framework:
  - [] BlueNITE
  - [] Ultimate II
  - [] Other
- LabVIEW Version: `<fill in>`
- TestStand Version: `<fill in>`
- System Configuration Version: `<fill in>`

Other products tested on the image NOT IMPACTED BY CRA:

| Routing Step  | Test Suite or U2 Path | Notes |
| ------------- | --------------------- | ----- |
| `<fill in>` |                       |       |

---

## Slide 34 - Software (Cont'd) [By Definition Exit] ❌

- Station Callback update required?  `<fill in>`
- Calibration requirements changed due to CRA firmware update?  `<fill in>`
- MFG pain-points with the updated SW solution (collect feedback from MFG TE)

---

## Slide 35 - Knowledge / Best Practices Sharing [By Planning Exit] ❌

- Training needed for MFG/RMA technicians on CRA-related test changes
- "Set on first use" process: ensure Debug tech, MFG Test, and RMA tech all understand the failure debug workflow (see Slide 20)
- Special handling requirements introduced by CRA
- Documentation to be handed off to MFG (links to runbooks, VIs, debug guides)
