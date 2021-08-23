$( document ).ready(function() {
    $("#patch-list").stickyTableHeaders();

    $("#check-all").change(function(e) {
        if(this.checked) {
            $("#patch-list > tbody").checkboxes("check");
        } else {
            $("#patch-list > tbody").checkboxes("uncheck");
        }
        e.preventDefault();
    });
});