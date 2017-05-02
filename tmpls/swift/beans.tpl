import Foundation

{% for bean in api.structs %}
class {{bean.name}} {
    {% for f in bean.fields %}var {{f.name}}:{{f.type('swift')}} = {{f.default('swift')}};
    {% end %}

    init({% for idx, f in enumerate(bean.requires) %}{{f.name}}:{{f.type('swift')}}{% if idx < len(bean.fields) - 1 %}, {% end %} {% end %}) {
        {% for f in bean.requires %}self.{{f.name}} = {{f.name}};
        {% end %}
     }

    init() {}
    init(d:NSDictionary) {
{% for f in bean.fields %}
    {% if f.is_primitive %}
        if let v = d["{{f.name}}"] as? {{f.type("swift")}} {
            self.{{f.name}} = v
        }
    {% elif f.list %}
        if let arr = d["{{f.name}}"] as? NSArray {
            for a in arr {
        {% if f.list_item.is_primitive %}
                if let v = a as? {{f.list_item.type("swift")}} {
                     self.{{f.name}}.append(v)
                }
        {% else %}
                if let v = a as? NSDictionary {
                    self.{{f.name}}.append({{f.list_item.t}}(d: v))
                }
        {% end %}
            }
        }
    {% else %}
        if let v = d["{{f.name}}"] as? NSDictionary {
            self.{{f.name}} = {{f.t}}(d: v)
        }
    {% end %}
{% end %}
    }
}
{% end %}