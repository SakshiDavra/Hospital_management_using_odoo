/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.EventStudioCalendar =
publicWidget.Widget.extend({

    selector: ".event_studio_calendar_wrapper",

    async start() {

        if (!window.flatpickr) return;

        this.calendar = this.el.querySelector("#event_studio_calendar");

        this.popup = this.el.querySelector("#event_calendar_popup");

        this.upcoming = this.el.querySelector("#event_studio_upcoming_events");

        const result = await this._fetchEvents();

        this.events = {};

        result.forEach(event => {
            (this.events[event.date] ||= []).push(event);
        });

        this._renderUpcoming(result);
        this._initCalendar();
        this._bindPopupClose();
    },

    async _fetchEvents() {

        try {

            const response = await fetch(
                "/event/calendar/data",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: {},
                        id: 1,
                    }),
                }
            );

            return (await response.json()).result || [];

        } catch {
            return [];
        }
    },
    _renderUpcoming(events) {
        if (!this.upcoming) return;
        const upcoming = events
            .filter(e => new Date(e.datetime || e.date) >= new Date())
            .sort((a, b) => new Date(a.datetime || a.date) - new Date(b.datetime || b.date));

        this.upcoming.innerHTML = upcoming.length
            ? upcoming.map(event => `
                <div class="event_upcoming_item" data-url="${event.url}">
                    <div class="event_upcoming_dot"></div>
                    <div class="event_upcoming_info">
                        <div class="event_upcoming_name">${event.title}</div>
                        <div class="event_upcoming_date">${event.date}</div>
                    </div>
                </div>
            `).join("")
            : `<div class="event_upcoming_empty">No upcoming events found.</div>`;

        this.upcoming.querySelectorAll(".event_upcoming_item").forEach(item => {
            item.addEventListener("click", () => {
                window.location.href = item.dataset.url;
            });
        });
        if (upcoming.length > 3) {
            const container = this.upcoming;
            const scrollSpeed = 1; 
            const intervalTime = 50;

            setInterval(() => {

                if (container.scrollTop + container.clientHeight >= container.scrollHeight - 1) {
                    container.scrollTop = 0; 
                } else {
                    container.scrollTop += scrollSpeed;
                }
            }, intervalTime);
        }
    },

    _initCalendar() {
        flatpickr(this.calendar, {

                inline: true,
                static: true,
                disableMobile: true,
                dateFormat: "Y-m-d",
                defaultDate: "today",
                monthSelectorType: "dropdown",
            onDayCreate:
                this._onDayCreate.bind(this),
        });
    },

    _onDayCreate(dObj, dStr, fp, dayElem) {

        const date = [
            dayElem.dateObj.getFullYear(),

            String(
                dayElem.dateObj.getMonth() + 1
            ).padStart(2, "0"),

            String(
                dayElem.dateObj.getDate()
            ).padStart(2, "0"),

        ].join("-");

        const events = this.events[date];

        if (!events) return;

        dayElem.classList.add("has-event-date");
        const dot = document.createElement("span");
        dot.className = "calendar-event-dot";
        dayElem.appendChild(dot);

        dayElem.addEventListener("click", ev => {

            ev.stopPropagation();

            this.popup.innerHTML = events.map(event => `
                <div
                    class="calendar_popup_item"
                    data-url="${event.url}"
                >

                    <img
                        src="${event.image}"
                        class="calendar_popup_img"
                    />

                    <div class="calendar_popup_info">

                        <div class="calendar_popup_title">
                            ${event.title}
                        </div>

                        <div class="calendar_popup_location">
                            ${event.location || ""}
                        </div>

                    </div>

                </div>
            `).join("");

            this.popup.classList.remove( "event-popup-hidden");
            this.popup
                .querySelectorAll(".calendar_popup_item")
                .forEach(item => {

                    item.addEventListener("click", () => {
                        window.location.href = item.dataset.url;
                    });
                });
        });
    },

    _bindPopupClose() {
        document.addEventListener("click", ev => {
            if (!this.popup.contains(ev.target)&& !this.calendar.contains(ev.target))
            {
                this.popup.classList.add(
                    "event-popup-hidden"
                );
            }
        });
    },
});