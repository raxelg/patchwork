import { updateProperty } from "./rest.js";

$( document ).ready(function() {
    let inlinePropertyDropdowns = $("td > select[class^='change-property-']");
    $(inlinePropertyDropdowns).each(function() {
        // Store previous dropdown selection
        $(this).data("prevProperty", $(this).val());
    });

    // Change listener for dropdowns that change an individual patch's delegate and state properties
    $(inlinePropertyDropdowns).change((event) => {
        const property = event.target.getAttribute("value");
        const { url, data } = getPatchProperties(event.target, property);
        const updateMessage = {
            'error': "No patches updated",
            'success': "1 patch updated",
        };
        updateProperty(url, data, updateMessage).then(isSuccess => {
            if (!isSuccess) {
                // Revert to previous selection
                $(event.target).val($(event.target).data("prevProperty"));
            } else {
                // Update to new previous selection
                $(event.target).data("prevProperty", $(event.target).val());
            }
        });
    });

    $("#patchlist").stickyTableHeaders();

    $("#check-all").change(function(e) {
        if(this.checked) {
            $("#patch-list > tbody").checkboxes("check");
        } else {
            $("#patch-list > tbody").checkboxes("uncheck");
        }
        e.preventDefault();
    });

    /**
     * Returns the data to make property changes to a patch through PATCH request.
     * @param {Element} propertySelect Property select element modified.
     * @param {string} property Patch property modified (e.g. "state", "delegate")
     * @return {{property: string, value: string}}
     *     property: Property field to be modified in request.
     *     value: New value for property to be modified to in request.
     */
    function getPatchProperties(propertySelect, property) {
        const selectedOption = propertySelect.options[propertySelect.selectedIndex];
        const patchId = propertySelect.parentElement.parentElement.dataset.patchId;
        const propertyValue = (property === "state") ? selectedOption.text
                            : (selectedOption.value === "*") ? null : selectedOption.value
        const data = {};
        data[property] = propertyValue;
        return {
            "url": `/api/patches/${patchId}/`,
            "data": data,
        };
    }
});
