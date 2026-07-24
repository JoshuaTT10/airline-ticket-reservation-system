let airportOutsideClickBound = false;


document.addEventListener(
    "DOMContentLoaded",
    () => {
        initialiseSeatMap();
        initialiseAirportPickers();
    }
);


document.body.addEventListener(
    "htmx:afterSwap",
    () => {
        initialiseSeatMap();
        initialiseAirportPickers();
    }
);


function initialiseSeatMap() {
    const seatMap = document.querySelector(
        "[data-seat-map]"
    );

    if (
        !seatMap ||
        seatMap.dataset.initialised === "true"
    ) {
        return;
    }

    seatMap.dataset.initialised = "true";

    const passengerCount = Number(
        seatMap.dataset.passengerCount
    );

    const seatInput = document.querySelector(
        "#id_seat_ids"
    );

    const confirmButton = document.querySelector(
        "#confirm-booking-button"
    );

    const countLabel = document.querySelector(
        "#seat-selection-count"
    );

    const selectedSeatList = document.querySelector(
        "#selected-seat-list"
    );

    const passengerSeatLabels =
        document.querySelectorAll(
            "[data-passenger-seat]"
        );

    const buttons = Array.from(
        seatMap.querySelectorAll(
            "[data-seat-button]"
        )
    );

    if (
        !seatInput ||
        !confirmButton ||
        !countLabel ||
        !selectedSeatList
    ) {
        return;
    }

    let selectedSeats = [];

    const initialIds = new Set(
        seatInput.value
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean)
    );


    buttons.forEach((button) => {
        if (
            initialIds.has(
                button.dataset.seatId
            )
            &&
            selectedSeats.length
            < passengerCount
        ) {
            selectedSeats.push(
                {
                    id: button.dataset.seatId,
                    number:
                    button.dataset.seatNumber,
                }
            );

            button.classList.add(
                "seat-selected"
            );

            button.setAttribute(
                "aria-pressed",
                "true"
            );
        }
    });


    function updateDisplay() {
        seatInput.value = selectedSeats
            .map((seat) => seat.id)
            .join(",");

        countLabel.textContent =
            `${selectedSeats.length} of ` +
            `${passengerCount} selected`;

        selectedSeatList.textContent =
            selectedSeats.length === 0
                ? "Choose your seats below"
                : selectedSeats
                    .map(
                        (seat) => seat.number
                    )
                    .join(", ");

        passengerSeatLabels.forEach(
            (label, index) => {
                const seat =
                    selectedSeats[index];

                label.textContent = seat
                    ? `Seat ${seat.number}`
                    : "No seat";
            }
        );

        confirmButton.disabled =
            selectedSeats.length
            !== passengerCount;
    }


    buttons.forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                const seatId =
                    button.dataset.seatId;

                const seatNumber =
                    button.dataset.seatNumber;

                const existingIndex =
                    selectedSeats.findIndex(
                        (seat) =>
                            seat.id === seatId
                    );

                if (
                    existingIndex !== -1
                ) {
                    selectedSeats.splice(
                        existingIndex,
                        1
                    );

                    button.classList.remove(
                        "seat-selected"
                    );

                    button.setAttribute(
                        "aria-pressed",
                        "false"
                    );

                    updateDisplay();
                    return;
                }

                if (
                    selectedSeats.length
                    >= passengerCount
                ) {
                    return;
                }

                selectedSeats.push(
                    {
                        id: seatId,
                        number: seatNumber,
                    }
                );

                button.classList.add(
                    "seat-selected"
                );

                button.setAttribute(
                    "aria-pressed",
                    "true"
                );

                updateDisplay();
            }
        );
    });


    updateDisplay();
}


function initialiseAirportPickers() {
    const selects = document.querySelectorAll(
        "select[data-airport-select='true']"
    );

    selects.forEach((select) => {
        if (
            select.dataset.enhanced
            === "true"
        ) {
            return;
        }

        select.dataset.enhanced = "true";

        const wrapper =
            document.createElement("div");

        wrapper.className =
            "airport-combobox";


        const input =
            document.createElement("input");

        input.type = "search";

        input.className =
            "form-control airport-search-input";

        input.autocomplete = "off";

        input.setAttribute(
            "role",
            "combobox"
        );

        input.setAttribute(
            "aria-autocomplete",
            "list"
        );

        input.setAttribute(
            "aria-expanded",
            "false"
        );

        input.placeholder =
            select.name === "departure_city"
                ? "Search city or airport code"
                : "Search destination";


        const list =
            document.createElement("div");

        list.className =
            "airport-options";

        list.setAttribute(
            "role",
            "listbox"
        );

        list.hidden = true;


        const originalOptions =
            Array.from(select.options)
                .filter(
                    (option) => option.value
                )
                .map(
                    (option) => ({
                        value: option.value,
                        label:
                            option.textContent.trim(),
                    })
                );


        if (select.value) {
            const selectedOption =
                originalOptions.find(
                    (option) =>
                        option.value
                        === select.value
                );

            if (selectedOption) {
                input.value =
                    selectedOption.label;
            }
        }


        function closeList() {
            list.hidden = true;

            input.setAttribute(
                "aria-expanded",
                "false"
            );
        }


        function renderOptions(
            query = ""
        ) {
            const term =
                query
                    .trim()
                    .toLowerCase();

            const matches =
                originalOptions
                    .filter(
                        (option) =>
                            option.label
                                .toLowerCase()
                                .includes(term)
                    )
                    .slice(
                        0,
                        12
                    );

            list.innerHTML = "";

            if (
                matches.length === 0
            ) {
                const empty =
                    document.createElement(
                        "div"
                    );

                empty.className =
                    "airport-option-empty";

                empty.textContent =
                    "No matching airports";

                list.appendChild(empty);

            } else {
                matches.forEach(
                    (option) => {
                        const button =
                            document.createElement(
                                "button"
                            );

                        button.type =
                            "button";

                        button.className =
                            "airport-option";

                        button.setAttribute(
                            "role",
                            "option"
                        );

                        button.dataset.value =
                            option.value;

                        button.textContent =
                            option.label;


                        button.addEventListener(
                            "click",
                            () => {
                                select.value =
                                    option.value;

                                input.value =
                                    option.label;

                                input.setCustomValidity(
                                    ""
                                );

                                closeList();

                                select.dispatchEvent(
                                    new Event(
                                        "change",
                                        {
                                            bubbles: true,
                                        }
                                    )
                                );
                            }
                        );

                        list.appendChild(
                            button
                        );
                    }
                );
            }

            list.hidden = false;

            input.setAttribute(
                "aria-expanded",
                "true"
            );
        }


        input.addEventListener(
            "focus",
            () => {
                renderOptions(
                    input.value
                );
            }
        );


        input.addEventListener(
            "input",
            () => {
                select.value = "";

                input.setCustomValidity(
                    ""
                );

                renderOptions(
                    input.value
                );
            }
        );


        input.addEventListener(
            "keydown",
            (event) => {
                if (
                    event.key === "Escape"
                ) {
                    closeList();
                    input.blur();
                    return;
                }

                if (
                    event.key === "Enter"
                ) {
                    const firstOption =
                        list.querySelector(
                            ".airport-option"
                        );

                    if (
                        firstOption
                        && !list.hidden
                    ) {
                        event.preventDefault();

                        firstOption.click();
                    }
                }
            }
        );


        const form =
            select.closest("form");

        if (form) {
            form.addEventListener(
                "submit",
                (event) => {
                    if (
                        input.value.trim()
                        &&
                        !select.value
                    ) {
                        event.preventDefault();

                        input.setCustomValidity(
                            "Choose an airport "
                            + "from the list."
                        );

                        input.reportValidity();
                    }
                }
            );
        }


        select.classList.add(
            "airport-native-select"
        );


        select.parentNode.insertBefore(
            wrapper,
            select
        );

        wrapper.appendChild(
            input
        );

        wrapper.appendChild(
            list
        );

        wrapper.appendChild(
            select
        );
    });


    if (!airportOutsideClickBound) {
        airportOutsideClickBound = true;

        document.addEventListener(
            "click",
            (event) => {
                document
                    .querySelectorAll(
                        ".airport-combobox"
                    )
                    .forEach(
                        (wrapper) => {
                            if (
                                wrapper.contains(
                                    event.target
                                )
                            ) {
                                return;
                            }

                            const list =
                                wrapper.querySelector(
                                    ".airport-options"
                                );

                            const input =
                                wrapper.querySelector(
                                    ".airport-search-input"
                                );

                            if (list) {
                                list.hidden = true;
                            }

                            if (input) {
                                input.setAttribute(
                                    "aria-expanded",
                                    "false"
                                );
                            }
                        }
                    );
            }
        );
    }
}