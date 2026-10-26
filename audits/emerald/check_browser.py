"""AI-authored browser audit. Requires local app at localhost:8519 and Playwright/Chrome."""
import json
import math
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path(__file__).resolve().parent / 'browser-evidence'
out.mkdir(exist_ok=True)
report = {}
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True)
    page = browser.new_page(viewport={'width':1440, 'height':1200})
    page.goto('http://localhost:8519')
    def wait_chart(n):
        page.wait_for_function('(n)=>document.querySelector(".js-plotly-plot")?.calcdata?.[0]?.length===n', arg=n, timeout=60000)
    def state():
        return page.locator('.js-plotly-plot').first.evaluate('''e=>({
            points:e.calcdata[0].map(p=>({x:p.x,y:p.y,soc:p.data[0],custom:p.data,size:p.ms,color:p.mc})),
            sizemode:e._fullData[0].marker.sizemode,sizeref:e._fullData[0].marker.sizeref,
            axes:[e.layout.xaxis.title.text,e.layout.yaxis.title.text],
            range:[e.layout.coloraxis.cmin,e.layout.coloraxis.cmax],
            shapes:e.layout.shapes,
            paths:Array.from(e.querySelectorAll('.scatterlayer .points path.point')).map(p=>p.getAttribute('d'))
        })''')
    def search(text):
        field=page.get_by_role('textbox',name='Search title or SOC (literal)',exact=True)
        field.fill(text);field.press('Enter')
    wait_chart(755)
    initial=state()
    assert initial['axes']==['BLS projected employment change (%)','Observed AI exposure (%)']
    assert initial['range']==[0,100] and initial['sizemode']=='area'
    assert any(s['x0']==s['x1']==0 for s in initial['shapes'])
    body=page.locator('body').inner_text()
    assert 'Chart omits 0 occupations' in body and 'Neither axis is an individual job-loss probability' in body
    report['default']={'points':755,'axes':initial['axes'],'color_range':initial['range'],'sizemode':initial['sizemode'],'reference_line':True,'caption_and_omissions':True}
    # Compare actual SVG circle radii against employment values, within one chart scale.
    ratios=[]
    for point,path in zip(initial['points'],initial['paths']):
        radius=float(path.split('A',1)[1].split(',',1)[0])
        ratios.append(radius*radius/point['size'])
    # Plotly rounds SVG path coordinates to two decimals.
    for point,path in zip(initial['points'],initial['paths']):
        radius=float(path.split('A',1)[1].split(',',1)[0])
        expected=math.sqrt(point['size']/(2*initial['sizeref']))
        assert abs(radius-expected)<=0.006
    report['bubble_area']={'svg_markers_checked':len(ratios),'result':'Rendered circle radii match sqrt(employment/(2*sizeref)) within 0.006 pixels; area is proportional to employment.'}
    page.screenshot(path=str(out/'01-default.png'),full_page=True)
    search('15-1251');wait_chart(1)
    point=state()['points'][0]
    assert point['soc']=='15-1251' and point['x']==-7.3 and point['y']==74.51
    assert point['custom'][6:9]==['74.51%','-7.3%','110,800']
    marker=page.locator('.js-plotly-plot').first.locator('.scatterlayer .points path.point').first
    marker.hover(force=True)
    page.locator('.hoverlayer .hovertext').first.wait_for(timeout=10000)
    hover=page.locator('.hoverlayer').first.text_content()
    assert all(s in hover for s in ['Computer Programmers','15-1251','74.51%','-7.3%','110,800','Wage:','components:'])
    report['programmers']={'point':point,'actual_hover':hover}
    page.screenshot(path=str(out/'02-programmers-hover.png'),full_page=True)
    search('');wait_chart(755)
    page.get_by_text('Use minimum exposure',exact=True).click()
    minimum=page.get_by_role('spinbutton',name='Minimum AI exposure (%)',exact=True)
    minimum.fill('50');minimum.press('Enter')
    page.wait_for_function('()=>{let p=document.querySelector(".js-plotly-plot")?.calcdata?.[0];return p?.length>0 && p.length<755 && p.every(d=>d.y>=50)}',timeout=60000)
    filtered=state()
    report['filter']={'minimum_exposure_percent':50,'points':len(filtered['points']),'minimum_y':min(d['y'] for d in filtered['points'])}
    page.screenshot(path=str(out/'03-filter.png'),full_page=True)
    # Disable the exposure bound before checking sort invariance.
    page.get_by_text('Use minimum exposure',exact=True).click();wait_chart(755)
    page.wait_for_timeout(1000)
    sort=page.get_by_role('combobox',name='Sort by',exact=True)
    sort.click()
    page.get_by_role('option',name='Median annual wage',exact=True).click()
    page.wait_for_timeout(1500)
    after=state()
    assert sorted((d['soc'],d['color']) for d in initial['points'])==sorted((d['soc'],d['color']) for d in after['points'])
    assert after['range']==[0,100]
    report['sort']={'selected':'Median annual wage','color_values_unchanged':True,'range_unchanged':True}
    search('NO_OCCUPATION_MATCH_987654321')
    page.get_by_text('No occupations match these filters',exact=True).wait_for(timeout=60000)
    page.wait_for_function('()=>document.querySelectorAll(".js-plotly-plot").length===0',timeout=60000)
    assert 'Chart omits 0 occupations' in page.locator('body').inner_text()
    report['empty']={'message':True,'plot_count':0,'omitted':0}
    page.screenshot(path=str(out/'04-empty.png'),full_page=True)
    assert page.get_by_test_id('stException').count()==0
    browser.close()
(out/'results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
