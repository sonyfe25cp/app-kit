package {{api.ns}};

import java.util.*;

// Do not edit, auto generated by api-kit, kanzhun.com.
// {{api.ts}}

public class {{bean.name}} {
     {% for f in bean.fields %}public {{f.type('java')}} {{f.name}} {% if f.default('java') is not None %} = {{f.default('java')}} {% end %}; {% if f.optional %} // optional {% end %}
     {% end %}

     public {{bean.name}}() {
     }

     public {{bean.name}}({% for idx, f in enumerate(bean.requires) %}{{f.type('java')}} {{f.name}}{% if idx < len(bean.requires) - 1 %}, {% end %} {% end %}) {
        {% for f in bean.requires %} this.{{f.name}} = {{f.name}};
        {% end %}
        {% for f in bean.optionals %} {% if f.default('java') is not None %}
         this.{{f.name}} = {{f.default('java')}}; {% end %}
        {% end %}
     }

     public {{bean.name}}(Map<String, String> m) {
     {% for f in bean.fields %}
          {% if f.is_primitive %}
          this.{{f.name}} = Dispatcher.get{{f.t}}(m, "{{f.name}}");{% end %}
     {% end %}
     }
}
