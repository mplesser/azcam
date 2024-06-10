$(document).ready(function() {

    // getstatus function
    function getstatus() {
        $.getJSON('/api/get_status', {}, function(data) {
            $("#imagetitle").text(data.data.imagetitle);
            $("#imagefilename").text(data.data.filename);
            $("#imagetype").text(data.data.imagetype);
            $("#exposuretime").text(data.data.exposuretime);
            $("#temps").text("Camera: " + data.data.camtemp + ", Dewar: " + data.data.dewtemp);
            $("#binning").text("(" + data.data.colbin + " x " + data.data.rowbin + ")");
            $("#testimage").text(data.data.imagetest);
            $("#exposurestate").text(data.data.exposurestate);
            $("#message").text(data.data.message);
            $("#servermode").text(data.data.mode);
            $("#progressbar").css("width", data.data.progressbar + "%");
            $("#progressbar").text(data.data.exposurelabel);
            $("#progressbar").css("background-color", data.data.exposurecolor);
            $("#timestamp").text(data.data.timestamp);
        });
        return false;
    }

    // set timer to get status
    setInterval(getstatus, 1000);


}); // end ready