import asyncio
from playwright.async_api import async_playwright
import config
import time

async def check_availability(days_to_check, target_slots, headless):
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        try:
            print(f"Navigating to login page: {config.LOGIN_URL}")
            await page.goto(config.LOGIN_URL)

            # Login
            print("Logging in...")
            # Login Logic with User Provided Selectors
            print("Entering email...")
            try:
                # Email is type="text" with name="email"
                await page.wait_for_selector('input[name="email"]', state="visible", timeout=10000)
                await page.fill('input[name="email"]', config.EMAIL)
                
                # Check if password field is visible. 
                # If not, we might need to click the button first (if it acts as "Next") or press Enter.
                # Use .first to avoid strict mode errors if multiple forms exist (e.g. login + register)
                password_input = page.locator('input[name="pass"]').first
                
                if not await password_input.is_visible():
                    print("Password hidden, clicking 'Connexion / Inscription'...")
                    # User specified button: <button ...> Connexion / Inscription </button>
                    # We target by text to be robust
                    next_btn = page.locator('button:has-text("Connexion / Inscription")').first
                    if await next_btn.is_visible():
                        await next_btn.click()
                    else:
                        print("Warning: 'Connexion / Inscription' button not found, trying Enter...")
                        await page.keyboard.press('Enter')
                    
                    # Wait for password to appear
                    await password_input.wait_for(state="visible", timeout=5000)

                # Fill Password
                print("Entering password...")
                await password_input.fill(config.PASSWORD)
                
                # Click Login Button
                print("Clicking login button...")
                # User specified: <button ...> Se connecter </button>
                await page.locator('button:has-text("Se connecter")').first.click()
                
                # Wait for navigation
                await page.wait_for_url('**/appli/**', timeout=15000)
                     
            except Exception as e:
                print(f"Login logic failed: {e}")
                await page.screenshot(path="error_login.png")
                # Continue strictly to debug if we are already logged in or if it's a soft error

            
            # Application often redirects or has a 'landing' dashboard.
            # We explicitly go to the reservation/planning page after login to be sure.
            try:
                await page.wait_for_url('**/appli/**', timeout=15000) # Wait for redirection to app
            except:
                print("Warning: Timeout waiting for redirect, forcing navigation to planning.")

            # Optimized: Inject LocalStorage for Filters and Popup
            # User tip: welcome_popup_seen=true, resa_filters={"sports": ["Padel"], "type": ["indoor"]}
            print("Injecting LocalStorage preferences...")
            
            await page.evaluate("""
                window.localStorage.setItem('welcome_popup_seen', true);
                window.localStorage.setItem('resa_filters', JSON.stringify({"sports": ["Padel"], "type": ["indoor"]}));
            """)
            
            print("Navigating to planning page (with pre-set filters)...")
            await page.goto(config.PLANNING_URL)
            
            # Wait for reload and grid
            # Match logic with user provided HTML structure
            # Wait for at least one slide or creneau container
            await page.wait_for_selector('swiper-slide, .creneaux', timeout=10000)
            
            # Check Slots
            print(f"Scanning for available slots matching: {target_slots}")
            available_results = {} # format: {"Date String": ["18:00"]}
            
            # Locate Day Slides
            slides = page.locator('swiper-slide')
            count = await slides.count()
            print(f"Found {count} days in calendar.")
            
            # We iterate through days
            for i in range(count):
                slide = slides.nth(i)
                
                # Extract Date Info
                # Text content: "jeu.\n12\nfévr." -> "jeu. 12 févr."
                date_text = await slide.inner_text()
                date_clean = " ".join(date_text.split())
                
                # Check if it's a valid day slide (sometimes empty slides exist)
                if not date_clean:
                    continue
                    
                print(f"Checking Day {i+1}: {date_clean}")
                
                # Filter by Day of Week
                # Map French short days to integers
                day_map = {
                    "lun.": 0, "mar.": 1, "mer.": 2, "jeu.": 3, "ven.": 4, 
                    "sam.": 5, "dim.": 6
                }
                
                # Identify current day index
                current_day_idx = -1
                for key, val in day_map.items():
                    if key in date_clean.lower():
                        current_day_idx = val
                        break
                
                if current_day_idx not in days_to_check:
                    print(f"Skipping {date_clean} (Not in target days)")
                    continue

                # Select the day
                # Only click if not already selected (class 'selected' on div inside)
                # But clicking valid slide is generally safe in this app
                await slide.click()
                
                # Wait for slots to load for this day
                # Since it's an SPA, we need a small buffer or check for update.
                # A 1.5s sleep is a practical robust solution here.
                time.sleep(1.5) 
                
                # Parse Slots by Card/Court
                day_slots = []
                # Only target cards that have slots structure
                cards = page.locator('.card:has(.creneaux)')
                count_cards = await cards.count()
                
                for k in range(count_cards):
                    card = cards.nth(k)
                    try:
                        # Get Court Name from h3
                        court_name = await card.locator('h3').inner_text()
                        court_name = court_name.strip()
                        
                        # Get slots in this card
                        slots_in_card = card.locator('.creneaux .heure')
                        count_slots = await slots_in_card.count()
                        
                        for j in range(count_slots):
                             slot_el = slots_in_card.nth(j)
                             if await slot_el.is_visible():
                                 slot_text = await slot_el.inner_text()
                                 slot_text = slot_text.strip()
                                 
                                 if slot_text in target_slots:
                                     day_slots.append(f"{slot_text} - {court_name}")
                    except Exception as e:
                        print(f"Error parsing card {k}: {e}")
                        continue
                
                # Remove duplicates and sort
                day_slots = sorted(list(set(day_slots)))
                
                if day_slots:
                    print(f"FOUND SLOTS on {date_clean}: {day_slots}")
                    # Flatten results for JSON output
                    # day_slots contains "18:00 - COURT"
                    # We want "jeu. 19 févr. 18:00 - COURT"
                    for slot in day_slots:
                        full_slot_str = f"{date_clean} {slot}"
                        available_results.setdefault(date_clean, []).append(slot)
                        
            # Prepare flattened list for n8n/JSON
            n8n_output = []
            for date, slots in available_results.items():
                for slot in slots:
                    n8n_output.append(f"{date} {slot}")
            
            # Write to JSON file
            import json
            with open("output.json", "w", encoding="utf-8") as f:
                json.dump(n8n_output, f, ensure_ascii=False, indent=2)
            print(f"\nJSON output written to output.json: {n8n_output}")

            # Send Notification if results found
            # Send Notification if results found
            if available_results:
                print("\nMatch found! See output.json")
            else:
                print("\nNo slots found matching criteria.")
                
            # Final Screenshot for verification
            await page.screenshot(path="final_scan.png")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            await page.screenshot(path="error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Padel Reservation Bot")
    parser.add_argument("--email", type=str, help="User email address")
    parser.add_argument("--password", type=str, help="User password")
    parser.add_argument("--days", type=int, nargs='+', default=[0, 1, 2, 3, 4], help="Days to check (0=Mon, 6=Sun). Default: 0-4")
    parser.add_argument("--slots", type=str, nargs='+', default=["18:00", "19:30"], help="Slots to check (e.g. 18:00 19:30). Default: 18:00 19:30")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")

    args = parser.parse_args()
    
    if args.email:
        config.EMAIL = args.email
    if args.password:
        config.PASSWORD = args.password
        
    if not config.EMAIL or not config.PASSWORD:
        print("Error: Email and Password must be provided via --email/--password arguments or .env file (MAS_EMAIL, MAS_PASSWORD).")
        exit(1)
        
    asyncio.run(check_availability(args.days, args.slots, args.headless))
