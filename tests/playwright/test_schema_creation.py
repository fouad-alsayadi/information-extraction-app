#!/usr/bin/env python3
"""Test script for schema creation functionality in the Information Extraction App"""

import asyncio

from playwright.async_api import async_playwright


async def test_schema_creation():
  """Test the schema creation functionality"""
  async with async_playwright() as p:
    # Launch browser
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    try:
      # Navigate to the app
      print('🌐 Navigating to the Information Extraction App...')
      await page.goto('http://localhost:5173')
      await page.wait_for_load_state('networkidle')

      # Take initial screenshot
      await page.screenshot(path='screenshots/01_initial_app_load.png')
      print('📸 Initial screenshot taken: screenshots/01_initial_app_load.png')

      # Wait for the page to load and look for the "Create New Schema" button
      print("🔍 Looking for 'Create New Schema' button...")

      # Wait for the schemas page to load
      await page.wait_for_selector('text=Schema Management', timeout=10000)

      # Take screenshot of schemas page
      await page.screenshot(path='screenshots/02_schemas_page.png')
      print('📸 Schemas page screenshot taken: screenshots/02_schemas_page.png')

      # Find and click the "Create New Schema" button
      create_button = page.locator('text=Create New Schema').first
      await create_button.wait_for(state='visible')

      print("✅ Found 'Create New Schema' button")
      await create_button.click()

      # Wait for modal to appear
      await page.wait_for_selector('text=Create New Schema', timeout=5000)

      # Take screenshot of modal
      await page.screenshot(path='screenshots/03_create_schema_modal.png')
      print('📸 Create schema modal screenshot taken: screenshots/03_create_schema_modal.png')

      # Fill in schema details
      print('📝 Filling in schema details...')

      # Schema name
      name_input = page.locator("input[placeholder*='Invoice Extraction']")
      await name_input.fill('Receipt Processing Test')

      # Description
      description_textarea = page.locator(
        "textarea[placeholder*='Describe what this schema extracts']"
      )
      await description_textarea.fill(
        'Test schema for extracting information from receipts and transaction documents'
      )

      # Take screenshot after filling basic info
      await page.screenshot(path='screenshots/04_basic_info_filled.png')
      print('📸 Basic info filled screenshot taken: screenshots/04_basic_info_filled.png')

      # Now add the fields
      print('🏗️ Adding schema fields...')

      # First field should already exist, let's fill it
      # Field 1: merchant_name
      field_inputs = page.locator("input[placeholder='Field name']")
      await field_inputs.first.fill('merchant_name')

      # Select type dropdown for first field
      type_selects = page.locator('select')
      await type_selects.first.select_option('text')

      # Mark as required
      required_checkboxes = page.locator("input[type='checkbox']")
      await required_checkboxes.first.check()

      # Add description for first field
      desc_inputs = page.locator("input[placeholder*='Field description']")
      await desc_inputs.first.fill('The name of the merchant/store')

      # Add second field
      add_field_button = page.locator('text=+ Add Field')
      await add_field_button.click()

      # Field 2: transaction_date
      await field_inputs.nth(1).fill('transaction_date')
      await type_selects.nth(1).select_option('date')
      await required_checkboxes.nth(1).check()
      await desc_inputs.nth(1).fill('Date of the transaction')

      # Add third field
      await add_field_button.click()

      # Field 3: total_amount
      await field_inputs.nth(2).fill('total_amount')
      await type_selects.nth(2).select_option('currency')
      await required_checkboxes.nth(2).check()
      await desc_inputs.nth(2).fill('Total amount paid')

      # Add fourth field
      await add_field_button.click()

      # Field 4: tax_amount
      await field_inputs.nth(3).fill('tax_amount')
      await type_selects.nth(3).select_option('currency')
      # Don't check required for this one (optional)
      await desc_inputs.nth(3).fill('Tax amount if shown')

      # Take screenshot with all fields filled
      await page.screenshot(path='screenshots/05_all_fields_filled.png')
      print('📸 All fields filled screenshot taken: screenshots/05_all_fields_filled.png')

      # Submit the form
      print('🚀 Submitting the schema...')
      submit_button = page.locator("button[type='submit']", has_text='Create Schema')
      await submit_button.click()

      # Wait for modal to close and page to reload
      await page.wait_for_selector('text=Create New Schema', state='hidden', timeout=10000)

      # Take screenshot of result
      await page.screenshot(path='screenshots/06_schema_created.png')
      print('📸 Schema created screenshot taken: screenshots/06_schema_created.png')

      # Verify the new schema appears in the list
      await page.wait_for_selector('text=Receipt Processing Test', timeout=5000)
      print('✅ Schema successfully created and appears in the list!')

      print('\n🎉 Schema creation test completed successfully!')
      print('📁 Screenshots saved in screenshots/ directory')

    except Exception as e:
      print(f'❌ Error during testing: {e}')
      await page.screenshot(path='screenshots/error_screenshot.png')
      raise

    finally:
      await browser.close()


if __name__ == '__main__':
  # Create screenshots directory
  import os

  os.makedirs('screenshots', exist_ok=True)

  # Run the test
  asyncio.run(test_schema_creation())
