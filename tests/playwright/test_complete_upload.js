const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  const page = await context.newPage();

  try {
    console.log('=== COMPLETE UPLOAD WORKFLOW TEST ===');

    console.log('1. Navigating to Upload Documents page...');
    await page.goto('http://localhost:5173/upload');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/claude/complete_step1.png', fullPage: true });

    console.log('2. Filling job name: "Receipt Test Job"...');
    await page.locator('input#jobName').fill('Receipt Test Job');
    await page.screenshot({ path: '/tmp/claude/complete_step2.png', fullPage: true });

    console.log('3. Selecting "Receipt Processing Test" schema...');
    await page.locator('select#schema').selectOption({ label: 'Receipt Processing Test (4 fields)' });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/tmp/claude/complete_step3.png', fullPage: true });

    console.log('4. Creating test documents...');
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

    console.log('5. Uploading documents...');
    await page.locator('input[type="file"]').setInputFiles([testFile1, testFile2]);
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/claude/complete_step5.png', fullPage: true });

    console.log('6. Submitting the job...');
    await page.locator('button:has-text("Create Job & Upload Files")').click();

    console.log('7. Waiting for response and capturing results...');
    await page.waitForTimeout(5000); // Wait for API response
    await page.screenshot({ path: '/tmp/claude/complete_step7.png', fullPage: true });

    // Check for success or error messages
    const successMessage = await page.locator('.text-success, .bg-success').textContent().catch(() => null);
    const errorMessage = await page.locator('.text-destructive, .bg-destructive').textContent().catch(() => null);

    if (successMessage) {
      console.log('✅ SUCCESS MESSAGE:', successMessage);
    }
    if (errorMessage) {
      console.log('❌ ERROR MESSAGE:', errorMessage);
    }

    console.log('8. Final state capture...');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/claude/complete_final.png', fullPage: true });

  } catch (error) {
    console.error('❌ Error during complete workflow test:', error);
    await page.screenshot({ path: '/tmp/claude/complete_error.png', fullPage: true });
  } finally {
    console.log('Test completed. Browser will close in 5 seconds...');
    await page.waitForTimeout(5000);
    await browser.close();
  }
})();