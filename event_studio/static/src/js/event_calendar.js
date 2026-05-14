/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.EventStudioCalendar =
    publicWidget.Widget.extend({

    selector: ".event_studio_calendar_wrapper",

    async start() {

        if (!window.flatpickr) {
            return Promise.resolve();
        }

        const calendarDiv =
            this.el.querySelector("#event_studio_calendar");

        const popup =
            this.el.querySelector("#event_calendar_popup");

        if (!calendarDiv || !popup) {
            return Promise.resolve();
        }

        let result = [];

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

            const data = await response.json();

            result = data.result || [];

        } catch {
            return Promise.resolve();
        }

        const events = {};

        result.forEach(event => {

            if (!events[event.date]) {
                events[event.date] = [];
            }

            events[event.date].push(event);
        });

        flatpickr(calendarDiv, {

            inline: true,

            disableMobile: true,

            dateFormat: "Y-m-d",

            defaultDate: "today",

            onDayCreate(dObj, dStr, fp, dayElem) {

                const date = [
                    dayElem.dateObj.getFullYear(),
                    String(
                        dayElem.dateObj.getMonth() + 1
                    ).padStart(2, "0"),
                    String(
                        dayElem.dateObj.getDate()
                    ).padStart(2, "0"),
                ].join("-");

                if (!events[date]) {
                    return;
                }

                dayElem.classList.add(
                    "has-event-date"
                );

                const dot =
                    document.createElement("span");

                dot.className =
                    "calendar-event-dot";

                dayElem.appendChild(dot);

                dayElem.addEventListener(
                    "click",

                    ev => {

                        ev.stopPropagation();

                        popup.innerHTML =
                            events[date]
                                .map(event => `

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

                                `)
                                .join("");

                        popup.classList.remove(
                            "event-popup-hidden"
                        );

                        const rect =
                            dayElem.getBoundingClientRect();

                        const parentRect =
                            calendarDiv.getBoundingClientRect();

                        popup.style.top =
                            `${rect.top - parentRect.top + 45}px`;

                        popup.style.left =
                            `${rect.left - parentRect.left - 40}px`;

                        popup
                            .querySelectorAll(
                                ".calendar_popup_item"
                            )
                            .forEach(item => {

                                item.addEventListener(
                                    "click",

                                    () => {
                                        window.location.href =
                                            item.dataset.url;
                                    }
                                );
                            });
                    }
                );
            },
        });

        document.addEventListener(
            "click",

            ev => {

                if (
                    !popup.contains(ev.target)
                    &&
                    !calendarDiv.contains(ev.target)
                ) {

                    popup.classList.add(
                        "event-popup-hidden"
                    );
                }
            }
        );

        return Promise.resolve();
    },
});