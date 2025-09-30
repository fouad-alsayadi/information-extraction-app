const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  const page = await context.newPage();

  // Capture console logs and errors
  page.on('console', msg => console.log(`CONSOLE ${msg.type()}: ${msg.text()}`));
  page.on('pageerror', err => console.log(`PAGE ERROR: ${err.message}`));

  try {
    console.log('1. Navigating to upload page directly...');
    await page.goto('http://localhost:5173/upload');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Take initial screenshot
    await page.screenshot({ path: '/tmp/claude/upload_initial.png', fullPage: true });
    console.log('Screenshot saved: upload_initial.png');

    // Check if we're actually on the upload page
    const pageTitle = await page.locator('h1').first().textContent();
    console.log('Page title:', pageTitle);

    // Check for schemas dropdown
    const schemaSelect = await page.locator('select#schema');
    const selectExists = await schemaSelect.count();
    console.log('Schema select exists:', selectExists > 0);

    if (selectExists > 0) {
      // Wait a bit more for schemas to load
      await page.waitForTimeout(2000);

      const options = await page.locator('select#schema option').allTextContents();
      console.log('Schema options:', options);

      // Check if the warning message is visible
      const warningMessage = await page.locator('.text-warning').textContent().catch(() => null);
      console.log('Warning message:', warningMessage);
    }

    // Try to fill the job name to test interactivity
    const jobNameInput = await page.locator('input#jobName');
    if (await jobNameInput.count() > 0) {
      await jobNameInput.fill('Test Job Manual');
      console.log('Successfully filled job name');

      await page.screenshot({ path: '/tmp/claude/upload_with_job_name.png', fullPage: true });
      console.log('Screenshot saved: upload_with_job_name.png');
    }

    // Try clicking the schema dropdown to see if it loads schemas
    if (selectExists > 0) {
      console.log('Clicking schema dropdown...');
      await schemaSelect.click();
      await page.waitForTimeout(2000);

      const optionsAfterClick = await page.locator('select#schema option').allTextContents();
      console.log('Schema options after click:', optionsAfterClick);

      await page.screenshot({ path: '/tmp/claude/upload_dropdown_clicked.png', fullPage: true });
      console.log('Screenshot saved: upload_dropdown_clicked.png');
    }

  } catch (error) {
    console.error('Error during testing:', error);
    await page.screenshot({ path: '/tmp/claude/upload_error.png', fullPage: true });
  } finally {
    console.log('Test completed. Closing browser in 5 seconds...');
    await page.waitForTimeout(5000);
    await browser.close();
  }
})();