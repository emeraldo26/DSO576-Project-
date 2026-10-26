"""AI-authored reproduction of reset-state discrepancy; requires the local app on port 8519."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out = Path(__file__).resolve().parent / 'browser-evidence'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 page=b.new_page(viewport={'width':1440,'height':1200});page.goto('http://localhost:8519')
 def n(k):page.wait_for_function('(k)=>document.querySelector(".js-plotly-plot")?.calcdata?.[0]?.length===k',arg=k,timeout=60000)
 def state():return page.evaluate('''()=>({n:document.querySelector('.js-plotly-plot')?.calcdata?.[0]?.length,checked:document.querySelector('input[aria-label="Use minimum exposure"]').checked,bound:document.querySelector('input[aria-label="Minimum AI exposure (%)"]').value})''')
 n(755);page.get_by_text('Use minimum exposure',exact=True).click()
 f=page.get_by_role('spinbutton',name='Minimum AI exposure (%)',exact=True);f.fill('50');f.press('Enter');n(11)
 before=state();page.get_by_role('button',name='Reset filters',exact=True).click();n(755);page.wait_for_timeout(1500);reset=state()
 page.get_by_role('combobox',name='Sort by',exact=True).click();page.get_by_role('option',name='Median annual wage',exact=True).click();page.wait_for_timeout(2000);after=state()
 result={'before':before,'after_reset':reset,'after_sort':after}
 (out / 'reset-results.json').write_text(json.dumps(result,indent=2))
 page.screenshot(path=str(out / '05-reset-followup.png'),full_page=True)
 print(result);b.close()
