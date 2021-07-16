import { updateProperty } from "./rest.js";

$( document ).ready(function() {
    function toggle_div(link_id, headers_id, label_show, label_hide) {
        const link = document.getElementById(link_id)
        const headers = document.getElementById(headers_id)

        const hidden = headers.style['display'] == 'none';

        if (hidden) {
            link.innerHTML = label_hide || 'hide';
            headers.style['display'] = 'block';
        } else {
            link.innerHTML = label_show || 'show';
            headers.style['display'] = 'none';
        }
    }

    $("button[id^='comment-action']").click((event) => {
        const patchId = document.getElementById("patch").dataset.patchId;
        const commentId = event.target.parentElement.dataset.commentId;
        const url = "/api/patches/" + patchId + "/comments/" + commentId + "/";
        const data = {'addressed': event.target.value} ;
        const updateMessage = {
            'none': "No comments updated",
            'some': "1 comment updated",
        };
        updateProperty(url, data, updateMessage);
        $("div[id^='comment-status-bar-'][data-comment-id='"+commentId+"']").toggleClass("hidden");
    });

    // Click listener to show/hide headers
    document.getElementById("toggle-patch-headers").addEventListener("click", function() {
        toggle_div("toggle-patch-headers", "patch-headers");
    });

    // Click listener to expand/collapse series
    document.getElementById("toggle-patch-series").addEventListener("click", function() {
        toggle_div("toggle-patch-series", "patch-series", "expand", "collapse");
    });

    // Click listener to show/hide related patches
    document.getElementById("toggle-related").addEventListener("click", function() {
        toggle_div("toggle-related", "related");
    });

    // Click listener to show/hide related patches from different projects
    document.getElementById("toggle-related-outside").addEventListener("click", function() {
        toggle_div("toggle-related-outside", "related-outside", "show from other projects");
    });

});