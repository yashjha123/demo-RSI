window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        test: function(ignore) {
            console.log(ignore)
            return "HELLO";
        }
        // initial_semi: function(aval_data) {

        // }
    }
});