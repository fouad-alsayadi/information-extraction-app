const { chromium } = require('playwright');

(async () => {
  // Launch browser with DevTools
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  const page = await context.newPage();

  // Capture console logs and network requests
  const logs = [];
  const networkRequests = [];

  page.on('console', msg => {
    logs.push(`${msg.type()}: ${msg.text()}`);
    console.log(`${msg.type()}: ${msg.text()}`);
  });

  page.on('pageerror', err => {
    logs.push(`PAGE ERROR: ${err.message}`);
    console.log(`PAGE ERROR: ${err.message}`);
  });

  page.on('request', request => {
    networkRequests.push(`${request.method()} ${request.url()}`);
    console.log(`Request: ${request.method()} ${request.url()}`);
  });

  page.on('response', response => {
    console.log(`Response: ${response.status()} ${response.url()}`);
  });

  try {
    console.log('Navigating to upload page...');
    await page.goto('http://localhost:5173/upload');
    await page.waitForLoadState('networkidle');

    console.log('Waiting for schemas to load...');
    await page.waitForTimeout(5000);

    // Check if schemas are loaded
    const schemaOptions = await page.locator('select#schema option').count();
    console.log(`Schema options found: ${schemaOptions}`);

    if (schemaOptions > 1) { // More than just the placeholder
      const options = await page.locator('select#schema option').allTextContents();
      console.log('Schema options:', options);
    }

    // Check for error messages
    const errorMessages = await page.locator('.text-warning, .text-destructive').allTextContents();
    if (errorMessages.length > 0) {
      console.log('Error messages found:', errorMessages);
    }

    // Take a screenshot
    await page.screenshot({ path: '/tmp/claude/debug_upload.png', fullPage: true });
    console.log('Screenshot saved: debug_upload.png');

    // Wait for user to interact
    console.log('Browser will stay open for manual inspection. Close when done.');
    await page.waitForTimeout(30000);

  } catch (error) {
    console.error('Error during debugging:', error);
  } finally {
    console.log('\nAll console logs:');
    logs.forEach(log => console.log(log));

    console.log('\nAll network requests:');
    networkRequests.forEach(req => console.log(req));

    await browser.close();
  }
})();