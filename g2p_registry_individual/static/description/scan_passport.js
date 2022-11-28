odoo.define(function (require) {
    var ajax = require("web.ajax");

    document.getElementById("id_scan_button").onclick = function () {
        ajax.jsonRpc("/web/dataset/call_kw", "call", {
            model: "res.partner",
            method: "scan_passport",
            args: [],
            kwargs: {
                context: {},
            },
        }).then(function (data) {
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
        });
    };
});
