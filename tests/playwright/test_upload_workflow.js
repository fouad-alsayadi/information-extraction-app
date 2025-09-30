const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  // Launch browser
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  const page = await context.newPage();

  try {
    console.log('1. Navigating to the app...');
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: '/tmp/claude/step1_homepage.png', fullPage: true });
    console.log('Screenshot saved: step1_homepage.png');

    console.log('2. Navigating to Upload Documents page...');
    // Look for upload or upload documents link/button
    const uploadButton = await page.locator('text=Upload').or(page.locator('text=Upload Documents')).or(page.locator('[href*="upload"]')).first();
    if (await uploadButton.isVisible()) {
      await uploadButton.click();
      await page.waitForLoadState('networkidle');
    } else {
      // Try to navigate directly to upload page
      await page.goto('http://localhost:5173/upload');
      await page.waitForLoadState('networkidle');
    }
    await page.screenshot({ path: '/tmp/claude/step2_upload_page.png', fullPage: true });
    console.log('Screenshot saved: step2_upload_page.png');

    console.log('3. Creating a new extraction job...');
    // Look for job name input
    const jobNameInput = await page.locator('input[placeholder*="job" i], input[placeholder*="name" i], input[name*="name" i], input[id*="name" i]').first();
    if (await jobNameInput.isVisible()) {
      await jobNameInput.fill('Receipt Test Job');
      console.log('Filled job name: Receipt Test Job');
    }
    await page.screenshot({ path: '/tmp/claude/step3_job_name.png', fullPage: true });
    console.log('Screenshot saved: step3_job_name.png');

    console.log('4. Selecting schema...');
    // Look for schema dropdown or select
    const schemaSelect = await page.locator('select, [role="combobox"]').or(page.locator('button').filter({ hasText: /schema/i })).or(page.locator('button').filter({ hasText: /select/i })).first();
    if (await schemaSelect.isVisible()) {
      await schemaSelect.click();
      await page.waitForTimeout(1000);

      // Look for the "Receipt Processing Test" option
      const receiptOption = await page.locator('text=Receipt Processing Test').or(page.locator('option:has-text("Receipt Processing Test")')).first();
      if (await receiptOption.isVisible()) {
        await receiptOption.click();
        console.log('Selected Receipt Processing Test schema');
      } else {
        console.log('Receipt Processing Test schema not found, looking for any available schemas...');
        await page.screenshot({ path: '/tmp/claude/step4_schema_options.png', fullPage: true });
      }
    }
    await page.screenshot({ path: '/tmp/claude/step4_schema_selected.png', fullPage: true });
    console.log('Screenshot saved: step4_schema_selected.png');

    console.log('5. Creating test files for upload...');
    // Create sample test files
    const testFilesDir = '/tmp/claude/test_documents';
    if (!fs.existsSync(testFilesDir)) {
      fs.mkdirSync(testFilesDir, { recursive: true });
    }

    const testFile1 = path.join(testFilesDir, 'receipt1.txt');
    const testFile2 = path.join(testFilesDir, 'receipt2.txt');

    fs.writeFileSync(testFile1, `RECEIPT #12345
Date: 2023-12-01
Store: Coffee Shop ABC
Items:
- Latte: $4.50
- Muffin: $3.25
Total: $7.75
Payment: Credit Card`);

    fs.writeFileSync(testFile2, `INVOICE #67890
Date: 2023-12-02
Vendor: Office Supplies Inc
Items:
- Pens (10x): $15.00
- Paper (5 reams): $25.00
Subtotal: $40.00
Tax: $3.20
Total: $43.20`);

    console.log('Created test files:', testFile1, testFile2);

    console.log('6. Uploading documents...');
    // Look for file input or upload area
    const fileInput = await page.locator('input[type="file"]').first();
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles([testFile1, testFile2]);
      console.log('Files uploaded');
    } else {
      // Look for drag-drop area
      const uploadArea = await page.locator('[class*="drop"]').or(page.locator('[class*="upload"]')).or(page.locator('text=drop')).first();
      if (await uploadArea.isVisible()) {
        console.log('Found upload area, but no file input visible');
      }
    }
    await page.screenshot({ path: '/tmp/claude/step6_files_uploaded.png', fullPage: true });
    console.log('Screenshot saved: step6_files_uploaded.png');

    console.log('7. Submitting the job...');
    // Look for submit button
    const submitButton = await page.locator('button').filter({ hasText: /submit/i }).or(page.locator('button').filter({ hasText: /start/i })).or(page.locator('button').filter({ hasText: /create/i })).or(page.locator('input[type="submit"]')).first();
    if (await submitButton.isVisible()) {
      console.log('Found submit button, clicking...');
      await submitButton.click();
      await page.waitForTimeout(2000); // Wait for submission
    }
    await page.screenshot({ path: '/tmp/claude/step7_submitted.png', fullPage: true });
    console.log('Screenshot saved: step7_submitted.png');

    console.log('8. Checking for success/error messages...');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/tmp/claude/step8_final_result.png', fullPage: true });
    console.log('Screenshot saved: step8_final_result.png');

    // Check browser console for any errors
    console.log('9. Checking browser console...');
    const logs = [];
    page.on('console', msg => logs.push(`${msg.type()}: ${msg.text()}`));
    page.on('pageerror', err => logs.push(`PAGE ERROR: ${err.message}`));

    await page.waitForTimeout(1000);
    console.log('Browser console logs:', logs);

  } catch (error) {
    console.error('Error during testing:', error);
    await page.screenshot({ path: '/tmp/claude/error_screenshot.png', fullPage: true });
  } finally {
    await browser.close();
    console.log('Test completed!');
  }
})();