package {{ns}};

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.sql.DataSource;
import java.sql.*;
import java.util.*;
import java.util.concurrent.*;


public class DBApi {
    protected static Logger logger = LoggerFactory.getLogger(DBApi.class);

    {% for func in funcs %}
     public static {{func.resp}} {{func.name}} (Connection con {% for idx, (t, name) in enumerate(func.args) %}, {{t}} {{name}} {% end %})
        throws SQLException {
        {% if func.list_arg %}
            if( {{func.list_arg}} == null || {{func.list_arg}}.isEmpty() ) {
                {% if func.is_group_py %}
                return new HashMap<>();
                {% elif func.resp_is_list %}
                return new ArrayList<>();
                {% end %}
            }
        {% end %}


            String sql = "{{func.sql}}";
        {% if func.generate_id %}
            PreparedStatement ps = con.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS);
        {% else %}
            PreparedStatement ps = con.prepareStatement(sql);
        {% end %}
        {% for idx, arg in func.sql_args %}
            ps.setObject({{idx}}, {{arg}}); {% end %}

        {% if func.update_insert %}
            ps.executeUpdate();
        {% else %}
            ResultSet rs = ps.executeQuery();
        {% end %}

        {% if func.is_group_py %}
            {{func.resp}} results = new HashMap<>(768);

            while (rs.next()) {
            try {
                {{func.resp_bean}} d = new {{func.resp_bean}}(rs);
            {% if func.is_group_by_list %}
                List<{{func.resp_bean}}> arr = results.get(d.{{func.group_key}});
                if (arr == null) {
                    arr = new ArrayList<>(4);
                    results.put(d.{{func.group_key}}, arr);
                }
                arr.add(d);
            {% else %}
                results.put(d.{{func.group_key}}, d);
            {% end %}
            } catch(SQLException e) {
            // logger.error(e.getMessage(), e);
                logger.error("GET ERROR {} {}, when {}", e.getClass().getSimpleName(), e.getMessage(),  "{{func.name}}");
            }
            }
            ps.close();
            rs.close();
            return results;
        {% elif func.resp_is_list %}
            {{func.resp}} results = new ArrayList<>();
            while (rs.next()) {
            try {
                {% if "String" == func.resp_bean %}
                    results.add(rs.getString(1));
                {% elif "Integer" == func.resp_bean %}
                    results.add(rs.getInt(1));
                {% else %}
                    results.add(new {{func.resp_bean}}(rs));
                {% end %}

            } catch(SQLException e) {
            // logger.error(e.getMessage(), e);
                logger.error("GET ERROR {} {}, when {}", e.getClass().getSimpleName(), e.getMessage(),  "{{func.name}}");
            }
            }
            ps.close();
            rs.close();
            return results;
        {% elif func.generate_id %}
            ResultSet rs = ps.getGeneratedKeys();
            if (rs.next()) {
                return rs.getInt(1);
            }
            return 0;
        {% elif func.is_primitive%}

            if (rs.next()) {
                return rs.{{func.is_primitive[0]}}(1);
            } else {
                return {{func.is_primitive[1]}};
            }

        {% elif func.has_resp %}
            if (rs.next()) {
                return new {{func.resp_bean}}(rs);
            } else {
                return null;
            }
        {% end %}
     }

    {% if func.resp != 'void' %}
    public static Future<{{func.resp_obj}}> {{func.name}} (final DataSource ds {% for idx, (t, name) in enumerate(func.args) %}, final {{t}} {{name}} {% end %},ExecutorService pool) {
        return pool.submit(new Callable<{{func.resp_obj}}>() {
            @Override
            public {{func.resp_obj}} call() throws Exception {
             try(Connection con = ds.getConnection()) {
                 {% if func.has_resp %} return {% end %} {{func.name}} (con {% for idx, (t, name) in enumerate(func.args) %},{{name}} {% end %});
             }
            }
        });
    }
    {% else %}
    public static Future<?> {{func.name}} (final DataSource ds {% for idx, (t, name) in enumerate(func.args) %}, final {{t}} {{name}} {% end %},ExecutorService pool) {
        return pool.submit(new Runnable() {
            @Override
            public void run() {
             try(Connection con = ds.getConnection()) {
                 {{func.name}} (con {% for idx, (t, name) in enumerate(func.args) %},{{name}} {% end %});
             } catch (SQLException e) {
                 logger.error("{{func.name}}", e);
             }
            }
        });
    }
    {% end %}

      public static {{func.resp}} {{func.name}} (DataSource ds {% for idx, (t, name) in enumerate(func.args) %}, {{t}} {{name}} {% end %})
         throws SQLException {
         try(Connection con = ds.getConnection()) {
             {% if func.has_resp %} return {% end %} {{func.name}} (con {% for idx, (t, name) in enumerate(func.args) %},{{name}} {% end %});
         }
      }
    {% end %}

    private static String join(List ids) {
        if (ids.size() > 0) {
            StringBuilder sb = new StringBuilder(ids.size() * 10);

            Object o = ids.get(0);
            if (o instanceof Number) {
                for (Number id : (List<Number>) ids) {
                    sb.append(id).append(",");
                }
            } else {
                for (String id : (List<String>) ids) {
                    sb.append('"').append(id).append("\",");
                }
            }
            sb.setLength(sb.length() - 1);
            return sb.toString();
        }
        return "";
    }

    public DBApi(DataSource ds) {
        this.ds = ds;
    }

    private final DataSource ds;
}
