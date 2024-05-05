from django.http import HttpResponse, HttpResponseRedirect
from .assets.dbrxlib import dbrxlib
from .assets.helper import event_search_table, place_search_table
from django.shortcuts import render, redirect
from markdown import markdown
import re
import time


dxl = dbrxlib('dapi332901199cd5c09211e054893ef8bda9')

def convert_markdown_links(markdown_content):
    # Regular expression to find Markdown links
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    # Replace Markdown links with HTML anchor tags
    return re.sub(pattern, r'<a href="\2">\1</a>', markdown_content)

def input_view(request):
    if request.method == 'POST':
        prompt = request.POST.get("prompt")
        
        # Searches
        gsearches = dxl.prompt_to_gsearch(prompt, rt = "pure")
        time.sleep(3)
        loc_searches = dxl.prompt_to_loc_search(prompt, rt = "pure")
        time.sleep(3)
        
        # Tables
        event_table = event_search_table(gsearches)
        loc_table = place_search_table(loc_searches)

        # Date Filter
        date1, date2 = dxl.get_date_range(prompt)
        time.sleep(3)
        event_table = event_table[(event_table.start_time >= date1) & (event_table.start_time <= date2)]

        # Results
        event_result = dxl.event_table_recommend(event_table, prompt)['choices'][0]['message']['content']
        time.sleep(3)
        loc_result = dxl.place_table_recommend(loc_table, prompt)['choices'][0]['message']['content']
        time.sleep(3)

        event_convert_links = convert_markdown_links(event_result)
        time.sleep(3)
        loc_convert_links = convert_markdown_links(loc_result)
        time.sleep(3)
        
        event_to_html = markdown(event_convert_links)
        loc_to_html = markdown(loc_convert_links)

        return render(request, 'input.html', {"prompt": prompt, 'event_result': event_to_html, 'loc_result': loc_to_html})

    return render(request, 'input.html')