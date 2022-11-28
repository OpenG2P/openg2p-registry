function httpGet(url) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("GET", url, false);
    xmlHttp.send(null);
    return xmlHttp.responseText;
}

document.getElementById("id_scan_button").onclick = function () {
    console.log("initializing........");
    const initialize_url = "http://localhost:12222/initialise";
    httpGet(initialize_url);

    const read_url = "http://127.0.0.1:12222/readdocument";
    const data = JSON.parse(httpGet(read_url));

    const gender_index_dict = {
        "": "0",
        Female: "1",
        Male: "2",
        Other: "3",
    };
    let gender = data.gender;
    if (!(gender in gender_index_dict)) {
        gender = "";
    }

    $("#o_field_input_34").val(data.family_name);
    $("#o_field_input_35").val(data.given_name);
    $("#o_field_input_17").val(data.birth_date);
    document.getElementById("o_field_input_20").selectedIndex = gender_index_dict[gender];

    $("#o_field_input_34").trigger("change");
    $("#o_field_input_35").trigger("change");
    $("#o_field_input_17").trigger("change");
    $("#o_field_input_20").trigger("change");

    console.log("shutting down........");
    const shutdown_url = "http://localhost:12222/shutdown";
    httpGet(shutdown_url);
};
