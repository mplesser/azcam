// Javascript/jQuery code for webobs.html

$(document).ready(function() {

    // get_status function which runs on a timer
    function watchdog() {
        $.getJSON('/api/webobs/watchdog', {}, function(data) {
            $("#timestamp").text(data.data.timestamp);
            $("#message").text(data.data.message);
            if (data.data.currentrow > 0) {
                HighlightRow(data.data.currentrow, 1);
            }
        });
        return false;
    };

    // initialize everthing
    Initialize();

    // set timer for get_status
    setInterval(watchdog, 500);

}); // end ready function

// ****************************************************************************
// Buttons
// ****************************************************************************
$("#load_script_btn").click(function() {
    LoadScript();
});

$("#run_btn").click(function() {
    RunScript();
});

$("#upload_btn").click(function() {
    Upload();
});


function LoadScript() {
    var scriptname = $("#scriptname").val();
    var cmd = "/api/webobs/load_script?scriptname=" + scriptname;
    $("#message").text("Loading script");
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
            var numtablecols = 17;
            // $("#table_data").text(data.data);

            // alert($('#script_table tr').eq(2).find('td').eq(3).text())

            // alert(data.data[1]);

            var numdatarows = data.data.length;
            var numdatacols = data.data[0].length;

            var tablerows = $("#script_table tr").length - 1;
            if (numdatarows > tablerows) {
                for (var extra = 0; extra < (numdatarows - tablerows); extra++) {
                    $("#script_table").append("<tr> <td></td>  <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td> <td></td></tr>");
                }
            }
            var row = 0;
            $("#script_table tr:gt(0)").each(function() {
                // alert($(this).text());
                // alert($(this).find('td').eq(2).text());
                // $(this).find('td').eq(1).text(data.data[0][0]);

                if (row < numdatarows) {
                    for (var col = 0; col < numdatacols; col++) {
                        // console.log($(this).find('td').eq(col).text());
                        $(this).find('td').eq(col).text(data.data[row][col]);
                    }
                    row++;
                } else {
                    $(this).remove();
                }
            });


        });
    return false;
}

function RunScript() {
    var cmd = "/api/webobs/run";
    $("#message").text("Running script");
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        }
    );

    return false;
};

/* function Upload() {
    // action = "http://localhost:2403/api/webobs/upload"
    // method = "POST"
    // enctype = "multipart/form-data"
    // alert("upload");
    $("#message").text("Uploading script");

    var post_url = $(this).attr("action"); //get form action url
    var request_method = $(this).attr("method"); //get form GET/POST method
    var form_data = $(this).serialize(); //Encode form elements for submission	
    $.ajax({
        url: post_url,
        type: request_method,
        data: form_data
    }).done(function(response) { //
        $("#message").html(response);
    });

    return false;
};
 */

function Upload() {
    var form_data = new FormData($('#upload_form')[0]);
    $.ajax({
        type: 'POST',
        url: '/api/webobs/upload',
        data: form_data,
        contentType: false,
        cache: false,
        processData: false,
        success: function(data) {
            console.log('Success!');
            $("#message").text(data.message);
        },
    });
};

function Initialize() {

    return false;
}

function HighlightRow(rownumber, toggle) {

    color = toggle ? "yellow" : "transparent"

    $("#script_table tr").eq(rownumber).css("background-color", color);
    // $("#script_table tr").eq(rownumber).css("opacity", "0.2");

    return false;
}