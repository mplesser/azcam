// Javascript/jQuery code for exptool.html

$(document).ready(function() {

    // get_status function which runs on a timer
    function getstatus() {
        $.getJSON('/api/get_status', {}, function(data) {
            $("#imagetitle_status").text(decodeURI(data.data.imagetitle));
            $("#imagefilename_status").text(data.data.filename);
            $("#exposuretime_status").text(data.data.exposuretime);
            $("#camtemp").text(data.data.camtemp);
            $("#dewtemp").text(data.data.dewtemp);
            $("#colbin_status").text(data.data.colbin);
            $("#rowbin_status").text(data.data.rowbin);
            $("#message").text(data.data.message);
            $("#progressbar").css("width", data.data.progressbar + "%");
            $("#progressbar").text(data.data.exposurelabel);
            $("#progressbar").css("background-color", data.data.exposurecolor);
            $("#timestamp").text(data.data.timestamp);
            $("#command").text(data.data.command);
            $("#testimage_status").text(data.data.imagetest);
        });
        return false;
    }

    // initialize everthing
    Initialize();

    // set timer for get_status
    setInterval(getstatus, 1000);

    // trigger events when tabs change
    $(document).on('shown.bs.tab', function(event) {
        var x = $(event.target).text(); // active tab
        var y = $(event.relatedTarget).text(); // previous tab
        if (x == "Exposure") {} else if (x == "Filename") {
            GetFilename();
        } else if (x == "Detector") {
            GetDetector()
        } else if (x == "Options") {
            GetOptions();
        }
    });

}); // end ready function

// ****************************************************************************
// Exposure pane
// ****************************************************************************
$("#expose").click(function() {
    Expose();
});
$("#sequence").click(function() {
    Sequence();
});
$("#reset").click(function() {
    Reset();
});
$("#abort").click(function() {
    Abort();
});
$("#save_pars").click(function() {
    Save_Pars();
});
$("#imagetest").click(function() {
    ImageTest();
});
$("#imagetitle").change(function() {
    ImageTitle();
});
$("#exposuretime").change(function() {
    ExposureTime();
});

function ImageTest() {
    var ti = $("#imagetest").prop("checked");
    var imagetest = (ti ? 1 : 0);
    var cmd = "/api/set_par?parameter=imagetest&value=" + imagetest;
    $("#message").text(cmd);
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    return false;
}

function ImageTitle() {
    var imagetitle = $("#imagetitle").val();
    var cmd = "/api/set_image_title?title=" + imagetitle;
    $("#message").text(cmd);
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    return false;
}

function ExposureTime() {
    var et = $("#exposuretime").val();
    var cmd = "/api/set_exposuretime?exposure_time=" + et;
    $("#message").text(cmd);
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    return false;
}

function Expose(et, it, title) {
    $("#message").text("starting exposure...");
    var imagetest = $('#imagetest')[0].checked;
    var et = $("#exposuretime").val();
    var it = $("#imagetype").val();
    var title = $("#imagetitle").val();
    var cmd = "/api/expose1?exposure_time=" + et + "&image_type=" + it + "&image_title=" + title;
    $("#command").text(cmd);
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    return false;
}

function Sequence() {
    $("#message").text("starting exposure sequence...");
    var seq_total = $("#seq_total").val();
    var seq_delay = $("#seq_delay").val();
    var seq_flush = $("#seq_flush").val();
    if (seq_flush == "All") {
        sf = 0;
    } else if (seq_flush == "Once") {
        sf = 1;
    } else if (seq_flush == "None") {
        sf = 2;
    } else {
        s
    }
    f = 0;

    var et = $("#exposuretime").val();
    var it = $("#imagetype").val();
    var title = $("#imagetitle").val();
    var cmd = "/api/set_exposuretime?exposure_time=" + et;
    $("#message").text(cmd);
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    var cmd = "/api/set_image_type?imagetype=" + it;
    $("#message").text(cmd);
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    var cmd = "/api/set_image_title?title=" + title;
    $("#message").text(cmd);
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });

    var cmd = "/api/sequence1?number_exposures=" + seq_total +
        "&flush_array_flag=" + sf + "&delay=" + seq_delay
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    return false;
}

function Reset() {
    $("#message").text("resetting camera...");
    $.getJSON('/api/reset', {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    return false;
}

function Abort() {
    $("#message").text("aborting exposure...");
    $.getJSON('/api/abort', {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    return false;
}

function Save_Pars() {
    $("#message").text("saving parameters...");
    $.getJSON('/api/save_pars', {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    return false;
}

function GetExposureInfo() {
    $.getJSON('/api/get_image_title', {},
        function(data) {
            $("#imagetitle").val(decodeURI(data.data));
        });
    $.getJSON('/api/get_image_types', {},
        function(data) {
            for (var dd in data.data) {
                var val = data.data[dd];
                $("#imagetype").append($('<option></option>').val(val).html(val));
            }
        });
    $.getJSON('/api/get_image_type', {},
        function(data) {
            $("#imagetype").val(data.data);
        });
    $.getJSON('/api/get_par?parameter=imagetest', {},
        function(data) {
            $('#imagetest')[0].checked = data.data;
        });
    $.getJSON('/api/get_exposuretime', {},
        function(data) {
            $("#exposuretime").val(data.data);
        });
    $.getJSON('/api/get_par?parameter=exposuresequencetotal', {},
        function(data) {
            $("#seq_total").val(data.data);
        });
    $.getJSON('/api/get_par?parameter=exposuresequencedelay', {},
        function(data) {
            $("#seq_delay").val(data.data);
        });
    $.getJSON('/api/get_par?parameter=exposuresequenceflush', {},
        function(data) {
            var seq_flush = data.data;
            if (seq_flush == 0) {
                $("#seq_flush").val("All");
            } else if (seq_flush == "1") {
                $("#seq_flush").val("Once");
            } else if (seq_flush == 2) {
                $("#seq_flush").val("None");
            } else {
                $("#seq_flush").val("All");
            }
        });
}


// ****************************************************************************
// Filename pane
// ****************************************************************************
$("#imagefolder").change(function() {
    imagefolder();
});
$("#imagesequencenumber").change(function() {
    imagesequencenumber();
});
$("#imageroot").change(function() {
    imageroot();
});
$("#imageautoincrementsequencenumber").change(function() {
    imageautoincrementsequencenumber();
});
$("#imageoverwrite").change(function() {
    imageoverwrite();
});
$("#imageincludesequencenumber").change(function() {
    imageincludesequencenumber();
});
$("#imageautoname").change(function() {
    imageautoname();
});

function GetFilename() {
    $.getJSON('/api/get_par?parameter=imagefolder', {},
        function(data) {
            $("#imagefolder").val(decodeURI(data.data));
        });
    $.getJSON('/api/get_par?parameter=imagesequencenumber', {},
        function(data) {
            $("#imagesequencenumber").val(data.data);
        });
    $.getJSON('/api/get_par?parameter=imageroot', {},
        function(data) {
            $("#imageroot").val(data.data);
        });
    $.getJSON('/api/get_par?parameter=imageautoincrementsequencenumber', {},
        function(data) {
            $("#imageautoincrementsequencenumber").prop("checked", data.data);
        });
    $.getJSON('/api/get_par?parameter=imageincludesequencenumber', {},
        function(data) {
            $("#imageincludesequencenumber").prop("checked", data.data);
        });
    $.getJSON('/api/get_par?parameter=imageautoname', {},
        function(data) {
            $("#imageautoname").prop("checked", data.data);
        });
    $.getJSON('/api/get_par?parameter=imageoverwrite', {},
        function(data) {
            $("#imageoverwrite").prop("checked", data.data);
        });
    return false;
}

function imagefolder() {
    var imagefolder = $("#imagefolder").val();
    $.getJSON('/api/set_par?parameter=imagefolder&value=' + imagefolder, {},
        function(data) {});

    return false;
}

function imagesequencenumber() {
    var imagenumber = $("#imagesequencenumber").val();
    $.getJSON('/api/set_par?parameter=imagesequencenumber&value=' + imagenumber, {},
        function(data) {});

    return false;
}

function imageroot() {
    var imageroot = $("#imageroot").val();
    $.getJSON('/api/set_par?parameter=imageroot&value=' + imageroot, {},
        function(data) {});

    return false;
}

function imageautoincrementsequencenumber() {
    var imageautoincrementsequencenumber = $("#imageautoincrementsequencenumber").prop("checked");
    imageautoincrementsequencenumber = (imageautoincrementsequencenumber ? 1 : 0)
    $.getJSON('/api/set_par?parameter=imageautoincrementsequencenumber&value=' + imageautoincrementsequencenumber, {},
        function(data) {});

    return false;
}

function imageoverwrite() {
    var imageoverwrite = $("#imageoverwrite").prop("checked");
    imageoverwrite = (imageoverwrite ? 1 : 0)
    $.getJSON('/api/set_par?parameter=imageoverwrite&value=' + imageoverwrite, {},
        function(data) {});

    return false;
}

function imageincludesequencenumber() {
    var imageincludesequencenumber = $("#imageincludesequencenumber").prop("checked");
    imageincludesequencenumber = (imageincludesequencenumber ? 1 : 0)
    $.getJSON('/api/set_par?parameter=imageincludesequencenumber&value=' + imageincludesequencenumber, {},
        function(data) {});

    return false;
}

function imageautoname() {
    var imageautoname = $("#imageautoname").prop("checked");
    imageautoname = (imageautoname ? 1 : 0)
    $.getJSON('/api/set_par?parameter=imageautoname&value=' + imageautoname, {},
        function(data) {});

    return false;
}

// ****************************************************************************
// Detector pane
// ****************************************************************************
$("#fullframe").click(function() {
    fullframe();
});
$("#applyroi").click(function() {
    applyroi();
});

function fullframe() {
    $("#message").text("setting ROI to full frame...");
    $.getJSON('/api/roi_reset', {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    $.getJSON('/api/get_roi', {},
        function(data) {
            $("#firstcol").val(data.data[0]);
            $("#lastcol").val(data.data[1]);
            $("#firstrow").val(data.data[2]);
            $("#lastrow").val(data.data[3]);
            $("#colbin").val(data.data[4]);
            $("#rowbin").val(data.data[5]);
        });
    return false;
}

function applyroi() {
    $("#message").text("setting ROI...");
    var firstcol = $("#firstcol").val();
    var lastcol = $("#lastcol").val();
    var colbin = $("#colbin").val();
    var firstrow = $("#firstrow").val();
    var lastrow = $("#lastrow").val();
    var rowbin = $("#rowbin").val();
    cmd = "/api/set_roi?" +
        "first_col=" + firstcol +
        "&last_col=" + lastcol +
        "&col_bin=" + colbin +
        "&first_row=" + firstrow +
        "&last_row=" + lastrow +
        "&row_bin=" + rowbin
    $.getJSON(cmd, {},
        function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
        });
    return false;
}

function GetDetector() {
    $.getJSON('/api/get_roi', {},
        function(data) {
            $("#firstcol").val(data.data[0]);
            $("#lastcol").val(data.data[1]);
            $("#firstrow").val(data.data[2]);
            $("#lastrow").val(data.data[3]);
            $("#colbin").val(data.data[4]);
            $("#rowbin").val(data.data[5]);
        });
    return false;
}

// ****************************************************************************
// Options pane
// ****************************************************************************
$("#flusharray").click(function() {
    flusharray();
});
$("#displayimage").click(function() {
    displayimage();
});
$("#instrumentenabled").click(function() {
    instrumentenabled();
});
$("#telescopeenabled").click(function() {
    telescopeenabled();
});
$("#autotitle").click(function() {
    autotitle();
});

function flusharray() {
    var x = $("#flusharray").prop("checked");
    x = (x ? 1 : 0)
    $.getJSON('/api/set_par?parameter=flusharray&value=' + x, {},
        function(data) {});

    return false;
}

function displayimage() {
    var x = $("#displayimage").prop("checked");
    x = (x ? 1 : 0)
    $.getJSON('/api/set_par?parameter=displayimage&value=' + x, {},
        function(data) {});
    return false;
}

function instrumentenabled() {
    var x = $("#instrumentenabled").prop("checked");
    x = (x ? 1 : 0)
    $.getJSON('/api/set_par?parameter=instrumentenabled&value=' + x, {},
        function(data) {});
    return false;
}

function telescopeenabled() {
    var x = $("#telescopeenabled").prop("checked");
    x = (x ? 1 : 0)
    $.getJSON('/api/set_par?parameter=telescopeenabled&value=' + x, {},
        function(data) {});
    return false;
}

function autotitle() {
    var x = $("#autotitle").prop("checked");
    x = (x ? 1 : 0)
    $.getJSON('/api/set_par?parameter=autotitle&value=' + x, {},
        function(data) {});
    return false;
}

function GetOptions() {
    $.getJSON('/api/get_par?parameter=flusharray', {},
        function(data) {
            $("#flusharray").prop("checked", data.data);
        });
    $.getJSON('/api/get_par?parameter=displayimage', {},
        function(data) {
            $("#displayimage").prop("checked", data.data);
        });
    $.getJSON('/api/get_par?parameter=instrumentenabled', {},
        function(data) {
            $("#instrumentenabled").prop("checked", data.data);
        });
    $.getJSON('/api/get_par?parameter=telescopeenabled', {},
        function(data) {
            $("#telescopeenabled").prop("checked", data.data);
        });
    $.getJSON('/api/get_par?parameter=autotitle', {},
        function(data) {
            $("#autotitle").prop("checked", data.data);
        });

    return false;
}

// ****************************************************************************
// Initialize function
// ****************************************************************************
function Initialize() {

    // exposure tab
    GetExposureInfo();

    // filename tab
    GetFilename();

    // detector tab
    GetDetector();

    // options tab
    GetOptions();

    return false;
} // end Initialize()