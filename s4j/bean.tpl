package {{ns}};

import java.sql.*;


public class {{bean.name}} {% if bean.extends %} extends {{bean.extends}} {% end %} {
    {% for f in bean.fields_rs %} public static final String {{f.field.upper()}} = "{{f.name.lower()}}";
    {% end %}

    {% for t, name in bean.fields %} public final {{t}} {{name}};
    {% end %}
{% if not bean.extends %}
    public {{bean.name}}({% for idx, (t, name) in enumerate(bean.fields) %}{{t}} {{name}}{% if idx < len(bean.fields) - 1%}, {% end %}{% end %}) {
    {% for t, name in bean.fields %} this.{{name}} = {{name}};
    {% end %}
    }
{% end %}
    public {{bean.name}}(ResultSet rs) throws SQLException{
        {%if bean.extends %}super(rs); {% end %}
        {% for f in bean.fields_rs %}this.{{f.var}} = rs.{{f.method}}("{{f.field}}");
        {% end %}
    }

    public String toString() {
    {% if bean.extends %}
        StringBuffer sb = new StringBuffer(super.toString());
    {% else %}
        StringBuffer sb = new StringBuffer();
    {% end %}
        {% for t, name in bean.fields %}
        sb.append("{{name}}=").append({{name}}).append("\n"); {% end %}
        return sb.toString();
    }
}
