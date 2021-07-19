/**
 * Sends fetch requests to update objects' properties using REST api endpoints.
 * @param {string} url Path to the REST api endpoint.
 * @param {{field: string, value: string}} data
 *     field: Name of the property field to update.
 *     value: Value to update the property field to.
 * @param {{none: string, some: string}} updateMessage
 *     none: Message when object update unsuccessful due to errors.
 *     some: Message when object update successful.
 */
 async function updateProperty(url, data, updateMessage) {
    const request = new Request(url, {
        method: 'PATCH',
        mode: "same-origin",
        headers: {
            "X-CSRFToken": Cookies.get("csrftoken"),
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    });

    await fetch(request)
        .then(response => {
            if (!response.ok) {
                response.text().then(text => {
                    // Error occurred, so update message specifies no objects updated
                    handleUpdateMessages(updateMessage.none);
                    handleErrorMessages(JSON.parse(text).detail);
                });
            } else {
                // Update message for successful changes
                handleUpdateMessages(updateMessage.some);
            }
        });
}

/**
 * Populates update messages for fetch requests.
 * @param {string} messageContent Text for update message.
 */
function handleUpdateMessages(messageContent) {
    let messages = document.getElementById("messages");
    if (messages == null) {
        messages = document.createElement("div");
        messages.setAttribute("id", "messages");
    }
    let message = document.createElement("div");
    message.setAttribute("class", "message");
    message.textContent = messageContent;
    messages.appendChild(message);
    if (messages) $(messages).insertAfter("nav");
}

/**
 * Populates error messages for fetch requests.
 * @param {string} errorMessage Text for error message.
 */
function handleErrorMessages(errorMessage) {
    let container = document.getElementById("main-content");
    let errorHeader = document.createElement("p");
    let errorList = document.createElement("ul");
    let error = document.createElement("li");
    errorHeader.textContent = "The following error was encountered while updating comments:";
    errorList.setAttribute("class", "errorlist");
    error.textContent = errorMessage;
    errorList.appendChild(error);
    container.prepend(errorList);
    container.prepend(errorHeader);
}

export { updateProperty };