// Javascript/jQuery code

$(document).ready(function() {

    // get_status function which runs on a timer
    function refresh() {
        //$("#message").text("refreshing...");
        location.reload(true);
        //$("#message").text("");
        
        return false;
    }

    // initialize everthing
    Initialize();

    // set timer for get_status
    setInterval(refresh, 3000);

}); // end ready function

$("#ID1_start").click(function() {
    Start_1();
});
$("#ID1_stop").click(function() {
    Stop_1();
});
$("#ID1_home").click(function() {
    var cmdport = $("#cmdport_1").text();
    var webport = parseInt(cmdport)+1;
    window.open("http://localhost:" + webport);;
});
$("#ID1_status").click(function() {
    var cmdport = $("#cmdport_1").text();
    var webport = parseInt(cmdport)+1;
    window.open("http://localhost:" + webport + "/status");;
});
$("#ID1_exposure").click(function() {
    var cmdport = $("#cmdport_1").text();
    var webport = parseInt(cmdport)+1;
    window.open("http://localhost:" + webport + "/exptool");;
});

$("#ID2_start").click(function() {
    Start_2();
});
$("#ID2_stop").click(function() {
    Stop_2();
});
$("#ID2_home").click(function() {
    var cmdport = $("#cmdport_2").text();
    var webport = parseInt(cmdport)+1;
    window.open("http://localhost:" + webport);;
});
$("#ID2_status").click(function() {
    var cmdport = $("#cmdport_2").text();
    var webport = parseInt(cmdport)+1;
    window.open("http://localhost:" + webport + "/status");;
});
$("#ID2_exposure").click(function() {
    var cmdport = $("#cmdport_2").text();
    var webport = parseInt(cmdport)+1;
    window.open("http://localhost:" + webport + "/exptool");;
});

$("#ID3_start").click(function() {
    Start_3();
});
$("#ID3_stop").click(function() {
    Stop_3();
});
$("#ID3_home").click(function() {
    var cmdport = $("#cmdport_3").text();
    var webport = parseInt(cmdport)+1;
    window.open("http://localhost:" + webport);;
});
$("#ID3_status").click(function() {
    var cmdport = $("#cmdport_3").text();
    var webport = parseInt(cmdport)+1;
    window.open("http://localhost:" + webport + "/status");;
});
$("#ID3_exposure").click(function() {
    var cmdport = $("#cmdport_3").text();
    var webport = parseInt(cmdport)+1;
    window.open("http://localhost:" + webport + "/exptool");;
});

$("#ID4_start").click(function() {
    Start_4();
});
$("#ID4_stop").click(function() {
    Stop_4();
});
$("#ID4_home").click(function() {
    var cmdport = $("#cmdport_4").text();
    var webport = parseInt(cmdport)+1;
    window.open("http://localhost:" + webport);;
});


function Start_1() {
    var cmdport = $("#cmdport_1").text();
    $("#message").text("Starting process on port "+cmdport);
    var cmd = "/api/start_process?cmd_port=" + cmdport;
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
        });
    location.reload();
    return false;
}

function Stop_1() {
    var cmdport = $("#cmdport_1").text();
    $("#message").text("Stopping process on port "+cmdport);
    var cmd = "/api/stop_process?cmd_port=" + cmdport;
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
        });
    location.reload();
    return false;
}

function Start_2() {
    var cmdport = $("#cmdport_2").text();
    $("#message").text("Starting process on port "+cmdport);
    var cmd = "/api/start_process?cmd_port=" + cmdport;
    $("#command").text(cmd);
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
        });
    location.reload();
    return false;
}

function Stop_2() {
    var cmdport = $("#cmdport_2").text();
    $("#message").text("Stopping process on port "+cmdport);
    var cmd = "/api/stop_process?cmd_port=" + cmdport;
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
        });
    location.reload();
    return false;
}

function Start_3() {
    var cmdport = $("#cmdport_3").text();
    var cmd = "/api/start_process?cmd_port=" + cmdport;
    $("#message").text("Starting process on port "+cmdport);
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
        });
    location.reload();
    return false;
}

function Stop_3() {
    var cmdport = $("#cmdport_3").text();
    var cmd = "/api/stop_process?cmd_port=" + cmdport;
    $("#message").text("Stopping process on port "+cmdport);
    $("#command").text(cmd);
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    location.reload();
    return false;
}

// ****************************************************************************
// Initialize function
// ****************************************************************************
function Initialize() {

    return false;
} // end Initialize()