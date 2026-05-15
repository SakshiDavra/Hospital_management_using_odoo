from odoo import http
from odoo.http import request
import json


class EventCalendarController(http.Controller):

    @http.route(
        '/event/calendar/data',
        type='jsonrpc',
        auth='public',
        website=True
    )
    def event_calendar_data(self):

        events = request.env['event.event'].sudo().search([])
        result = []

        for event in events:

            if not event.date_begin:
                continue

            image_url = ""

            try:
                cover = json.loads(event.cover_properties or "{}")

                bg = cover.get("background-image", "")

                image_url = (
                    bg.replace("url('", "")
                    .replace("')", "")
                    .replace('url("', "")
                    .replace('")', "")
                )

            except Exception as e:
                print("IMAGE ERROR:", e)

            result.append({

                'title': event.name,

                'date':
                    event.date_begin.strftime('%Y-%m-%d'),

                'datetime':
                    event.date_begin.strftime('%Y-%m-%d %H:%M:%S'),

                'url': event.website_url,

                'location':
                    event.address_id.name
                    if event.address_id
                    else '',

                'image': image_url,
            })

        return result