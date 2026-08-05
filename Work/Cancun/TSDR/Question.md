1. Have we validated station capacity using the latest Kinaxis unconstrained upside forecast and demonstrated sufficient margin through ramp? Have you and William discussed clarity on test system that will be used and when will capacity modelling be available for that station? Until that is answered, the station count and CAPEX may be wrong.

   **[Ans] Will work will William to get the capacity using the Kinaxis.**
2. Key Risks to On Time Release - Very low time to respond between Repeatability, TVR and MVR. Could you add some margin so that there is enough time to respond to the actions coming from one to the next?

   **[Ans] The timeline not yet confirm yet. Will work with Stack to get the confirm date.**
3. Several news may add up to risks. Have you considered what can be re-used from existing fixtures, stations etc.?

   1. No leverage of existing test design
      * **[Ans] Existing Digilent product is using the digilent User Interface. Now, the product already migrated to PEN. New Digilent product need to use NI User Interface. So, I cannot leverage test design from existing product.**
   2. New workstation
      * **[Ans] The Digilent line does not have existing workstation for the new station. it need to have one workstation to put the test station. (show the picture)**
   3. New Station and fixture
      * **[Ans] Test Station used for existing existing Digilent product is obsolated and new station need to be introduce for this product. However, the station design is simple and the risk is low.**
      * **[Ans] No Test Fixture can be reuse for this product.**
   4. New software image
      * **[Ans] I will have new Test Image since new drivers needed to support the testing.**
   5. New validation effort
      * **[Ans] No Much addition validation on the station side. all the instruments/accossories are inside the Test Fixture. Only Test Fixture Validation needed.**
4. Debug Strategy Is weakly defined - Leverage production solution is usually a bad idea to start to plan with. You need to define plan for debug without affecting the MFG line. And hence what test costs will be affected if you need to reproduce production issue?

   **[Ans] Debug not going to use the Test Fixture for debugging. It will have their own parts. The detail are in below**

   **[MFG] Test Fixture consists all the test accessories.
   [Debug] There is no test fixture, but all test accessories are provided, giving the debug engineer the flexibility to perform debugging.**

   1. Coverage Risks – Some of the coverage risk that you have mentioned might have higher impact and may need to spend some time on mitigation options.
      **[Ans] The Coverage Risk in the TSDR are not applicable. The content is just an example. I have removed the content to don't make confusion to reviewer.**

      1. Such as if there is any strategy on supplier tested parts, or may be a base test equipment that can isolate part issue like voltage regulator and FPGA, FX3, microcontroller or flash.
      2. You mention on SMU sense voltage measurement may differ to what DUT measures, and not able to test / calibrate up to the requirement. If they deviate significantly is there a station maintenance plan that can detect it before invalidating the measurements on multiple DUTs?
         * **[Ans] The ITA and station usage counts are logged and tracked. Once a count reaches its defined threshold, it triggers a scheduled maintenance to recalibrate the station before the measurements are invalidated.**
5. Question: What is your confidence level that fixture, software, and debug readiness will be available before repeatability in April 2027?

 **[Ans] Will get back to you later.**
