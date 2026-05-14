# -*- coding: utf-8 -*-
{
    "name": "Event Studio",
    "summary": """Advanced Website Event Customizations """,
    "description": """
            Event Studio

            Provides advanced customizations for website events:
            - Event sidebar widgets
            - Event calendar
            - Advanced filters
            - Event UI enhancements
            - Custom event sections
            - Future event extensions
                """,
    "author": "Sakshi Davra",
    "category": "Website/Event",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "depends": [
        "website_event",
    ],

    "data": [
        # "views/event_calendar_sidebar.xml",
        'views/event_calendar.xml',



    ],

    "assets": {

            "web.assets_frontend": [

                # Flatpickr
                "event_studio/static/src/lib/flatpickr.min.css",
                "event_studio/static/src/lib/flatpickr.min.js",

                # # CSS
                "event_studio/static/src/css/event_calendar.css",
                # # JS
                "event_studio/static/src/js/event_calendar.js",

            ],
            'web.assets_backend': [

                'event_studio/static/src/xml/calendar_option.xml',
            ],

    },

    "installable": True,
}