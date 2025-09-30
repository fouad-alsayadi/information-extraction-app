const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  const page = await context.newPage();

  try {
    console.log('1. Testing routing fix - navigating to upload page...');
    await page.goto('http://localhost:5173/upload');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Check the page title
    const pageTitle = await page.locator('h1').first().textContent();
    console.log('Page title:', pageTitle);

    // Check if schema select exists
    const schemaSelect = await page.locator('select#schema');
    const selectExists = await schemaSelect.count();
    console.log('Schema select exists:', selectExists > 0);

    if (selectExists > 0) {
      console.log('SUCCESS: Upload page is now rendering correctly!');

      // Wait for schemas to load
      await page.waitForTimeout(2000);

      const options = await page.locator('select#schema option').allTextContents();
      console.log('Schema options available:', options);

      // Check if warning message exists
      const warningText = await page.locator('.text-warning').textContent().catch(() => null);
      console.log('Warning message:', warningText);

    } else {
      console.log('ISSUE: Upload page components still not rendering');
    }

    await page.screenshot({ path: '/tmp/claude/routing_fix_test.png', fullPage: true });
    console.log('Screenshot saved: routing_fix_test.png');

  } catch (error) {
    console.error('Error during testing:', error);
  } finally {
    console.log('Test completed. Closing browser in 3 seconds...');
    await page.waitForTimeout(3000);
    await browser.close();
  }
})();