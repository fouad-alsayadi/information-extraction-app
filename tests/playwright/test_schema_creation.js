const { chromium } = require('playwright');

async function testSchemaCreation() {
  console.log('🚀 Starting schema creation test...');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  const page = await context.newPage();

  try {
    // Navigate to the app
    console.log('📱 Navigating to http://localhost:5173');
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Take initial screenshot
    await page.screenshot({ path: 'screenshot-1-homepage.png', fullPage: true });
    console.log('📸 Screenshot 1: Homepage captured');

    // Navigate to Schemas page
    console.log('🔗 Navigating to Schemas page');
    await page.click('a[href="/schemas"]');
    await page.waitForLoadState('networkidle');

    // Take screenshot of schemas page
    await page.screenshot({ path: 'screenshot-2-schemas-page.png', fullPage: true });
    console.log('📸 Screenshot 2: Schemas page captured');

    // Look for the "Create New Schema" button and click it
    console.log('🎯 Looking for "Create New Schema" button');
    const createButton = page.locator('button:has-text("Create New Schema"), button:has-text("Create Your First Schema")');
    await createButton.first().click();
    await page.waitForTimeout(1000); // Wait for modal to appear

    // Take screenshot of modal
    await page.screenshot({ path: 'screenshot-3-create-modal.png', fullPage: true });
    console.log('📸 Screenshot 3: Create schema modal captured');

    // Fill in the schema name
    console.log('✏️ Filling in schema name: "Receipt Processing"');
    await page.fill('input[placeholder*="Invoice"], input[placeholder*="name"]', 'Receipt Processing');

    // Fill in description
    console.log('✏️ Filling in description');
    await page.fill('textarea[placeholder*="Describe"]', 'Schema for extracting data from receipts including merchant, date, amounts, and tax information');

    // Take screenshot after basic info
    await page.screenshot({ path: 'screenshot-4-basic-info-filled.png', fullPage: true });
    console.log('📸 Screenshot 4: Basic info filled');

    // Fill in the first field (merchant name)
    console.log('✏️ Configuring field 1: Merchant Name');
    const firstFieldName = page.locator('input[placeholder*="Field name"]').first();
    await firstFieldName.fill('merchant_name');

    // Select text type (should already be selected)
    const firstFieldType = page.locator('select').first();
    await firstFieldType.selectOption('text');

    // Make it required
    const firstFieldRequired = page.locator('input[type="checkbox"]').first();
    await firstFieldRequired.check();

    // Add description for first field
    const firstFieldDesc = page.locator('input[placeholder*="Field description"]').first();
    await firstFieldDesc.fill('Name of the merchant or store');

    // Add second field (date)
    console.log('➕ Adding field 2: Date');
    await page.click('button:has-text("+ Add Field")');
    await page.waitForTimeout(500);

    const secondFieldName = page.locator('input[placeholder*="Field name"]').nth(1);
    await secondFieldName.fill('date');

    const secondFieldType = page.locator('select').nth(1);
    await secondFieldType.selectOption('date');

    const secondFieldRequired = page.locator('input[type="checkbox"]').nth(1);
    await secondFieldRequired.check();

    const secondFieldDesc = page.locator('input[placeholder*="Field description"]').nth(1);
    await secondFieldDesc.fill('Transaction date');

    // Add third field (total amount)
    console.log('➕ Adding field 3: Total Amount');
    await page.click('button:has-text("+ Add Field")');
    await page.waitForTimeout(500);

    const thirdFieldName = page.locator('input[placeholder*="Field name"]').nth(2);
    await thirdFieldName.fill('total_amount');

    const thirdFieldType = page.locator('select').nth(2);
    await thirdFieldType.selectOption('currency');

    const thirdFieldRequired = page.locator('input[type="checkbox"]').nth(2);
    await thirdFieldRequired.check();

    const thirdFieldDesc = page.locator('input[placeholder*="Field description"]').nth(2);
    await thirdFieldDesc.fill('Total amount including tax');

    // Add fourth field (tax amount)
    console.log('➕ Adding field 4: Tax Amount');
    await page.click('button:has-text("+ Add Field")');
    await page.waitForTimeout(500);

    const fourthFieldName = page.locator('input[placeholder*="Field name"]').nth(3);
    await fourthFieldName.fill('tax_amount');

    const fourthFieldType = page.locator('select').nth(3);
    await fourthFieldType.selectOption('currency');

    const fourthFieldDesc = page.locator('input[placeholder*="Field description"]').nth(3);
    await fourthFieldDesc.fill('Tax amount');

    // Take screenshot with all fields filled
    await page.screenshot({ path: 'screenshot-5-all-fields-filled.png', fullPage: true });
    console.log('📸 Screenshot 5: All fields filled');

    // Submit the form
    console.log('🎯 Submitting the schema');
    await page.click('button[type="submit"]:has-text("Create Schema")');

    // Wait for response and potential redirect/modal close
    await page.waitForTimeout(3000);

    // Take final screenshot
    await page.screenshot({ path: 'screenshot-6-after-submit.png', fullPage: true });
    console.log('📸 Screenshot 6: After submission');

    console.log('✅ Schema creation test completed successfully!');
    console.log('📁 Screenshots saved:');
    console.log('  - screenshot-1-homepage.png');
    console.log('  - screenshot-2-schemas-page.png');
    console.log('  - screenshot-3-create-modal.png');
    console.log('  - screenshot-4-basic-info-filled.png');
    console.log('  - screenshot-5-all-fields-filled.png');
    console.log('  - screenshot-6-after-submit.png');

  } catch (error) {
    console.error('❌ Error during testing:', error);
    await page.screenshot({ path: 'screenshot-error.png', fullPage: true });
    console.log('📸 Error screenshot saved as screenshot-error.png');
  } finally {
    await browser.close();
  }
}

testSchemaCreation();