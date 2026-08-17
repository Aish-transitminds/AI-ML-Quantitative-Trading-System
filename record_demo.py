import asyncio
import os
from playwright.async_api import async_playwright

async def record_demo():
    print("Starting Playwright to record the demo...")
    
    # Ensure the output directory exists
    output_dir = os.path.join(os.getcwd(), "demo_recording")
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser with video recording enabled
        browser = await p.chromium.launch(headless=False) # Set headless=True if you don't want to see the browser pop up
        context = await browser.new_context(
            record_video_dir=output_dir,
            record_video_size={"width": 1920, "height": 1080},
            viewport={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        url = "https://quantumgrow-ai.onrender.com"
        print(f"Navigating to {url}...")
        
        # Go to the website
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            print("Page loaded successfully. Recording for 30 seconds...")
            
            # Wait a few seconds to let the initial data populate
            await page.wait_for_timeout(5000)
            
            # Scroll down slowly to show different parts of the dashboard
            await page.mouse.wheel(0, 500)
            await page.wait_for_timeout(5000)
            
            await page.mouse.wheel(0, 500)
            await page.wait_for_timeout(5000)
            
            # Scroll back up
            await page.mouse.wheel(0, -1000)
            await page.wait_for_timeout(10000)
            
            # You can add more automated interactions here, e.g.:
            # await page.click("text=Settings")
            # await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"An error occurred while navigating: {e}")
        
        finally:
            print("Finishing recording...")
            # Closing the context saves the video
            await context.close()
            await browser.close()
            
            print(f"\nDone! Your video recording has been saved in the folder: {output_dir}")
            print("Look for a .webm file inside that folder.")

if __name__ == "__main__":
    asyncio.run(record_demo())
