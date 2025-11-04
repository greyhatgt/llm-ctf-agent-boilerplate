#!/usr/bin/env python3
"""
Simple script to pull and start a local CTFd instance on localhost:8000
Automatically configures CTFd with admin credentials to bypass setup wizard.
"""

import sys
import os
import time
import requests
import json
import glob

# Fix import issue: the local docker/ directory shadows the docker package
# Temporarily remove current directory from path to import the actual docker package
_script_dir = os.path.dirname(os.path.abspath(__file__))
_current_dir = os.getcwd()
_path_to_restore = None

# Remove current directory and script directory from path temporarily
if sys.path and (sys.path[0] == '' or sys.path[0] == _current_dir or sys.path[0] == _script_dir):
    _path_to_restore = sys.path.pop(0)

try:
    import docker
    # Verify we got the right module by checking for from_env
    if not hasattr(docker, 'from_env'):
        raise ImportError(
            "Failed to import docker package correctly. "
            "The local 'docker/' directory is shadowing the docker package. "
            "Install docker package with: pip install docker"
        )
finally:
    # Restore path if we removed it
    if _path_to_restore is not None:
        sys.path.insert(0, _path_to_restore)

def ensure_playwright_browsers():
    """Ensure Playwright browsers are installed. Returns True if successful or already installed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n⚠ Playwright not installed. Please run: uv sync")
        return False
    
    # First, check if browsers are already installed by trying to launch
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        print("  ✓ Playwright browsers already installed")
        return True
    except:
        pass  # Browsers not installed, need to install them
    
    print(f"  Installing Playwright browsers (this may take a few minutes)...")
    try:
        import subprocess
        import sys
        # Install chromium browser - show output so user knows it's working
        print("  Running: playwright install chromium --with-deps")
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium", "--with-deps"],
            stdout=sys.stdout,  # Show output in real-time
            stderr=subprocess.STDOUT,  # Merge stderr with stdout
            timeout=600  # 10 minute timeout for browser download
        )
        if result.returncode == 0:
            print("  ✓ Playwright browsers installed successfully")
            # Verify installation by trying to launch
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    browser.close()
                return True
            except Exception as e:
                print(f"  ⚠ Installation completed but browser launch failed: {e}")
                return False
        else:
            print(f"  ⚠ Playwright browser installation failed (exit code: {result.returncode})")
            print("  Please run manually: uv run playwright install chromium")
            return False
    except subprocess.TimeoutExpired:
        print("  ⚠ Browser installation timed out (took more than 10 minutes)")
        print("  Please run manually: uv run playwright install chromium")
        return False
    except Exception as e:
        print(f"  ⚠ Could not install browsers: {e}")
        print("  Please run manually: uv run playwright install chromium")
        return False

def wait_for_ctfd(container, max_wait=120, check_interval=2):
    """Wait for CTFd to be ready by checking HTTP endpoint"""
    print("Waiting for CTFd to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get("http://localhost:8000", timeout=5)
            if response.status_code in [200, 302]:  # 302 is redirect to setup/login
                print("✓ CTFd is ready!")
                time.sleep(2)  # Give it a moment to fully initialize
                return True
        except requests.exceptions.RequestException:
            pass
        
        # Check if container is still running
        container.reload()
        if container.status != 'running':
            print(f"✗ Container stopped unexpectedly (status: {container.status})")
            return False
        
        time.sleep(check_interval)
        print(".", end="", flush=True)
    
    print(f"\n⚠ CTFd did not become ready within {max_wait} seconds")
    return False

def setup_ctfd_browser(admin_name="admin", admin_email="admin@ctfd.local", admin_password="admin", ctf_name="CTF Platform"):
    """Setup CTFd using browser automation (Playwright). Returns (success, cookies_dict)"""
    try:
        # Ensure Playwright is installed and browsers are available
        if not ensure_playwright_browsers():
            print("\n⚠ Could not ensure Playwright browsers are installed")
            return False, {}, None
        
        from playwright.sync_api import sync_playwright
        
        print(f"\nAttempting to setup CTFd via browser automation...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Show browser window to see what's happening
            context = browser.new_context(viewport={'width': 1280, 'height': 720})
            page = context.new_page()
            
            # Navigate to setup page and wait for it to load
            print("  Navigating to setup page...")
            page.goto("http://localhost:8000", wait_until="networkidle", timeout=60000)
            time.sleep(1)  # Give React time to render
            
            # Check if we're on setup page or already configured
            current_url = page.url
            print(f"  Current URL: {current_url}")
            
            if "/setup" in current_url:
                print("  Found setup wizard, navigating through tabs...")
                
                # Wait for the page to be fully loaded
                page.wait_for_load_state("networkidle")
                time.sleep(0.5)
                
                # Debug: Get all tabs to see what's available
                print("  Looking for tabs...")
                all_tabs = page.locator("[role='tab'], .nav-tabs button, button[class*='tab'], .tab-button").all()
                print(f"  Found {len(all_tabs)} potential tab elements")
                for i, tab in enumerate(all_tabs):
                    try:
                        text = tab.text_content().strip()
                        print(f"    Tab {i}: '{text}'")
                    except:
                        pass
                
                # Click on Administration tab - try more specific selectors
                print("  Clicking Administration tab...")
                admin_tab_clicked = False
                
                # Try exact text match first
                admin_selectors = [
                    "button:has-text('Administration'):visible",
                    "[role='tab']:has-text('Administration'):visible",
                    "text='Administration'",
                    "button:has-text('Administration')",
                    "[role='tab']:has-text('Administration')"
                ]
                
                for selector in admin_selectors:
                    try:
                        locator = page.locator(selector)
                        count = locator.count()
                        print(f"    Trying selector '{selector}' - found {count} elements")
                        if count > 0:
                            locator.first.wait_for(state="visible", timeout=5000)
                            locator.first.click()
                            admin_tab_clicked = True
                            print("  ✓ Administration tab clicked")
                            time.sleep(0.5)  # Wait for tab content to load
                            break
                    except Exception as e:
                        print(f"    Selector '{selector}' failed: {e}")
                        continue
                
                if not admin_tab_clicked:
                    # Try to find any tab with "admin" text (case insensitive)
                    print("  Trying to find tab by searching all tabs...")
                    tabs = page.locator("[role='tab'], .nav-tabs button, button[class*='tab']").all()
                    for tab in tabs:
                        try:
                            text = tab.text_content().strip().lower()
                            print(f"    Checking tab text: '{text}'")
                            if "admin" in text:
                                tab.wait_for(state="visible", timeout=5000)
                                tab.click()
                                admin_tab_clicked = True
                                print("  ✓ Administration tab clicked (by text search)")
                                time.sleep(0.5)
                                break
                        except Exception as e:
                            print(f"    Error checking tab: {e}")
                            continue
                
                if admin_tab_clicked:
                    # Fill out the administration form fields
                    print("  Filling out admin credentials...")
                    
                    # Wait for tab content to render
                    time.sleep(0.5)
                    
                    # Debug: List all input fields
                    all_inputs = page.locator("input").all()
                    print(f"  Found {len(all_inputs)} input fields")
                    for i, inp in enumerate(all_inputs):
                        try:
                            name_attr = inp.get_attribute("name") or ""
                            input_type = inp.get_attribute("type") or ""
                            input_id = inp.get_attribute("id") or ""
                            print(f"    Input {i}: name='{name_attr}', type='{input_type}', id='{input_id}'")
                        except:
                            pass
                    
                    # Fill username/name field
                    print("  Filling username...")
                    name_filled = False
                    name_selectors = [
                        "input[name='name']:visible",
                        "input#name:visible",
                        "input[name='username']:visible",
                        "input[placeholder*='name' i]:visible",
                        "input[placeholder*='username' i]:visible"
                    ]
                    for selector in name_selectors:
                        try:
                            locator = page.locator(selector)
                            if locator.count() > 0:
                                locator.first.wait_for(state="visible", timeout=5000)
                                locator.first.fill("")
                                locator.first.fill(admin_name)
                                print(f"    ✓ Filled username using '{selector}'")
                                name_filled = True
                                break
                        except Exception as e:
                            continue
                    if not name_filled:
                        print("    ⚠ Could not fill username field")
                    time.sleep(0.1)
                    
                    # Fill email field
                    print("  Filling email...")
                    email_filled = False
                    email_selectors = [
                        "input[name='email']:visible",
                        "input#email:visible",
                        "input[type='email']:visible",
                        "input[placeholder*='email' i]:visible"
                    ]
                    for selector in email_selectors:
                        try:
                            locator = page.locator(selector)
                            if locator.count() > 0:
                                locator.first.wait_for(state="visible", timeout=5000)
                                locator.first.fill("")
                                locator.first.fill(admin_email)
                                print(f"    ✓ Filled email using '{selector}'")
                                email_filled = True
                                break
                        except Exception as e:
                            continue
                    if not email_filled:
                        print("    ⚠ Could not fill email field")
                    time.sleep(0.1)
                    
                    # Fill password field(s)
                    print("  Filling password...")
                    password_selectors = [
                        "input[name='password']:visible",
                        "input#password:visible",
                        "input[type='password']:visible"
                    ]
                    password_filled = False
                    for selector in password_selectors:
                        try:
                            locator = page.locator(selector)
                            if locator.count() > 0:
                                locator.first.wait_for(state="visible", timeout=5000)
                                locator.first.fill("")
                                locator.first.fill(admin_password)
                                print(f"    ✓ Filled password using '{selector}'")
                                password_filled = True
                                break
                        except Exception as e:
                            continue
                    if not password_filled:
                        print("    ⚠ Could not fill password field")
                    time.sleep(0.1)
                    
                    # Try to fill password confirmation (optional)
                    print("  Checking for password confirmation...")
                    try:
                        all_password_inputs = page.locator("input[type='password']:visible").all()
                        print(f"    Found {len(all_password_inputs)} password inputs")
                        if len(all_password_inputs) > 1:
                            # Fill the second password field
                            all_password_inputs[1].wait_for(state="visible", timeout=5000)
                            all_password_inputs[1].fill("")
                            all_password_inputs[1].fill(admin_password)
                            print("    ✓ Filled password confirmation (second password field)")
                        else:
                            # Try specific password_confirm selectors
                            confirm_selectors = [
                                "input[name='password_confirm']:visible",
                                "input#password_confirm:visible",
                                "input[name='confirm']:visible"
                            ]
                            for selector in confirm_selectors:
                                try:
                                    if page.locator(selector).count() > 0:
                                        page.locator(selector).first.fill(admin_password)
                                        print(f"    ✓ Filled password confirmation using '{selector}'")
                                        break
                                except:
                                    continue
                    except Exception as e:
                        print(f"    ⚠ Password confirmation not found or not needed: {e}")
                    
                    time.sleep(0.1)
                    print("  ✓ Admin credentials filled")
                    
                    # Click on Integrations tab
                    print("  Clicking Integrations tab...")
                    integrations_tab_clicked = False
                    
                    integrations_selectors = [
                        "button:has-text('Integrations'):visible",
                        "[role='tab']:has-text('Integrations'):visible",
                        "text='Integrations'",
                        "button:has-text('Integrations')",
                        "[role='tab']:has-text('Integrations')"
                    ]
                    
                    for selector in integrations_selectors:
                        try:
                            locator = page.locator(selector)
                            if locator.count() > 0:
                                locator.first.wait_for(state="visible", timeout=5000)
                                locator.first.click()
                                integrations_tab_clicked = True
                                print("  ✓ Integrations tab clicked")
                                time.sleep(0.2)
                                break
                        except Exception as e:
                            continue
                    
                    if not integrations_tab_clicked:
                        # Try to find any tab with "integrations" text
                        print("  Searching for Integrations tab by text...")
                        tabs = page.locator("[role='tab'], .nav-tabs button, button[class*='tab']").all()
                        for tab in tabs:
                            try:
                                text = tab.text_content().strip().lower()
                                if "integration" in text:
                                    tab.wait_for(state="visible", timeout=5000)
                                    tab.click()
                                    integrations_tab_clicked = True
                                    print("  ✓ Integrations tab clicked (by text search)")
                                    time.sleep(0.2)
                                    break
                            except Exception as e:
                                continue
                    
                    if not integrations_tab_clicked:
                        print("  ⚠ Could not find Integrations tab, trying to click Finish anyway...")
                    
                    # Click Finish/Submit button
                    print("  Looking for Finish button...")
                    finish_clicked = False
                    
                    # Scroll to bottom in case button is below viewport
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(0.1)
                    
                    # Debug: List all visible buttons
                    print("  Debugging: Listing all visible buttons on page...")
                    all_buttons = page.locator("button:visible").all()
                    print(f"    Found {len(all_buttons)} visible buttons")
                    for i, btn in enumerate(all_buttons):
                        try:
                            text = btn.text_content().strip()
                            btn_type = btn.get_attribute("type") or ""
                            btn_class = btn.get_attribute("class") or ""
                            print(f"    Button {i}: text='{text}', type='{btn_type}', class='{btn_class[:50]}'")
                        except:
                            pass
                    
                    # Look specifically for "Finish" button - it's an INPUT element, not a button!
                    finish_selectors = [
                        "input[type='submit'][value='Finish']:visible",
                        "input#_submit:visible",
                        "input[name='_submit']:visible",
                        "input[type='submit'][value*='Finish']:visible",
                        "input.btn-primary[value='Finish']:visible",
                        "button:has-text('Finish'):not(:has-text('Setup')):visible",
                        "button:has-text('Complete Setup'):not(:has-text('Setup')):visible",
                    ]
                    
                    for selector in finish_selectors:
                        try:
                            locator = page.locator(selector)
                            count = locator.count()
                            print(f"    Trying Finish selector '{selector}' - found {count} elements")
                            if count > 0:
                                element = locator.first
                                
                                # Get text/value - for input elements, use value attribute, for buttons use text_content
                                try:
                                    tag_name = element.evaluate("el => el.tagName.toLowerCase()")
                                    if tag_name == "input":
                                        element_text = element.get_attribute("value") or ""
                                    else:
                                        element_text = element.text_content().strip()
                                except:
                                    element_text = element.get_attribute("value") or element.text_content().strip() or ""
                                
                                print(f"    Found element with text/value: '{element_text}'")
                                
                                # Double-check it's not a Setup button
                                if "setup" in element_text.lower() and "finish" not in element_text.lower():
                                    print(f"    Skipping element with text '{element_text}' (it's a Setup button)")
                                    continue
                                
                                element.wait_for(state="visible", timeout=5000)
                                
                                # Scroll element into view (scroll to bottom right where Finish usually is)
                                element.scroll_into_view_if_needed()
                                time.sleep(0.2)
                                
                                # Try normal click first
                                try:
                                    element.click()
                                    finish_clicked = True
                                    print(f"  ✓ Finish button clicked (value/text: '{element_text}')")
                                    break
                                except:
                                    # If normal click fails, try force click
                                    try:
                                        element.click(force=True)
                                        finish_clicked = True
                                        print(f"  ✓ Finish button clicked (force, value/text: '{element_text}')")
                                        break
                                    except:
                                        pass
                        except Exception as e:
                            print(f"    Selector '{selector}' failed: {e}")
                            continue
                    
                    if not finish_clicked:
                        # More thorough search - find all buttons AND input elements, filter out Setup buttons
                        print("  Searching all buttons and inputs for Finish (excluding Setup buttons)...")
                        all_buttons = page.locator("button").all()
                        all_inputs = page.locator("input[type='submit']").all()
                        all_elements = list(all_buttons) + list(all_inputs)
                        print(f"    Found {len(all_elements)} total buttons/inputs")
                        for element in all_elements:
                            try:
                                # Get text/value appropriately
                                if element.evaluate("el => el.tagName.toLowerCase()") == "input":
                                    text = element.get_attribute("value") or ""
                                else:
                                    text = element.text_content().strip()
                                
                                text_lower = text.lower()
                                print(f"    Checking element text/value: '{text}'")
                                
                                # Skip any element that says "Setup" unless it also says "Finish" or "Complete Setup"
                                if "setup" in text_lower and "finish" not in text_lower and "complete setup" not in text_lower:
                                    print(f"      Skipping (Setup button)")
                                    continue
                                
                                # Look for elements with "finish" or "complete setup" but NOT just "setup"
                                if ("finish" in text_lower or "complete setup" in text_lower) and "setup" not in text_lower.replace("complete setup", ""):
                                    # Try to make it visible and click
                                    element.scroll_into_view_if_needed()
                                    element.wait_for(state="visible", timeout=3000)
                                    element.click()
                                    finish_clicked = True
                                    print(f"  ✓ Finish button clicked (found text/value: '{text}')")
                                    break
                            except Exception as e:
                                print(f"    Error with element: {e}")
                                continue
                    
                    if not finish_clicked:
                        # Last resort: try to find by id or name attribute
                        print("  Last resort: Looking for Finish button by ID/name attribute...")
                        try:
                            # Try the specific ID we know from the HTML
                            finish_input = page.locator("input#_submit")
                            if finish_input.count() > 0:
                                finish_input.first.scroll_into_view_if_needed()
                                finish_input.first.click()
                                finish_clicked = True
                                print(f"  ✓ Finish button clicked (by ID _submit)")
                            elif page.locator("input[name='_submit']").count() > 0:
                                page.locator("input[name='_submit']").first.scroll_into_view_if_needed()
                                page.locator("input[name='_submit']").first.click()
                                finish_clicked = True
                                print(f"  ✓ Finish button clicked (by name _submit)")
                        except Exception as e:
                            print(f"    Last resort method failed: {e}")
                    
                    if finish_clicked:
                        # Wait for redirect or success
                        print("  Waiting for setup to complete...")
                        try:
                            # Wait for URL to change from /setup (with shorter timeout)
                            page.wait_for_url(lambda url: "/setup" not in url, timeout=10000, wait_until="networkidle")
                            final_url = page.url
                            print(f"  ✓ Setup complete! Redirected to: {final_url}")
                        except:
                            # If timeout, just check current URL
                            final_url = page.url
                            print(f"  Current URL: {final_url}")
                            if "/setup" not in final_url:
                                print(f"  ✓ Setup appears complete (no longer on /setup)")
                            else:
                                print(f"  ⚠ Still on setup page, but continuing...")
                    
                    print(f"\n✓ Setup process completed")
                    print(f"  Username: {admin_name}")
                    print(f"  Email: {admin_email}")
                    
                    # After setup, user should already be authenticated
                    # Get cookies from browser session
                    cookies = page.context.cookies()
                    browser_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
                    if browser_cookies:
                        print(f"  ✓ Browser session cookies captured ({len(browser_cookies)} cookies)")
                    
                    # Create API token while browser is still open (handles CSRF automatically)
                    print(f"\n  Creating API token...")
                    api_token = create_api_token_browser(page, admin_name, admin_password)
                    
                    # Keep browser open for a bit so user can see the result
                    print("\n  Browser window will stay open for 10 seconds...")
                    time.sleep(10)
                    
                    # Close browser after token creation
                    browser.close()
                    
                    # Return success and token info
                    if api_token:
                        return True, browser_cookies, api_token
                    else:
                        return True, browser_cookies, None
                else:
                    print("  ⚠ Could not find Administration tab")
                    browser.close()
                    return False, {}, None
            else:
                print("  CTFd appears to be already configured")
                # Get cookies from current session
                try:
                    cookies = page.context.cookies()
                    browser_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
                    
                    # Create API token while browser is still open
                    api_token = create_api_token_browser(page, admin_name, admin_password)
                    
                    print("\n  Browser window will stay open for 10 seconds...")
                    time.sleep(10)
                    
                    browser.close()
                    
                    if api_token:
                        return True, browser_cookies, api_token
                    else:
                        return True, browser_cookies, None
                except:
                    browser.close()
                    return True, {}, None
                
    except Exception as e:
        print(f"✗ Browser automation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}, None

def create_api_token_browser(page, admin_name="admin", admin_password="admin"):
    """Create an API token via browser automation: Settings > Access Tokens > Create token"""
    print("\n  Creating API token via browser...")
    
    try:
        # Navigate to settings page
        print("    Navigating to Settings page...")
        page.goto("http://localhost:8000/settings", wait_until="load", timeout=30000)
        time.sleep(1)
        
        # Check if we're on a login page (session might have expired)
        if "/login" in page.url:
            print("    Session expired, logging in again...")
            page.goto("http://localhost:8000/login", wait_until="load")
            time.sleep(0.5)
            
            page.locator("input#name").fill(admin_name)
            page.locator("input#password").fill(admin_password)
            page.locator("input#_submit").click()
            time.sleep(2)
            
            # Try again
            page.goto("http://localhost:8000/settings", wait_until="load", timeout=30000)
            time.sleep(1)
        
        # Click on "Access Tokens" tab
        print("    Looking for Access Tokens tab...")
        access_tokens_clicked = False
        
        # Try various selectors for the Access Tokens tab
        tab_selectors = [
            "a:has-text('Access Tokens'):visible",
            "button:has-text('Access Tokens'):visible",
            "[role='tab']:has-text('Access Tokens'):visible",
            "li:has-text('Access Tokens') a:visible",
            "a[href*='tokens']:visible",
            "a[href*='token']:visible"
        ]
        
        for selector in tab_selectors:
            try:
                tab = page.locator(selector)
                if tab.count() > 0:
                    tab.first.wait_for(state="visible", timeout=5000)
                    tab.first.click()
                    access_tokens_clicked = True
                    print("    ✓ Access Tokens tab clicked")
                    time.sleep(1)  # Wait for tab content to load
                    break
            except:
                continue
        
        if not access_tokens_clicked:
            # Try to find any link/button with "token" in the text
            print("    Searching for Access Tokens by text...")
            all_links = page.locator("a, button").all()
            for link in all_links:
                try:
                    text = link.text_content().strip().lower()
                    if "access token" in text or ("token" in text and "access" in text):
                        link.wait_for(state="visible", timeout=5000)
                        link.click()
                        access_tokens_clicked = True
                        print(f"    ✓ Access Tokens tab clicked (found text: '{text}')")
                        time.sleep(1)
                        break
                except:
                    continue
        
        if not access_tokens_clicked:
            # Try navigating directly to the tokens page
            print("    Trying direct navigation to /settings/tokens...")
            page.goto("http://localhost:8000/settings/tokens", wait_until="load", timeout=30000)
            time.sleep(1)
        
        # Now we should be on the Access Tokens page
        # Look for form to create a new token
        print("    Looking for token creation form...")
        time.sleep(0.5)
        
        # Find and fill in the token name field
        print("    Filling token name...")
        name_field_filled = False
        name_selectors = [
            "input[name='description']:visible",
            "input[name='name']:visible",
            "input#description:visible",
            "input#name:visible",
            "input[placeholder*='name' i]:visible",
            "input[placeholder*='description' i]:visible"
        ]
        
        for selector in name_selectors:
            try:
                name_input = page.locator(selector)
                if name_input.count() > 0:
                    name_input.first.wait_for(state="visible", timeout=5000)
                    name_input.first.fill("")
                    name_input.first.fill("access token")
                    name_field_filled = True
                    print("    ✓ Token name filled: 'access token'")
                    time.sleep(0.3)
                    break
            except:
                continue
        
        # Find and set the expiry date (1 year from today)
        print("    Setting expiry date (1 year from today)...")
        from datetime import datetime, timedelta
        expiry_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        
        expiry_field_filled = False
        expiry_selectors = [
            "input[type='date']:visible",
            "input[name='expiration']:visible",
            "input[name='expiry']:visible",
            "input[name='expires']:visible",
            "input#expiration:visible",
            "input#expiry:visible",
            "input#expires:visible"
        ]
        
        for selector in expiry_selectors:
            try:
                expiry_input = page.locator(selector)
                if expiry_input.count() > 0:
                    expiry_input.first.wait_for(state="visible", timeout=5000)
                    expiry_input.first.fill("")
                    expiry_input.first.fill(expiry_date)
                    expiry_field_filled = True
                    print(f"    ✓ Expiry date filled: {expiry_date}")
                    time.sleep(0.3)
                    break
            except:
                continue
        
        if not expiry_field_filled:
            print("    ⚠ Could not find expiry date field, continuing anyway...")
        
        # Find and click submit button
        print("    Clicking submit button...")
        submit_clicked = False
        submit_selectors = [
            "button[type='submit']:visible",
            "input[type='submit']:visible",
            "button:has-text('Submit'):visible",
            "button:has-text('Create'):visible",
            "button:has-text('Generate'):visible",
            "button.btn-primary:visible"
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = page.locator(selector)
                if submit_btn.count() > 0:
                    submit_btn.first.wait_for(state="visible", timeout=5000)
                    submit_btn.first.click()
                    submit_clicked = True
                    print("    ✓ Submit button clicked")
                    time.sleep(2)  # Wait for token to be created and displayed
                    break
            except:
                continue
        
        if not submit_clicked:
            print("    ⚠ Could not find submit button, trying Enter key...")
            try:
                page.keyboard.press("Enter")
            except:
                pass
        
        # Wait a moment for the token to appear
        time.sleep(1)
        
        # Look for the created token on the page
        print("    Looking for created token...")
        token_selectors = [
            "code:visible",
            ".token:visible",
            "input[value*='ctfd']:visible",
            "input[readonly]:visible",
            "[data-token]:visible",
            "pre:visible",
            "textarea:visible"
        ]
        
        for selector in token_selectors:
            try:
                token_elem = page.locator(selector)
                if token_elem.count() > 0:
                    # Get all matching elements and find the one with the token
                    all_tokens = token_elem.all()
                    for elem in all_tokens:
                        try:
                            token_text = elem.text_content().strip()
                            # Check if it looks like a token (long string, might contain ctfd)
                            if token_text and len(token_text) > 20:
                                api_token = token_text
                                print(f"    ✓ API token found: {api_token[:30]}...")
                                return api_token
                        except:
                            continue
            except:
                continue
        
        # Alternative: try to get token from input value
        try:
            token_inputs = page.locator("input[readonly], input[value*='ctfd']").all()
            for inp in token_inputs:
                try:
                    token_value = inp.get_attribute("value") or inp.input_value()
                    if token_value and len(token_value) > 20:
                        api_token = token_value
                        print(f"    ✓ API token found from input: {api_token[:30]}...")
                        return api_token
                except:
                    continue
        except:
            pass
        
        print("    ⚠ Could not find created token on page")
        return None
        
    except Exception as e:
        print(f"    ⚠ Error creating API token via browser: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_api_token(admin_name="admin", admin_password="admin", cookies=None, browser_page=None):
    """Create an API token and save it to .env file. Uses browser if available for CSRF."""
    print("\n  Creating API token...")
    
    # If we have a browser page (could be tuple of page, browser, context), use it (handles CSRF automatically)
    if browser_page:
        # Extract page from tuple if needed
        if isinstance(browser_page, tuple):
            page = browser_page[0]
        else:
            page = browser_page
        api_token = create_api_token_browser(page, admin_name, admin_password)
        if api_token:
            return save_token_to_env(api_token)
    
    # Fallback to API method with cookies
    try:
        session = requests.Session()
        base_url = "http://localhost:8000"
        
        # Use cookies from browser session if provided
        if cookies:
            print("    Using browser session cookies...")
            for name, value in cookies.items():
                session.cookies.set(name, value)
            
            # Try to get CSRF token from a page request
            try:
                csrf_page = session.get(f"{base_url}/admin/users/me/tokens", timeout=10)
                if csrf_page.status_code == 200:
                    # Try to extract CSRF token from HTML
                    import re
                    csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', csrf_page.text)
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                        session.headers.update({'X-CSRFToken': csrf_token})
                        print("    ✓ CSRF token extracted")
            except:
                pass
        else:
            # Fallback: Login via API to get session
            print("    Logging in via API...")
            login_data = {
                "name": admin_name,
                "password": admin_password
            }
            
            login_response = session.post(
                f"{base_url}/login",
                data=login_data,
                timeout=10
            )
            
            if login_response.status_code not in [200, 302]:
                print(f"    ⚠ Login failed (status: {login_response.status_code})")
                return False
            
            print("    ✓ Logged in successfully")
            time.sleep(0.5)
        
        # Create API token
        print("    Creating API token via API...")
        token_response = session.post(
            f"{base_url}/api/v1/tokens",
            json={"description": "Auto-generated token for CTF agent"},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            if 'data' in token_data and 'value' in token_data['data']:
                api_token = token_data['data']['value']
                print(f"    ✓ API token created successfully")
                return save_token_to_env(api_token)
            else:
                print(f"    ⚠ Unexpected token response format: {token_data}")
                return False
        else:
            print(f"    ⚠ Failed to create token (status: {token_response.status_code})")
            print(f"    Response: {token_response.text}")
            return False
            
    except Exception as e:
        print(f"    ⚠ Error creating API token: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_token_to_env(api_token):
    """Save API token to .env file"""
    env_file = ".env"
    print(f"    Adding token to {env_file}...")
    
    # Read existing .env content
    existing_content = ""
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            existing_content = f.read()
    
    # Check if CTFD_API_TOKEN already exists
    if "CTFD_API_TOKEN" in existing_content:
        print(f"    ⚠ CTFD_API_TOKEN already exists in .env, updating it...")
        # Replace existing CTFD_API_TOKEN line
        lines = existing_content.split('\n')
        new_lines = []
        replaced = False
        for line in lines:
            if line.strip().startswith("CTFD_API_TOKEN="):
                new_lines.append(f"CTFD_API_TOKEN={api_token}")
                replaced = True
            else:
                new_lines.append(line)
        
        if not replaced:
            new_lines.append(f"CTFD_API_TOKEN={api_token}")
        
        new_content = '\n'.join(new_lines)
    else:
        # Append to existing content
        new_content = existing_content
        if existing_content and not existing_content.endswith('\n'):
            new_content += "\n"
        new_content += f"\n# CTFd API Token (auto-generated)\nCTFD_API_TOKEN={api_token}\n"
    
    # Write back to .env
    with open(env_file, 'w') as f:
        f.write(new_content)
    
    print(f"    ✓ API token saved to {env_file}")
    print(f"    Token: {api_token[:20]}...")
    return True

def load_api_token():
    """Load API token from .env file"""
    env_file = ".env"
    if not os.path.exists(env_file):
        return None
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.strip().startswith("CTFD_API_TOKEN="):
                return line.split("=", 1)[1].strip()
    return None

def upload_file_to_ctfd(file_path, challenge_id, api_token, base_url="http://localhost:8000"):
    """Upload a file to CTFd and attach it to a challenge"""
    try:
        headers = {
            'Authorization': f'Token {api_token}',
        }
        
        # Read file
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        filename = os.path.basename(file_path)
        
        # Upload file using multipart form data
        files = {
            'file': (filename, file_data)
        }
        data = {
            'challenge_id': challenge_id,
            'type': 'challenge'  # File type for challenge files
        }
        
        response = requests.post(
            f"{base_url}/api/v1/files",
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"        ⚠ Failed to upload {filename}: {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"        ⚠ Error uploading {file_path}: {e}")
        return False

def sync_challenges(challenges_dir="challenges", api_token=None):
    """Sync local challenges from challenges/ folder to CTFd"""
    if not api_token:
        api_token = load_api_token()
    
    if not api_token:
        print("  ⚠ No API token found. Cannot sync challenges.")
        return False
    
    print(f"\n  Syncing challenges from {challenges_dir}...")
    
    # Find all challenge.json files
    challenge_files = glob.glob(os.path.join(challenges_dir, "**/challenge.json"), recursive=True)
    
    if not challenge_files:
        print(f"  ⚠ No challenge.json files found in {challenges_dir}")
        return False
    
    print(f"  Found {len(challenge_files)} challenges")
    
    base_url = "http://localhost:8000"
    headers = {
        'Authorization': f'Token {api_token}',
        'Content-Type': 'application/json'
    }
    
    synced_count = 0
    failed_count = 0
    
    for challenge_file in challenge_files:
        try:
            with open(challenge_file, 'r') as f:
                challenge_data = json.load(f)
            
            challenge_name = challenge_data.get('name', os.path.basename(os.path.dirname(challenge_file)))
            challenge_dir = os.path.dirname(challenge_file)
            artifacts_dir = os.path.join(challenge_dir, "artifacts")
            
            print(f"    Syncing challenge: {challenge_name}...")
            
            # Check if challenge already exists
            existing_challenges = requests.get(
                f"{base_url}/api/v1/challenges",
                headers=headers,
                timeout=10
            )
            
            challenge_exists = False
            challenge_id = None
            
            if existing_challenges.status_code == 200:
                existing_data = existing_challenges.json()
                if 'data' in existing_data:
                    for existing in existing_data['data']:
                        if existing.get('name') == challenge_name:
                            challenge_exists = True
                            challenge_id = existing.get('id')
                            break
            
            # Prepare challenge data for CTFd API
            # Note: Create challenge first, then add flag separately
            ctf_challenge = {
                'name': challenge_data.get('name'),
                'description': challenge_data.get('description', ''),
                'category': challenge_data.get('categories', ['Misc'])[0] if challenge_data.get('categories') else 'Misc',
                'value': 100,  # Default value, could be from challenge.json
                'state': 'visible',
                'type': 'standard'
            }
            
            if challenge_exists and challenge_id:
                # Update existing challenge
                response = requests.patch(
                    f"{base_url}/api/v1/challenges/{challenge_id}",
                    headers=headers,
                    json=ctf_challenge,
                    timeout=10
                )
                if response.status_code == 200:
                    print(f"      ✓ Updated: {challenge_name}")
                    synced_count += 1
                else:
                    print(f"      ⚠ Failed to update: {response.status_code} - {response.text}")
                    failed_count += 1
            else:
                # Create new challenge
                response = requests.post(
                    f"{base_url}/api/v1/challenges",
                    headers=headers,
                    json=ctf_challenge,
                    timeout=10
                )
                if response.status_code == 200:
                    response_data = response.json()
                    if 'data' in response_data:
                        challenge_id = response_data['data'].get('id')
                    print(f"      ✓ Created: {challenge_name}")
                    synced_count += 1
                else:
                    print(f"      ⚠ Failed to create: {response.status_code} - {response.text}")
                    failed_count += 1
                    continue  # Skip file upload if challenge creation failed
            
            # Now add the flag (after challenge is created/updated)
            if challenge_id:
                flag = challenge_data.get('flag')
                if flag:
                    # Check for existing flags first and delete them
                    existing_flags_response = requests.get(
                        f"{base_url}/api/v1/flags",
                        headers=headers,
                        params={'challenge_id': challenge_id},
                        timeout=10
                    )
                    if existing_flags_response.status_code == 200:
                        existing_flags_data = existing_flags_response.json()
                        if 'data' in existing_flags_data:
                            for existing_flag in existing_flags_data['data']:
                                flag_id = existing_flag.get('id')
                                if flag_id:
                                    # Delete existing flag
                                    delete_response = requests.delete(
                                        f"{base_url}/api/v1/flags/{flag_id}",
                                        headers=headers,
                                        timeout=10
                                    )
                                    if delete_response.status_code == 200:
                                        print(f"      ✓ Removed existing flag")
                    
                    # Add flag via flags endpoint
                    flag_data = {
                        'content': flag,
                        'type': 'static',
                        'challenge_id': challenge_id
                    }
                    flags_response = requests.post(
                        f"{base_url}/api/v1/flags",
                        headers=headers,
                        json=flag_data,
                        timeout=10
                    )
                    if flags_response.status_code == 200:
                        print(f"      ✓ Flag added")
                    else:
                        print(f"      ⚠ Failed to add flag: {flags_response.status_code} - {flags_response.text[:200]}")
                
                # Upload files from artifacts folder
                if os.path.isdir(artifacts_dir):
                    artifact_files = []
                    for root, dirs, files in os.walk(artifacts_dir):
                        for file in files:
                            artifact_files.append(os.path.join(root, file))
                    
                    if artifact_files:
                        print(f"      Uploading {len(artifact_files)} file(s)...")
                        for artifact_file in artifact_files:
                            if upload_file_to_ctfd(artifact_file, challenge_id, api_token, base_url):
                                print(f"        ✓ Uploaded: {os.path.basename(artifact_file)}")
                            else:
                                print(f"        ⚠ Failed: {os.path.basename(artifact_file)}")
                    else:
                        print(f"      No files in artifacts folder")
                else:
                    print(f"      No artifacts folder found")
            
        except Exception as e:
            print(f"      ⚠ Error syncing {challenge_file}: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
    
    print(f"\n  ✓ Sync complete: {synced_count} synced, {failed_count} failed")
    return synced_count > 0

def create_team_browser(page, team_name="lca_team", team_password="lca_team"):
    """Create a team via browser automation: Challenges page > Create Team"""
    print(f"\n  Creating team '{team_name}'...")
    
    try:
        # Navigate to challenges page
        print("    Navigating to Challenges page...")
        page.goto("http://localhost:8000/challenges", wait_until="load", timeout=30000)
        time.sleep(1)
        
        # Look for "Create Team" button or link
        print("    Looking for Create Team button...")
        create_clicked = False
        
        create_selectors = [
            "button:has-text('Create Team'):visible",
            "a:has-text('Create Team'):visible",
            "a:has-text('New Team'):visible",
            "button:has-text('New Team'):visible",
            "button.btn-primary:visible",
            "a.btn-primary:visible"
        ]
        
        for selector in create_selectors:
            try:
                btn = page.locator(selector)
                if btn.count() > 0:
                    btn.first.wait_for(state="visible", timeout=5000)
                    btn.first.click()
                    create_clicked = True
                    print("    ✓ Create Team button clicked")
                    time.sleep(1)  # Wait for form to appear
                    break
            except:
                continue
        
        if not create_clicked:
            # Try navigating directly to create team page
            print("    Trying direct navigation to create team page...")
            page.goto("http://localhost:8000/admin/teams/new", wait_until="load", timeout=30000)
            time.sleep(1)
        
        # Fill in team name
        print(f"    Filling team name: {team_name}...")
        name_filled = False
        name_selectors = [
            "input[name='name']:visible",
            "input#name:visible",
            "input[placeholder*='name' i]:visible"
        ]
        
        for selector in name_selectors:
            try:
                name_input = page.locator(selector)
                if name_input.count() > 0:
                    name_input.first.wait_for(state="visible", timeout=5000)
                    name_input.first.fill("")
                    name_input.first.fill(team_name)
                    name_filled = True
                    print(f"      ✓ Team name filled: {team_name}")
                    time.sleep(0.3)
                    break
            except:
                continue
        
        if not name_filled:
            print("      ⚠ Could not find team name field")
        
        # Fill in team password
        print(f"    Filling team password...")
        password_filled = False
        password_selectors = [
            "input[name='password']:visible",
            "input#password:visible",
            "input[type='password']:visible"
        ]
        
        for selector in password_selectors:
            try:
                password_input = page.locator(selector)
                if password_input.count() > 0:
                    password_input.first.wait_for(state="visible", timeout=5000)
                    password_input.first.fill("")
                    password_input.first.fill(team_password)
                    password_filled = True
                    print("      ✓ Team password filled")
                    time.sleep(0.3)
                    break
            except:
                continue
        
        if not password_filled:
            print("      ⚠ Could not find team password field (may not be required)")
        
        # Submit the form
        print("    Submitting team creation form...")
        submit_clicked = False
        submit_selectors = [
            "button[type='submit']:visible",
            "input[type='submit']:visible",
            "button:has-text('Create'):visible",
            "button:has-text('Submit'):visible",
            "button.btn-primary:visible"
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = page.locator(selector)
                if submit_btn.count() > 0:
                    submit_btn.first.wait_for(state="visible", timeout=5000)
                    submit_btn.first.click()
                    submit_clicked = True
                    print("    ✓ Submit button clicked")
                    time.sleep(2)  # Wait for team to be created
                    break
            except:
                continue
        
        if submit_clicked:
            print(f"    ✓ Team '{team_name}' created successfully")
            return True
        else:
            print("    ⚠ Could not find submit button")
            return False
        
    except Exception as e:
        print(f"    ⚠ Error creating team: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_ctfd(container, admin_name="admin", admin_email="admin@ctfd.local", admin_password="admin", ctf_name="CTF Platform"):
    """Setup CTFd automatically using browser automation. Returns (success, cookies_dict, api_token)"""
    return setup_ctfd_browser(admin_name, admin_email, admin_password, ctf_name)

def start_ctfd(admin_name="admin", admin_email="admin@ctfd.local", admin_password="admin", ctf_name="CTF Platform", skip_setup=False, team_name="lca_team", team_password="lca_team"):
    """Pull and start CTFd Docker container on localhost:8000"""
    client = docker.from_env()
    
    # CTFd image name
    image_name = "ctfd/ctfd"
    
    # Check if container already exists
    container_name = "ctfd"
    container = None
    container_existed = False
    
    try:
        existing_container = client.containers.get(container_name)
        container_status = existing_container.status
        container_existed = True
        print(f"Found existing container '{container_name}' in state: {container_status}")
        
        if container_status == 'running':
            print(f"  Container is already running")
            container = existing_container
        else:
            # Container exists but is not running - start it
            print(f"  Starting existing container...")
            existing_container.start()
            container = existing_container
            print(f"  ✓ Container started")
        
        # Wait for CTFd to be ready (if it was just started)
        if container_status != 'running':
            if not wait_for_ctfd(container):
                print("⚠ CTFd container started but didn't become ready")
                print("  You may need to check logs: docker logs ctfd")
                return
        else:
            # Container was already running, give it a moment and verify it's accessible
            time.sleep(2)
            print(f"  Checking if CTFd is accessible...")
            try:
                response = requests.get("http://localhost:8000", timeout=5)
                if response.status_code in [200, 302]:
                    print(f"  ✓ CTFd is accessible")
                else:
                    print(f"  ⚠ CTFd responded with status {response.status_code}")
            except:
                print(f"  ⚠ Could not verify CTFd accessibility")
        
    except docker.errors.NotFound:
        # Container doesn't exist, create it
        print(f"  No existing container found. Creating new container...")
        try:
            # Pull the image if needed
            client.images.pull(image_name)
            print(f"  ✓ Image ready")
        except Exception as e:
            print(f"  ⚠ Could not pull image: {e}")
        
        # Start the CTFd container
        print(f"\nStarting new CTFd container on localhost:8000...")
        container = client.containers.run(
            image=image_name,
            name=container_name,
            ports={'8000/tcp': 8000},
            detach=True,
            remove=False
        )
        print(f"✓ Container started: {container.name}")
        
        # Wait for CTFd to be ready
        if not wait_for_ctfd(container):
            print("⚠ CTFd container started but didn't become ready")
            print("  You may need to check logs: docker logs ctfd")
            return
        
        # Check if CTFd is already configured (not on setup page)
        needs_setup = False
        if not skip_setup:
            try:
                response = requests.get("http://localhost:8000", timeout=5, allow_redirects=True)
                # If we're redirected to /setup, setup is needed
                if "/setup" in response.url:
                    print(f"\n  CTFd needs initial setup...")
                    needs_setup = True
                else:
                    print(f"\n  CTFd appears to be already configured")
                    needs_setup = False
            except:
                print(f"\n  Could not check CTFd status, assuming setup needed")
                needs_setup = True
        
        # Automatically setup CTFd if needed and not skipped
        if not skip_setup and needs_setup:
            setup_success, browser_cookies, api_token = setup_ctfd(container, admin_name, admin_email, admin_password, ctf_name)
            if setup_success:
                print(f"\n✓ CTFd setup complete!")
                
                # Save API token if we got one
                if api_token:
                    save_token_to_env(api_token)
                else:
                    # Fallback: try creating token via API if browser method didn't work
                    print("    Token not created via browser, trying API method...")
                    create_api_token(admin_name, admin_password, cookies=browser_cookies, browser_page=None)
            else:
                print(f"\n⚠ Automatic setup failed. Please configure manually at http://localhost:8000")
                return
        elif skip_setup:
            print(f"\nCTFd is running at: http://localhost:8000")
            print(f"  (Setup wizard skipped - configure manually)")
            return
        
        # After setup (or if already configured), sync challenges and create team
        # Get API token
        api_token = load_api_token()
        if not api_token:
            print(f"\n  ⚠ No API token found. Cannot sync challenges or create team.")
            print(f"  Access CTFd at: http://localhost:8000")
            return
        
        # Create team first, then sync challenges
        print(f"\n  Setting up team and challenges...")
        
        # Create team using browser (reopen browser if needed)
        print(f"\n  Creating team...")
        # Ensure browsers are installed before creating team
        if not ensure_playwright_browsers():
            print("  ⚠ Could not ensure Playwright browsers are installed, skipping team creation")
        else:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={'width': 1280, 'height': 720})
                page = context.new_page()
                
                # Login first
                page.goto("http://localhost:8000/login", wait_until="load")
                time.sleep(0.5)
                page.locator("input#name").fill(admin_name)
                page.locator("input#password").fill(admin_password)
                page.locator("input#_submit").click()
                time.sleep(2)
                
                # Create team
                create_team_browser(page, team_name=team_name, team_password=team_password)
                
                print("\n  Browser window will stay open for 10 seconds...")
                time.sleep(10)
                browser.close()
        
        # Sync challenges from challenges/ folder (after team is created)
        sync_challenges(challenges_dir="challenges", api_token=api_token)
        
        print(f"\n  Access CTFd at: http://localhost:8000")
        print(f"  Login credentials:")
        print(f"    Username: {admin_name}")
        print(f"    Email: {admin_email}")
        print(f"    Password: {admin_password}")
        if team_name:
            print(f"    Team name: {team_name}")
            print(f"    Team password: {team_password}")
        
        print(f"\nContainer ID: {container.id}")
        print(f"\nTo stop the container, run:")
        print(f"  docker stop {container_name}")
        print(f"\nTo view logs, run:")
        print(f"  docker logs -f {container_name}")
        print(f"\nPress Ctrl+C to exit (container will keep running)")
        
        # Keep the script running and show logs
        try:
            for line in container.logs(stream=True, follow=True):
                print(line.decode('utf-8').strip())
        except KeyboardInterrupt:
            print(f"\n\nContainer is still running. Access CTFd at http://localhost:8000")
            print(f"To stop: docker stop {container_name}")
            
    except Exception as e:
        print(f"✗ Failed to start container: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start and configure a local CTFd instance")
    parser.add_argument("--admin-name", default="admin", help="Admin username (default: admin)")
    parser.add_argument("--admin-email", default="admin@ctfd.local", help="Admin email (default: admin@ctfd.local)")
    parser.add_argument("--admin-password", default="admin", help="Admin password (default: admin)")
    parser.add_argument("--ctf-name", default="CTF Platform", help="CTF name (default: CTF Platform)")
    parser.add_argument("--skip-setup", action="store_true", help="Skip automatic setup (show setup wizard)")
    parser.add_argument("--team-name", default="lca_team", help="Team name (default: lca_team)")
    parser.add_argument("--team-password", default="lca_team", help="Team password (default: lca_team)")
    
    args = parser.parse_args()
    
    start_ctfd(
        admin_name=args.admin_name,
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        ctf_name=args.ctf_name,
        skip_setup=args.skip_setup,
        team_name=args.team_name,
        team_password=args.team_password
    )

