/**
 * Created by feng on 12/6/14.
 */

(function (undefined) {

    {% for func in api.funcs %}
    function {{func.name}}({% for arg in func.params %} {{arg.name}} {% end %} callback) {

    }
    {% end %}


    var r = {
    {% for idx, func in enumerate(api.funcs) %}
        {{func.name}}: {{func.name}} {% if idx < len(api.funcs) - 1%}, {% end %}

    {% end %}
    };

    if (typeof define == 'function' && define.amd) {
        return r;
    } else {
        window['_API'] = r;
    }
})();

// godep  gopm