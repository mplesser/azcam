$(document).ready(function () {
    
    // getstatus function
    function getstatus(){
        $.getJSON('/api/exposure/get_status', {}, function(data) {
            $("#imagetitle").text(data.data.imagetitle);
            $("#imagefilename").text(data.data.filename);
            $("#imagetype").text(data.data.imagetype);
            $("#exposuretime").text(data.data.exposuretime);
            $("#camtemp").text(data.data.camtemp);
            $("#dewtemp").text(data.data.dewtemp);
            $("#colbin").text(data.data.colbin);
            $("#rowbin").text(data.data.rowbin);
            $("#testimage").text(data.data.imagetest);
            $("#exposurestate").text(data.data.exposurestate);
            $("#message").text(data.data.message);
            $("#progressbar").css("width", data.data.progressbar + "%");
            $("#progressbar").text(data.data.exposurelabel);
            $("#title").css("background-color", data.data.exposurecolor);
            $("#timestamp").text(data.data.timestamp);
        });
        return false;
    }

    // set timer to get status
    setInterval(getstatus, 1000);  

    // example...
    $("#exposuretime" ).click(function() {
        var et = $("#exposuretime").val();
            et1=parseFloat(et);
            $("#testbox" ).text(et1.toFixed(3));
        });
    
        // **********************************************************************
        // initialization
        // **********************************************************************
        
        $( window ).load(function() {
          Initialize();
        });        
    
}); // end ready

    // **********************************************************************
    // functions
    // **********************************************************************
    
    var folder = document.getElementById("myInput");
    folder.onchange=function(){
      var files = folder.files,
          len = files.length,
          i;
      for(i=0;i<len;i+=1){
        console.log(files[i]);
      }
    }
        
    function selectFolder(e) {
        var theFiles = e.target.files;
        var relativePath = theFiles[0].webkitRelativePath;
        var folder = relativePath.split("/");
        alert(folder[0]);
    } 

    function Expose(et,it,title) {
        $("#message").text("starting exposure...");
        var testimage = $('#testimage')[0].checked;
        var et = $("#exposuretime").val();
        var it = $("#imagetype").val();
        var title = $("#title").val();
        var cmd="/obstool/expose?exposuretime="+et+"&imagetype="+it+"&title="+title+"&testimage="+testimage;
        $("#testbox").text(cmd);
        $.getJSON(cmd, {},
            function(data) {
            $("#message").text(data.message);
            $("#command").text(data.command);
            });
            return false;
    }
    
    function Sequence() {
    $("#message").text("starting exposure sequence...");
    $.getJSON('/obstool/sequence', {},
        function(data) {
        $("#message").text(data.message);
        $("#command").text(data.command);
        });
        return false;
    }
    
    function Reset() {
    $("#message").text("resetting camera...");
    $.getJSON('/obstool/reset', {},
        function(data) {
        $("#message").text(data.message);
        $("#command").text(data.command);
        });
        return false;
    }
    
    function Initialize() {
    $.getJSON('/obstool/initialize', {},
        function(data) {
        $("#message").text(data.message);
        $("#command").text(data.command);
        var prog = data.progress;
        $("#progressbar").progressbar({value: prog});
        $("#watchdog").text(data.watchdog);
        $("#camtemp").text(data.camtemp);
        $("#dewtemp").text(data.dewtemp);
        $("#filename").text(data.filename);
        $("#seqnumber").text(data.seqnumber);
        $("#exposuretime").val(data.exposuretime);
        $("#testbox").val(data.testimage);
        $("#title").val(data.title);
        if (data.testimage == 1) {
           $('#testimage').prop("checked", true);
        } else {
           $('#testimage').prop("checked", false);
        };
        });
        return false;
    }
    