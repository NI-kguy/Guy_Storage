# CRA Password Requirements & Firmware Assessment Discussion

**Meeting Date:** May 15, 2026
**Participants:** Phillip Conrad, TM-A1.111 - Penang (Koay), Yeoh Audrey
**Absent:** Sun, Brian, Guy (in interviews / out)

---

## 1. Overview — Cyber Resilience Act (CRA)

- The **Cyber Resilience Act (CRA)** is an EU regulation requiring products to meet specific cybersecurity requirements before being shipped to the EU market.
- **Compliance deadline: December 11, 2027.**
- Scope is **not all products** — only a specific, identified set of products are subject to CRA.

---

## 2. Product Scope & Inclusions

- The team reviewed a product list to determine which products fall under CRA.
- Products must be **internet-connected devices with a microcontroller** to be considered in scope.
- Phillip agreed to provide a **one-sentence definition/criteria** after the meeting to help the team identify whether a product needs CRA treatment.

### Products NOT Requiring CRA

| Product                                      | Reason                                                      |
| -------------------------------------------- | ----------------------------------------------------------- |
| Line item 135 (PCI form factor / simulating) | Ethernet cards in PCI form factor — not in scope           |
| SRC                                          | Uses Kate; CRA handled at the Kate level, so SRC is covered |

> **Exception for SRC:** If SRC is reflashing Kate with an SLSC image, it may need separate CRA consideration.

### Products with Uncertainty

- **Digilent FPGA development boards** — Some models include an internet port and are not explicitly listed. Phillip noted they may be going **EOL (End of Life)**, which would exclude them.
- **Virtual Bench** and **MCC products** — Were noted as being on the list.

---

## 3. New Product — Code Name "Khan Khan" (Next-Gen MPG/FPGA)

- A new next-generation FPGA product (code name **Khan Khan**) is in development with an estimated release around **mid-2027**.
- It **does require CRA compliance**.
- Since both the product and its test solution are still in development, surprises are not expected — CRA requirements should be built in from the start.
- **Concern raised:** No one may have explicitly informed the product team that Khan Khan needs CRA compliance.
- The Penang team will follow up with the relevant team to ensure they are aware of the CRA requirement.

> *"If that releases without CRA compliance, that's the product team that has dropped the ball."* — Phillip Conrad

---

## 4. Action Items

| # | Action                                                                                    | Owner            | Status        |
| - | ----------------------------------------------------------------------------------------- | ---------------- | ------------- |
| 1 | Write a one-sentence definition/criteria to identify which products require CRA treatment | Phillip Conrad   | After meeting |
| 2 | Review the product sheet shared in the meeting invite and work through individual items   | Penang Team      | Ongoing       |
| 3 | Ping Phillip for any questions about individual items on the sheet                        | All team members | Ongoing       |
| 4 | Inform the Khan Khan product team that their new product must be CRA compliant            | Penang (Koay)    | To do         |

---

## 5. Key Takeaways

- CRA compliance deadline is **December 11, 2027** for EU-shipped products.
- Not all products are in scope — scope is limited to internet-connected devices with microcontrollers.
- Products already covered under another platform (e.g., SRC via Kate) do not need separate CRA treatment unless they use a different image.
- New products in development (e.g., Khan Khan) must have CRA compliance built in before release.
- Test Engineering often serves as the team that surfaces these compliance requirements to product teams.
